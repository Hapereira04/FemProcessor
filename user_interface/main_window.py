"""
main_window.py
==============
Define a janela principal da aplicação TerraMEF.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from PySide6.QtCore import QThread, Qt, QObject
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QScrollArea, QLabel, QMessageBox, QMenu
)
from pyvistaqt import QtInteractor

from .result_dataclass import ResultadoMEF
from .sidebar import Sidebar
from .styles import STYLESHEET


class JanelaMEF(QMainWindow):
    """
    Janela principal do simulador TerraMEF.
    Gerencia a interface, o cálculo, a visualização 3D e a exportação.
    """

    def __init__(self) -> None:
        """Inicializa a janela, define título, tamanho e variáveis de estado."""
        super().__init__()
        self.setWindowTitle("TerraMEF | Simulador de aterramento")
        self.resize(1420, 860)

        # Estado da simulação
        self.resultado: Optional[ResultadoMEF] = None
        self.malha = None  # pyvista.UnstructuredGrid

        # Modos de visualização
        self.modo: str = "superficie"
        self.eixo_corte: str = "y"

        # Thread de cálculo
        self.thread: Optional[QThread] = None
        self.trabalhador: Optional[QObject] = None

        # Atalhos de teclado
        self.atalhos: list[QShortcut] = []

        # Aplicar estilo
        self.setStyleSheet(STYLESHEET)

        # Construir interface
        self._criar_interface()

        # Atalhos e barra de menu (serão implementados depois)
        self._criar_atalhos()
        self._criar_barra_exportacao()

    def _criar_interface(self) -> None:
        """Constrói a interface: painel lateral + área de visualização 3D."""
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QHBoxLayout(central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ---- Painel lateral (com scroll) ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.sidebar = Sidebar()
        scroll.setWidget(self.sidebar)

        # Contentor do painel lateral com largura fixa
        sidebar_frame = QFrame(objectName="sidebar")
        sidebar_frame.setFixedWidth(330)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)

        layout_principal.addWidget(sidebar_frame)

        # ---- Área de visualização 3D (placeholder até ao commit 4) ----
        self.viewer = QLabel("Área de visualização 3D (será implementada no próximo commit)")
        self.viewer.setAlignment(Qt.AlignCenter)
        self.viewer.setStyleSheet("color: #9fb0c9; font-size: 16px; background: #101827;")
        layout_principal.addWidget(self.viewer, 1)

        # Conecta o sinal da sidebar ao metodo de cálculo
        self.sidebar.calcular_clicked.connect(self.calcular)

    def _criar_atalhos(self) -> None:
        """Cria os atalhos de teclado (serão implementados depois)."""
        # Placeholder: ainda não há atalhos
        pass

    def _criar_barra_exportacao(self) -> None:
        """Cria a barra de menu Exportar (será implementada depois)."""
        # Placeholder
        pass

    def calcular(self) -> None:
        """Inicia o cálculo da simulação (será implementado num commit futuro)."""
        pontos, elementos = self.sidebar.obter_caminhos()
        if not os.path.isfile(pontos) or not os.path.isfile(elementos):
            QMessageBox.warning(
                self,
                "Ficheiros em falta",
                "Selecione ficheiros válidos para os nós e os elementos."
            )
            return
        # Por enquanto, apenas uma mensagem
        self.mostrar_mensagem("A calcular... (funcionalidade em breve)")

    def mostrar_mensagem(self, texto: str) -> None:
        """Mostra uma mensagem na barra de estado (será melhorada depois)."""
        # Por enquanto, usa print. Futuramente, actualizará a QLabel de estado.
        print(f"[MENSAGEM] {texto}")

    def repor_camara(self, mostrar_mensagem: bool = True) -> None:
        """Repõe a câmara para a posição padrão (será implementado depois)."""
        # Placeholder
        if mostrar_mensagem:
            self.mostrar_mensagem("Câmara reposta (funcionalidade em breve).")


# ------------------------------------------------------------
# Função para iniciar a aplicação
# ------------------------------------------------------------
def iniciar_interface() -> int:
    """
    Função principal que inicia a aplicação Qt e mostra a janela.

    :return: Código de saída do loop de eventos.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("TerraMEF")
    janela = JanelaMEF()
    janela.show()
    return app.exec()