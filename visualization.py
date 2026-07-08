"""
visualization.py
================
Módulo dedicado à renderização 3D e pós-processamento visual dos resultados MEF.

Este módulo utiliza a biblioteca PyVista para transformar os dados numéricos
(nós, elementos e potenciais) em representações gráficas interativas,
permitindo a análise de cortes transversais e a visualização do campo elétrico.
"""
import pyvista as pv
import numpy as np


def preparar_malha_vtk(nos, elementos):
    """
    Converte a malha do Python (nós e elementos) para o formato UnstructuredGrid do VTK.

    :param nos: Array NumPy (N x 3) com as coordenadas (x, y, z) dos nós.
    :param elementos: Array NumPy (M x 4) com os índices dos 4 nós de cada tetraedro.
    :return: Objeto pv.UnstructuredGrid formatado para renderização 3D.
    """
    M = len(elementos)
    # PyVista exige que os arrays comecem com o número de nós da célula
    celulas_vtk = np.empty((M, 5), dtype=int)
    celulas_vtk[:, 0] = 4
    celulas_vtk[:, 1:] = elementos
    celulas_vtk = celulas_vtk.flatten()

    # O código VTK para 'Linear Tetrahedron' é 10
    tipos_celulas = np.full(M, 10, dtype=np.uint8)

    return pv.UnstructuredGrid(celulas_vtk, tipos_celulas, nos)


def visualizar_resultados_3d(nos, elementos, potenciais):
    """
    Gera uma janela 3D interativa com um mapa de cores (heatmap) dos potenciais.

    :param nos: Array NumPy (N x 3) com as coordenadas dos nós.
    :param elementos: Array NumPy (M x 4) com a conectividade dos tetraedros.
    :param potenciais: Array NumPy (N) com os valores de voltagem em cada nó.
    """
    malha = preparar_malha_vtk(nos, elementos)
    malha.point_data["Potencial (V)"] = potenciais

    plotter = pv.Plotter(title="Visualização MEF 3D")
    plotter.add_mesh(malha, show_edges=True, scalars="Potencial (V)", cmap="jet", lighting=True)
    plotter.add_axes()
    plotter.add_bounding_box(color='gray')

    plotter.show()


def visualizar_corte_interativo(nos, elementos, potenciais, gradientes, condicoes):
    """
    Gera uma interface gráfica avançada com um plano de corte dinâmico,
    visualização de gradientes (vetores corrente) e controlo de câmara.

    :param nos: Array NumPy (N x 3) com as coordenadas dos nós.
    :param elementos: Array NumPy (M x 4) com a conectividade dos tetraedros.
    :param potenciais: Array NumPy (N) com os valores de voltagem em cada nó.
    :param gradientes: Array NumPy (M x 3) com o vetor Campo Elétrico calculado por elemento.
    :param condicoes: Dicionário com as condições de fronteira (índice do nó : voltagem).
    """
    import pyvista as pv
    import numpy as np

    # Descobre os limites globais absolutos da tua simulação
    pot_min = np.min(potenciais)
    pot_max = np.max(potenciais)

    malha = preparar_malha_vtk(nos, elementos)
    malha.point_data["Potencial (V)"] = potenciais
    malha.cell_data["Gradiente"] = gradientes

    plotter = pv.Plotter(title="Pós-Processador MEF - Corte Interativo")
    plotter.add_mesh(malha.outline(), color="black")

    # 1. IDENTIFICAÇÃO DAS PLACAS
    if condicoes:
        v_max = max(condicoes.values())
        v_min = min(condicoes.values())
        nos_max = [no for no, v in condicoes.items() if v == v_max]
        nos_min = [no for no, v in condicoes.items() if v == v_min]

        ator_pos = plotter.add_points(nos[nos_max], color="red", point_size=15, render_points_as_spheres=True,
                                      name="Placa Positiva")
        ator_neg = plotter.add_points(nos[nos_min], color="blue", point_size=15, render_points_as_spheres=True,
                                      name="Placa Negativa")

    # Memória de estado para os botões + e - saberem onde está o plano
    estado_plano = {'normal': [0.0, 1.0, 0.0], 'origem': np.array(malha.center)}
    # O tamanho do passo será 2% do tamanho total da malha
    passo = malha.length * 0.02

    # 2. LÓGICA DO CORTE
    def atualizar_corte(normal, origem):
        # Guarda a posição atual sempre que o plano se mexe (mesmo com o rato)
        estado_plano['normal'] = normal
        estado_plano['origem'] = np.array(origem)

        fatia = malha.slice(normal=normal, origin=origem)
        if fatia.n_points == 0:
            return

        curvas = fatia.contour(scalars="Potencial (V)", isosurfaces=15)
        setas = fatia.cell_centers().glyph(orient="Gradiente", scale=False, factor=0.08)

        # O clim tranca as cores: pot_max será sempre vermelho forte, pot_min será sempre azul forte
        plotter.add_mesh(fatia, scalars="Potencial (V)", cmap="jet", opacity=0.8, name='fatia', show_scalar_bar=True,
                         clim=[pot_min, pot_max])
        plotter.add_mesh(curvas, color="white", line_width=estado_visual['espessura_linha'], name='curvas')
        plotter.add_mesh(setas, color="black", name='setas')

    # 3. FORÇAR A MUDANÇA DE PLANOS (Correção do tamanho: bounds=malha.bounds)
    def set_plano_x():
        plotter.clear_plane_widgets()
        plotter.add_plane_widget(atualizar_corte, normal='x', origin=malha.center, bounds=malha.bounds)

    def set_plano_y():
        plotter.clear_plane_widgets()
        plotter.add_plane_widget(atualizar_corte, normal='y', origin=malha.center, bounds=malha.bounds)

    def set_plano_z():
        plotter.clear_plane_widgets()
        plotter.add_plane_widget(atualizar_corte, normal='z', origin=malha.center, bounds=malha.bounds)

    # 4. ANDAR COM O PLANO PARA A FRENTE E PARA TRÁS (w e s) - 100% MATEMÁTICO
    percentagem_passo = 0.01

    def calcular_passo_dinamico():
        bounds = malha.bounds
        dx = bounds[1] - bounds[0]
        dy = bounds[3] - bounds[2]
        dz = bounds[5] - bounds[4]

        nx, ny, nz = estado_plano['normal']
        tamanho_direcao = abs(nx) * dx + abs(ny) * dy + abs(nz) * dz

        return tamanho_direcao * percentagem_passo

    def mover_frente():
        passo_atual = calcular_passo_dinamico()
        nova_origem = estado_plano['origem'] + np.array(estado_plano['normal']) * passo_atual

        teste_fatia = malha.slice(normal=estado_plano['normal'], origin=nova_origem)

        if teste_fatia.n_points > 0:
            plotter.clear_plane_widgets()
            # Trancado aos limites da malha
            plotter.add_plane_widget(atualizar_corte, normal=estado_plano['normal'], origin=nova_origem,
                                     bounds=malha.bounds)

    def mover_tras():
        passo_atual = calcular_passo_dinamico()
        nova_origem = estado_plano['origem'] - np.array(estado_plano['normal']) * passo_atual

        teste_fatia = malha.slice(normal=estado_plano['normal'], origin=nova_origem)

        if teste_fatia.n_points > 0:
            plotter.clear_plane_widgets()
            # Trancado aos limites da malha
            plotter.add_plane_widget(atualizar_corte, normal=estado_plano['normal'], origin=nova_origem,
                                     bounds=malha.bounds)

    # 5. FUNÇÃO DE RESET E CAMARA
    def resetar_tudo():
        for actor_name in ['fatia', 'curvas', 'setas']:
            if actor_name in plotter.actors:
                plotter.remove_actor(actor_name)
        plotter.clear_plane_widgets()
        plotter.add_plane_widget(atualizar_corte, normal='y', origin=malha.center)
        set_view_3d()

    def set_view_xy():
        plotter.view_xy(); plotter.enable_parallel_projection()

    def set_view_xz():
        plotter.view_xz(); plotter.enable_parallel_projection()

    # Substituímos a função que causava o erro CrystalEyes no Windows
    def set_view_3d():
        plotter.disable_parallel_projection()
        plotter.camera_position = 'iso'  # Posição isométrica sem bugs!
        plotter.reset_camera()

    # 6. RODAR COM AS SETAS DO TECLADO
    def rodar_esquerda():
        plotter.camera.azimuth += 5

    def rodar_direita():
        plotter.camera.azimuth -= 5

    def rodar_cima():
        plotter.camera.elevation += 5

    def rodar_baixo():
        plotter.camera.elevation -= 5

    # Função para tirar Screenshot
    def tirar_print():
        # Guarda a imagem com fundo branco e alta resolução
        plotter.screenshot("Relatorio_Corte_MEF.png", transparent_background=False)
        print(">>> FOTOGRAFIA GUARDADA: Relatorio_Corte_MEF.png <<<")

    # Memória visual partilhada (bolas e linhas)
    estado_visual = {'tamanho_pontos': 15, 'espessura_linha': 2.0}

    def aumentar_tamanho():
        # Limita os pontos (Máximo: 30)
        if estado_visual['tamanho_pontos'] < 30:
            estado_visual['tamanho_pontos'] += 2

        # Limita as linhas (Máximo: 8)
        if estado_visual['espessura_linha'] < 8.0:
            estado_visual['espessura_linha'] += 1.0

        # Aplica aos pontos
        ator_pos.prop.point_size = estado_visual['tamanho_pontos']
        ator_neg.prop.point_size = estado_visual['tamanho_pontos']

        # Aplica às linhas (só se elas estiverem visíveis no momento)
        if 'curvas' in plotter.actors:
            plotter.actors['curvas'].prop.line_width = estado_visual['espessura_linha']

        plotter.render()

    def diminuir_tamanho():
        # Limita os pontos (Mínimo: 5)
        if estado_visual['tamanho_pontos'] > 5:
            estado_visual['tamanho_pontos'] -= 2

        # Limita as linhas (Mínimo: 1)
        if estado_visual['espessura_linha'] > 1.0:
            estado_visual['espessura_linha'] -= 1.0

        # Aplica aos pontos
        ator_pos.prop.point_size = estado_visual['tamanho_pontos']
        ator_neg.prop.point_size = estado_visual['tamanho_pontos']

        # Aplica às linhas
        if 'curvas' in plotter.actors:
            plotter.actors['curvas'].prop.line_width = estado_visual['espessura_linha']

        plotter.render()

    # Liga aos botões
    plotter.add_key_event('plus', aumentar_tamanho)
    plotter.add_key_event('KP_Add', aumentar_tamanho)
    plotter.add_key_event('minus', diminuir_tamanho)
    plotter.add_key_event('KP_Subtract', diminuir_tamanho)

    # --- ATRIBUIÇÃO DE TODAS AS TECLAS ---
    plotter.add_key_event('x', set_plano_x)
    plotter.add_key_event('y', set_plano_y)
    plotter.add_key_event('z', set_plano_z)
    plotter.add_key_event('r', resetar_tudo)
    plotter.add_key_event('1', set_view_xy)
    plotter.add_key_event('2', set_view_xz)
    plotter.add_key_event('3', set_view_3d)
    plotter.add_key_event('p', tirar_print)

    # Atalhos aumentar e diminuir tamanho
    plotter.add_key_event('plus', aumentar_tamanho)
    plotter.add_key_event('KP_Add', aumentar_tamanho)
    plotter.add_key_event('minus', diminuir_tamanho)
    plotter.add_key_event('KP_Subtract', diminuir_tamanho)

    # Teclas novas de deslocamento e rotação
    plotter.add_key_event('n', mover_frente)
    plotter.add_key_event('m', mover_tras)
    plotter.add_key_event('Up', rodar_cima)
    plotter.add_key_event('Down', rodar_baixo)
    plotter.add_key_event('Left', rodar_esquerda)
    plotter.add_key_event('Right', rodar_direita)

    # Inicializar o plano pela primeira vez
    plotter.add_plane_widget(atualizar_corte, normal='y', origin=malha.center)

    # HUD (Texto de instruções no ecrã atualizado)
    instrucoes = (
        "--- CONTROLOS ---\n"
        "[x/y/z] Mudar orientacao do corte\n"
        "[n/m]   Mover plano (frente/tras)\n"
        "[Setas] Rodar a camara em 3D\n"
        "[1/2]   Vistas 2D (Topo/Frente)\n"
        "[3]     Vista 3D Isometrica\n"
        "[r]     Resetar corte e camara\n"
        "[p]     Tirar Fotografia (Screenshot)\n\n"
        "Placas: Vermelho (+) / Azul (-)"
    )
    plotter.add_text(instrucoes, position="upper_left", font_size=10, color="black", font="courier")

    plotter.add_axes()
    plotter.show()