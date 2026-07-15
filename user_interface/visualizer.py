"""
Módulo gestor do motor gráfico PyVista. Aplica cores, fatia a malha e traça setas.
"""
import numpy as np


class VisualizerManager:
    """
    Encapsula toda a lógica de plotagem gráfica para não poluir a janela principal.
    Decide que tipo de filtro aplicar (Surface ou Slice) com base no modo selecionado.
    """

    def __init__(self, visualizador):
        """
        :param visualizador: Instância de QtInteractor do PyVista onde se desenha.
        """
        self.visualizador = visualizador

    def atualizar_visualizacao(self, malha, resultado, modo, eixo_corte, origem_corte,
                               mostrar_malha, mostrar_contornos, mostrar_setas,
                               repor_vista=False, mensagem_callback=None):
        """
        Limpa a tela e desenha de novo a malha baseada no estado atual das checkboxes e sliders.

        :param malha: Estrutura vtkUnstructuredGrid gerada pelo PyVista.
        :param resultado: Dataclass ResultadoMEF com os potenciais numéricos.
        :param modo: 'superficie' (Vista 3D) ou 'corte' (Fatia plana).
        :param eixo_corte: Eixo geométrico em uso ('x', 'y' ou 'z').
        :param origem_corte: Tuplo (x,y,z) designando o centro do plano de corte.
        :param mostrar_malha: Boolean - Traçar as linhas pretas dos tetraedros?
        :param mostrar_contornos: Boolean - Traçar linhas isopotenciais (Curvas de Nível)?
        :param mostrar_setas: Boolean - Traçar o fluxo de Campo Elétrico?
        :param repor_vista: Boolean - Reenquadrar as câmaras no final do desenho?
        :param mensagem_callback: Função para atualizar o texto do topo da interface.
        """
        if malha is None or resultado is None:
            return

        # Guarda as posições da câmara para não dar um 'salto' quando a malha faz update
        posicao_camara = None
        projecao_paralela = False
        if not repor_vista:
            try:
                posicao_camara = self.visualizador.camera_position
                projecao_paralela = bool(self.visualizador.camera.GetParallelProjection())
            except Exception:
                pass

        # Limpar o canvas
        self.visualizador.clear()

        minimo = float(np.min(resultado.potenciais))
        maximo = float(np.max(resultado.potenciais))

        # Argumentos comuns que vão ser partilhados quer pelo corte quer pela 3D
        comuns = dict(
            scalars="Potencial (V)", cmap="turbo", clim=(minimo, maximo),
            show_edges=mostrar_malha,
            scalar_bar_args={"title": "Potencial (V)", "color": "white",
                             "vertical": False, "position_x": 0.35, "position_y": 0.03}
        )

        if modo == "superficie":
            # Plot da casca exterior
            self.visualizador.add_mesh(malha, **comuns)
            if mensagem_callback:
                mensagem_callback("Vista 3D: a superficie exterior mostra o potencial na fronteira da malha.")
        else:
            # Corte Interno
            normal = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[eixo_corte]
            fatia = malha.slice(normal=normal, origin=origem_corte)

            # Adiciona o wireframe fantasma da caixa total
            self.visualizador.add_mesh(malha.outline(), color="#9fb0c9", line_width=1.2)

            if fatia.n_points:
                self.visualizador.add_mesh(fatia, opacity=0.92, **comuns)

                # Curvas Isopotenciais (Brancas)
                if mostrar_contornos:
                    curvas = fatia.contour(scalars="Potencial (V)", isosurfaces=18)
                    self.visualizador.add_mesh(curvas, color="white", line_width=1.5)

                # Setas Vectoriais do Campo Elétrico (Escuras)
                if mostrar_setas and "Campo eletrico (V/m)" in fatia.cell_data:
                    escala = malha.length * 0.025
                    setas = fatia.cell_centers().glyph(orient="Campo eletrico (V/m)", scale=False, factor=escala)
                    self.visualizador.add_mesh(setas, color="#111827")

            if mensagem_callback:
                mensagem_callback(f"Corte {eixo_corte.upper()}: use A/D, setas, botoes laterais ou a posicao exata.")

        # Eletrodos (Bateria e Terra)
        self._adicionar_eletrodos(resultado)
        self.visualizador.add_axes(color="#cbd5e1")

        # Repor ou restaurar a Câmara visual
        if repor_vista:
            self.repor_camara(modo, eixo_corte, mostrar_mensagem=False)
        elif posicao_camara is not None:
            self.visualizador.camera_position = posicao_camara
            if projecao_paralela:
                self.visualizador.enable_parallel_projection()
            else:
                self.visualizador.disable_parallel_projection()

        self.visualizador.render()

    def _adicionar_eletrodos(self, resultado):
        """
        Adiciona esferas de marcação nos nós que contêm voltagens fixas (bateria).

        :param resultado: Instância de ResultadoMEF.
        """
        vmax = max(resultado.condicoes.values())
        vmin = min(resultado.condicoes.values())

        positivos = [no for no, valor in resultado.condicoes.items() if valor == vmax]
        negativos = [no for no, valor in resultado.condicoes.items() if valor == vmin]

        # Bateria (+) a Vermelho
        self.visualizador.add_points(resultado.nos[positivos], color="#ff5c5c", point_size=10,
                                     render_points_as_spheres=True, label="Eletrodo (+)")
        # Referência (-) a Azul
        self.visualizador.add_points(resultado.nos[negativos], color="#5f8dff", point_size=6,
                                     render_points_as_spheres=True, label="Referencia (0 V)")

    def repor_camara(self, modo, eixo_corte, mostrar_mensagem=True, mensagem_callback=None):
        """
        Reposiciona a câmara perfeitamente plana num eixo ortogonal de corte
        ou num aspeto isométrico livre para superfícies.

        :param modo: 'superficie' ou 'corte'.
        :param eixo_corte: 'x', 'y', 'z'.
        """
        if modo == "corte":
            if eixo_corte == "x":
                self.visualizador.view_yz()
            elif eixo_corte == "y":
                self.visualizador.view_xz()
            else:
                self.visualizador.view_xy()
            self.visualizador.enable_parallel_projection()  # Desliga a perspetiva visual
        else:
            self.visualizador.view_isometric()
            self.visualizador.disable_parallel_projection()

        self.visualizador.reset_camera()
        self.visualizador.render()

        if mostrar_mensagem and mensagem_callback:
            mensagem_callback("Camara reposta.")