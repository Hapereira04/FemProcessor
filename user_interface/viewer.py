"""
viewer.py
=========
Define a área de visualização 3D baseada em pyvistaqt.
"""

from __future__ import annotations

from typing import Optional, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from pyvistaqt import QtInteractor
import pyvista as pv


class Viewer3D(QWidget):
    """
    Widget que encapsula o visualizador 3D (pyvista) com cabeçalho.

    :param parent: Widget pai (normalmente a janela principal).
    """

    # Sinal emitido quando o utilizador pede para repor a câmara
    repor_camara_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Estado da visualização
        self.modo: str = "superficie"      # "superficie" ou "corte"
        self.eixo_corte: str = "y"

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Constrói a interface: cabeçalho + visualizador."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Cabeçalho ----
        cabecalho = QFrame(objectName="cabecalho")
        cabecalho_layout = QHBoxLayout(cabecalho)
        cabecalho_layout.setContentsMargins(22, 12, 18, 12)

        self.titulo_vista = QLabel("Vista 3D do potencial", objectName="titulo_vista")
        cabecalho_layout.addWidget(self.titulo_vista)

        self.mensagem_topo = QLabel("Pronto para calcular", objectName="mensagem_topo")
        cabecalho_layout.addWidget(self.mensagem_topo, 1)

        # Botão Repor câmara
        botao_repor = QPushButton("Repor câmara")
        botao_repor.clicked.connect(self.repor_camara_clicked.emit)
        cabecalho_layout.addWidget(botao_repor)

        layout.addWidget(cabecalho)

        # ---- Visualizador 3D (pyvista) ----
        self.plotter = QtInteractor(self)
        self.plotter.interactor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Configuração inicial
        self.plotter.set_background("#101827", top="#172238")
        self.plotter.add_text(
            "Carregue uma malha e calcule para iniciar.",
            position="upper_left",
            font_size=13,
            color="#cbd5e1"
        )
        self.plotter.add_axes(color="#cbd5e1")

        layout.addWidget(self.plotter.interactor, 1)

    # ------------------------------------------------------------
    # Métodos públicos para controlar a visualização
    # ------------------------------------------------------------

    def definir_modo(self, modo: str, eixo: Optional[str] = None) -> None:
        """
        Define o modo de visualização (superfície ou corte).

        :param modo: "superficie" ou "corte".
        :param eixo: Eixo do corte ("x", "y", "z") – só usado no modo corte.
        """
        self.modo = modo
        if eixo is not None:
            self.eixo_corte = eixo
        self.titulo_vista.setText("Corte interativo" if modo == "corte" else "Vista 3D do potencial")

    def mostrar_mensagem(self, texto: str) -> None:
        """Actualiza a mensagem no topo da área de visualização."""
        self.mensagem_topo.setText(texto)

    def adicionar_malha(self, malha: pv.UnstructuredGrid, **kwargs) -> None:
        """
        Adiciona uma malha ao visualizador.

        :param malha: Malha pyvista (UnstructuredGrid) com dados de potencial.
        :param kwargs: Argumentos adicionais para `add_mesh` (ex: scalars, cmap).
        """
        self.plotter.add_mesh(malha, **kwargs)

    def adicionar_pontos(self, pontos: Any, **kwargs) -> None:
        """Adiciona pontos ao visualizador (ex: eléctrodos)."""
        self.plotter.add_points(pontos, **kwargs)

    def adicionar_outline(self, malha: pv.UnstructuredGrid, **kwargs) -> None:
        """Adiciona o contorno da malha."""
        self.plotter.add_mesh(malha.outline(), **kwargs)

    def adicionar_fatia(self, fatia: pv.PolyData, **kwargs) -> None:
        """Adiciona uma fatia (corte) ao visualizador."""
        self.plotter.add_mesh(fatia, **kwargs)

    def adicionar_contornos(self, fatia: pv.PolyData, n_curvas: int = 18, **kwargs) -> None:
        """Adiciona curvas de contorno a uma fatia."""
        curvas = fatia.contour(scalars="Potencial (V)", isosurfaces=n_curvas)
        self.plotter.add_mesh(curvas, **kwargs)

    def adicionar_setas(self, fatia: pv.PolyData, escala: float, **kwargs) -> None:
        """Adiciona setas do campo eléctrico a uma fatia."""
        setas = fatia.cell_centers().glyph(
            orient="Campo eletrico (V/m)",
            scale=False,
            factor=escala
        )
        self.plotter.add_mesh(setas, **kwargs)

    def adicionar_axes(self) -> None:
        """Adiciona eixos de coordenadas (garantindo que estão sempre visíveis)."""
        self.plotter.add_axes(color="#cbd5e1")

    def adicionar_texto(self, texto: str, **kwargs) -> None:
        """Adiciona texto à cena (ex: instruções)."""
        self.plotter.add_text(texto, **kwargs)

    def limpar(self) -> None:
        """Remove todos os actores da cena."""
        self.plotter.clear()

    def renderizar(self) -> None:
        """Força a renderização da cena."""
        self.plotter.render()

    def repor_camara(self, modo: str, eixo: Optional[str] = None) -> None:
        """
        Repõe a câmara para a posição padrão do modo actual.

        :param modo: "superficie" ou "corte".
        :param eixo: Eixo do corte ("x", "y", "z") – só usado no modo corte.
        """
        if modo == "corte":
            if eixo == "x":
                self.plotter.view_yz()
            elif eixo == "y":
                self.plotter.view_xz()
            else:  # z
                self.plotter.view_xy()
            self.plotter.enable_parallel_projection()
        else:
            self.plotter.view_isometric()
            self.plotter.disable_parallel_projection()
        self.plotter.reset_camera()
        self.renderizar()

    def guardar_imagem(self, caminho: str) -> None:
        """Guarda a cena actual como imagem PNG."""
        self.plotter.screenshot(caminho, transparent_background=False)

    def obter_posicao_camara(self) -> tuple:
        """Devolve a posição actual da câmara (para restauro)."""
        return self.plotter.camera_position

    def definir_posicao_camara(self, posicao: tuple) -> None:
        """Restaura a posição da câmara."""
        self.plotter.camera_position = posicao

    def obter_projecao_paralela(self) -> bool:
        """Devolve True se a projecção paralela estiver activa."""
        return bool(self.plotter.camera.GetParallelProjection())

    def definir_projecao_paralela(self, activa: bool) -> None:
        """Activa ou desactiva a projecção paralela."""
        if activa:
            self.plotter.enable_parallel_projection()
        else:
            self.plotter.disable_parallel_projection()