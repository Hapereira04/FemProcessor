"""
visualization.py
================
Módulo dedicado à renderização 3D e pós-processamento visual dos resultados MEF.
"""
import pyvista as pv
import numpy as np

def preparar_malha_vtk(nos, elementos):
    M = len(elementos)
    celulas_vtk = np.empty((M, 5), dtype=int)
    celulas_vtk[:, 0] = 4
    celulas_vtk[:, 1:] = elementos
    celulas_vtk = celulas_vtk.flatten()
    tipos_celulas = np.full(M, 10, dtype=np.uint8)
    return pv.UnstructuredGrid(celulas_vtk, tipos_celulas, nos)

def visualizar_resultados_3d(nos, elementos, potenciais):
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
    """
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

        ator_pos = plotter.add_points(nos[nos_max], color="red", point_size=15, render_points_as_spheres=True, name="Placa Positiva")
        ator_neg = plotter.add_points(nos[nos_min], color="blue", point_size=15, render_points_as_spheres=True, name="Placa Negativa")

    estado_plano = {'normal': [0.0, 1.0, 0.0], 'origem': np.array(malha.center)}
    passo = malha.length * 0.02

    # 2. LÓGICA DO CORTE
    def atualizar_corte(normal, origem):
        estado_plano['normal'] = normal
        estado_plano['origem'] = np.array(origem)

        fatia = malha.slice(normal=normal, origin=origem)
        if fatia.n_points == 0:
            return

        curvas = fatia.contour(scalars="Potencial (V)", isosurfaces=15)
        setas = fatia.cell_centers().glyph(orient="Gradiente", scale=False, factor=0.08)

        plotter.add_mesh(fatia, scalars="Potencial (V)", cmap="jet", opacity=0.8, name='fatia', show_scalar_bar=True, clim=[pot_min, pot_max])
        plotter.add_mesh(curvas, color="white", line_width=estado_visual['espessura_linha'], name='curvas')
        plotter.add_mesh(setas, color="black", name='setas')

    # 3. FORÇAR A MUDANÇA DE PLANOS
    def set_plano_x(): plotter.clear_plane_widgets(); plotter.add_plane_widget(atualizar_corte, normal='x', origin=malha.center, bounds=malha.bounds)
    def set_plano_y(): plotter.clear_plane_widgets(); plotter.add_plane_widget(atualizar_corte, normal='y', origin=malha.center, bounds=malha.bounds)
    def set_plano_z(): plotter.clear_plane_widgets(); plotter.add_plane_widget(atualizar_corte, normal='z', origin=malha.center, bounds=malha.bounds)

    # 4. ANDAR COM O PLANO PARA A FRENTE E PARA TRÁS
    percentagem_passo = 0.01
    def calcular_passo_dinamico():
        bounds = malha.bounds
        dx, dy, dz = bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]
        nx, ny, nz = estado_plano['normal']
        return (abs(nx) * dx + abs(ny) * dy + abs(nz) * dz) * percentagem_passo

    def mover_frente():
        nova_origem = estado_plano['origem'] + np.array(estado_plano['normal']) * calcular_passo_dinamico()
        if malha.slice(normal=estado_plano['normal'], origin=nova_origem).n_points > 0:
            plotter.clear_plane_widgets()
            plotter.add_plane_widget(atualizar_corte, normal=estado_plano['normal'], origin=nova_origem, bounds=malha.bounds)

    def mover_tras():
        nova_origem = estado_plano['origem'] - np.array(estado_plano['normal']) * calcular_passo_dinamico()
        if malha.slice(normal=estado_plano['normal'], origin=nova_origem).n_points > 0:
            plotter.clear_plane_widgets()
            plotter.add_plane_widget(atualizar_corte, normal=estado_plano['normal'], origin=nova_origem, bounds=malha.bounds)

    # 5. FUNÇÃO DE RESET E CAMARA
    def resetar_tudo():
        for actor_name in ['fatia', 'curvas', 'setas']:
            if actor_name in plotter.actors: plotter.remove_actor(actor_name)
        plotter.clear_plane_widgets()
        plotter.add_plane_widget(atualizar_corte, normal='y', origin=malha.center)
        set_view_3d()

    def set_view_xy(): plotter.view_xy(); plotter.enable_parallel_projection()
    def set_view_xz(): plotter.view_xz(); plotter.enable_parallel_projection()
    def set_view_3d(): plotter.disable_parallel_projection(); plotter.camera_position = 'iso'; plotter.reset_camera()

    # 6. RODAR COM AS SETAS DO TECLADO
    def rodar_esquerda(): plotter.camera.azimuth += 5
    def rodar_direita(): plotter.camera.azimuth -= 5
    def rodar_cima(): plotter.camera.elevation += 5
    def rodar_baixo(): plotter.camera.elevation -= 5

    def tirar_print():
        plotter.screenshot("Relatorio_Corte_MEF.png", transparent_background=False)
        print(">>> FOTOGRAFIA GUARDADA: Relatorio_Corte_MEF.png <<<")

    estado_visual = {'tamanho_pontos': 15, 'espessura_linha': 2.0}

    def aumentar_tamanho():
        if estado_visual['tamanho_pontos'] < 30: estado_visual['tamanho_pontos'] += 2
        if estado_visual['espessura_linha'] < 8.0: estado_visual['espessura_linha'] += 1.0
        ator_pos.prop.point_size, ator_neg.prop.point_size = estado_visual['tamanho_pontos'], estado_visual['tamanho_pontos']
        if 'curvas' in plotter.actors: plotter.actors['curvas'].prop.line_width = estado_visual['espessura_linha']
        plotter.render()

    def diminuir_tamanho():
        if estado_visual['tamanho_pontos'] > 5: estado_visual['tamanho_pontos'] -= 2
        if estado_visual['espessura_linha'] > 1.0: estado_visual['espessura_linha'] -= 1.0
        ator_pos.prop.point_size, ator_neg.prop.point_size = estado_visual['tamanho_pontos'], estado_visual['tamanho_pontos']
        if 'curvas' in plotter.actors: plotter.actors['curvas'].prop.line_width = estado_visual['espessura_linha']
        plotter.render()

    # --- ATRIBUIÇÃO DE TODAS AS TECLAS ---
    teclas = {
        'x': set_plano_x, 'y': set_plano_y, 'z': set_plano_z, 'r': resetar_tudo,
        '1': set_view_xy, '2': set_view_xz, '3': set_view_3d, 'p': tirar_print,
        'plus': aumentar_tamanho, 'KP_Add': aumentar_tamanho, 'minus': diminuir_tamanho, 'KP_Subtract': diminuir_tamanho,
        'n': mover_frente, 'm': mover_tras, 'Up': rodar_cima, 'Down': rodar_baixo, 'Left': rodar_esquerda, 'Right': rodar_direita
    }
    for tecla, funcao in teclas.items():
        plotter.add_key_event(tecla, funcao)

    plotter.add_plane_widget(atualizar_corte, normal='y', origin=malha.center)

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