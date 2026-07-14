"""
visualizer.py
=============
Define a área de visualização 3D usando PyVista.

Esta classe encapsula o widget QtInteractor e oferece métodos para
adicionar malhas, cortes, eléctrodos e controlar a câmara.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog
from pyvistaqt import QtInteractor

# Importação do módulo de visualização do projecto (para preparar a malha VTK)
import visualization as vis_lib


class Visualizer3D(QWidget):
    """
    Widget que contém a área 3D de visualização.

    :param parent: Widget pai (normalmente a janela principal).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Estado interno
        self.malha = None          # pyvista.UnstructuredGrid
        self.resultado = None      # ResultadoMEF (para acesso aos dados)
        self.modo: str = "superficie"   # "superficie" ou "corte"
        self.eixo_corte: str = "y"      # "x", "y" ou "z"
        self.posicao_corte: float = 0.0  # posição actual do plano

        # Opções de visualização
        self.mostrar_contornos: bool = True
        self.mostrar_setas: bool = False
        self.mostrar_arestas: bool = True

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Constrói a interface do visualizador."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho
        cabecalho = QWidget(objectName="cabecalho")
        cabecalho_layout = QHBoxLayout(cabecalho)
        cabecalho_layout.setContentsMargins(22, 12, 18, 12)

        self.titulo_vista = QLabel("Vista 3D do potencial", objectName="titulo_vista")
        self.mensagem_topo = QLabel("Pronto para calcular", objectName="mensagem_topo")
        self.mensagem_topo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cabecalho_layout.addWidget(self.titulo_vista)
        cabecalho_layout.addWidget(self.mensagem_topo, 1)

        self.botao_repor = QPushButton("Repor câmara")
        self.botao_repor.clicked.connect(self.repor_camara)
        cabecalho_layout.addWidget(self.botao_repor)

        layout.addWidget(cabecalho)

        # Área 3D (QtInteractor)
        self.plotter = QtInteractor(self)
        self.plotter.interactor.setFocusPolicy(Qt.StrongFocus)
        self.plotter.set_background("#101827", top="#172238")
        self.plotter.add_text(
            "Carregue uma malha e calcule para iniciar.",
            position="upper_left",
            font_size=13,
            color="#cbd5e1"
        )
        self.plotter.add_axes(color="#cbd5e1")

        layout.addWidget(self.plotter.interactor)

    # ------------------------------------------------------------------
    # Métodos públicos para actualizar a visualização
    # ------------------------------------------------------------------

    def definir_dados(self, resultado, malha_vtk) -> None:
        """
        Define os dados a visualizar.

        :param resultado: Objecto ResultadoMEF.
        :param malha_vtk: Malha VTK (pyvista.UnstructuredGrid) com os dados.
        """
        self.resultado = resultado
        self.malha = malha_vtk

    def definir_modo(self, modo: str) -> None:
        """
        Define o modo de visualização: "superficie" ou "corte".
        """
        self.modo = modo
        self._atualizar_titulo()
        self.atualizar()

    def definir_eixo_corte(self, eixo: str) -> None:
        """
        Define o eixo de corte: "x", "y" ou "z".
        """
        self.eixo_corte = eixo
        self.atualizar()

    def definir_posicao_corte(self, posicao: float) -> None:
        """
        Define a posição do plano de corte.
        """
        self.posicao_corte = posicao
        self.atualizar()

    def definir_opcoes_visualizacao(self, contornos: bool, setas: bool, arestas: bool) -> None:
        """
        Define as opções de visualização.

        :param contornos: Mostrar curvas de potencial.
        :param setas: Mostrar setas do campo eléctrico.
        :param arestas: Mostrar arestas da malha.
        """
        self.mostrar_contornos = contornos
        self.mostrar_setas = setas
        self.mostrar_arestas = arestas
        self.atualizar()

    def atualizar(self, repor_vista: bool = False) -> None:
        """
        Actualiza a cena 3D com os dados actuais.

        :param repor_vista: Se True, repõe a câmara para a posição padrão.
        """
        if self.malha is None or self.resultado is None:
            return

        # Guardar posição da câmara (se não for para repor)
        posicao_camara = None
        projecao_paralela = False
        if not repor_vista:
            try:
                posicao_camara = self.plotter.camera_position
                projecao_paralela = bool(self.plotter.camera.GetParallelProjection())
            except Exception:
                pass

        # Limpar a cena
        self.plotter.clear()

        # Configurações comuns
        minimo = float(np.min(self.resultado.potenciais))
        maximo = float(np.max(self.resultado.potenciais))
        args_comuns = {
            "scalars": "Potencial (V)",
            "cmap": "turbo",
            "clim": (minimo, maximo),
            "show_edges": self.mostrar_arestas,
            "scalar_bar_args": {
                "title": "Potencial (V)",
                "color": "white",
                "vertical": False,
                "position_x": 0.35,
                "position_y": 0.03,
            },
        }

        # Renderização conforme o modo
        if self.modo == "superficie":
            self.plotter.add_mesh(self.malha, **args_comuns)
            self.mensagem_topo.setText("Vista 3D: a superfície exterior mostra o potencial na fronteira da malha.")
        else:  # corte
            normal = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[self.eixo_corte]
            origem = self._obter_origem_corte()
            fatia = self.malha.slice(normal=normal, origin=origem)

            # Outline da malha
            self.plotter.add_mesh(self.malha.outline(), color="#9fb0c9", line_width=1.2)

            if fatia.n_points:
                self.plotter.add_mesh(fatia, opacity=0.92, **args_comuns)

                # Curvas de contorno
                if self.mostrar_contornos:
                    curvas = fatia.contour(scalars="Potencial (V)", isosurfaces=18)
                    self.plotter.add_mesh(curvas, color="white", line_width=1.5)

                # Setas do campo eléctrico
                if self.mostrar_setas and "Campo eletrico (V/m)" in fatia.cell_data:
                    escala = self.malha.length * 0.025
                    setas = fatia.cell_centers().glyph(
                        orient="Campo eletrico (V/m)",
                        scale=False,
                        factor=escala
                    )
                    self.plotter.add_mesh(setas, color="#111827")

            self.mensagem_topo.setText(
                f"Corte {self.eixo_corte.upper()}: use os controlos laterais para mover o plano."
            )

        # Adicionar eléctrodos
        self._adicionar_eletrodos()

        # Eixos
        self.plotter.add_axes(color="#cbd5e1")

        # Restaurar ou repor câmara
        if repor_vista:
            self.repor_camara(mostrar_mensagem=False)
        elif posicao_camara is not None:
            self.plotter.camera_position = posicao_camara
            if projecao_paralela:
                self.plotter.enable_parallel_projection()
            else:
                self.plotter.disable_parallel_projection()

        self.plotter.render()

    def repor_camara(self, mostrar_mensagem: bool = True) -> None:
        """
        Repõe a câmara para a posição padrão conforme o modo.

        :param mostrar_mensagem: Se True, actualiza a mensagem de topo.
        """
        if self.modo == "corte":
            if self.eixo_corte == "x":
                self.plotter.view_yz()
            elif self.eixo_corte == "y":
                self.plotter.view_xz()
            else:
                self.plotter.view_xy()
            self.plotter.enable_parallel_projection()
        else:
            self.plotter.view_isometric()
            self.plotter.disable_parallel_projection()

        self.plotter.reset_camera()
        self.plotter.render()

        if mostrar_mensagem:
            self.mensagem_topo.setText("Câmara reposta.")

    def guardar_imagem(self) -> None:
        """
        Abre um diálogo para guardar a imagem actual em PNG.
        """
        if self.malha is None:
            return
        destino, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar imagem",
            "resultado_mef.png",
            "Imagem PNG (*.png)"
        )
        if destino:
            self.plotter.screenshot(destino, transparent_background=False)
            self.mensagem_topo.setText(f"Imagem guardada: {os.path.basename(destino)}")

    # ------------------------------------------------------------------
    # Métodos auxiliares
    # ------------------------------------------------------------------

    def _obter_origem_corte(self) -> Tuple[float, float, float]:
        """
        Calcula o ponto de origem do plano de corte (centro da malha,
        com a coordenada do eixo ajustada para self.posicao_corte).
        """
        if self.malha is None:
            return (0.0, 0.0, 0.0)
        centro = self.malha.center
        indices = {"x": 0, "y": 1, "z": 2}
        origem = list(centro)
        origem[indices[self.eixo_corte]] = self.posicao_corte
        return tuple(origem)

    def _adicionar_eletrodos(self) -> None:
        """Adiciona pontos para os eléctrodos (nós com potencial fixo)."""
        if self.resultado is None:
            return

        condicoes = self.resultado.condicoes
        if not condicoes:
            return

        vmax = max(condicoes.values())
        vmin = min(condicoes.values())
        positivos = [no for no, v in condicoes.items() if v == vmax]
        negativos = [no for no, v in condicoes.items() if v == vmin]

        if positivos:
            self.plotter.add_points(
                self.resultado.nos[positivos],
                color="#ff5c5c",
                point_size=10,
                render_points_as_spheres=True,
                label="Eletrodo (+)",
            )
        if negativos:
            self.plotter.add_points(
                self.resultado.nos[negativos],
                color="#5f8dff",
                point_size=6,
                render_points_as_spheres=True,
                label="Referência (0 V)",
            )

    def _atualizar_titulo(self) -> None:
        """Actualiza o título da vista conforme o modo."""
        if self.modo == "corte":
            self.titulo_vista.setText("Corte interativo")
        else:
            self.titulo_vista.setText("Vista 3D do potencial")