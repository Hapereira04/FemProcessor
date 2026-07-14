"""
main_window.py
==============
Define a janela principal da aplicação TerraMEF.
"""

from __future__ import annotations

import os
import sys
import traceback
from typing import Optional

import numpy as np
import scipy.sparse as sparse
from scipy.io import mmwrite

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QDoubleSpinBox, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton,
    QSlider, QVBoxLayout, QWidget, QScrollArea,
)
from pyvistaqt import QtInteractor

# Importações internas do módulo user_interface
from .result_dataclass import ResultadoMEF
from .utils import formatar
from .styles import STYLESHEET
from .sidebar import Sidebar
from .viewer import Viewer3D


# Importações dos módulos de cálculo (serão usados mais tarde)
# import fem_solver
# import io_utils
# import visualization


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
        self.trabalhador: Optional[QObject] = None  # será TrabalhadorCalculo

        # Atalhos de teclado
        self.atalhos: list[QShortcut] = []

        # Aplicar estilo (a folha está em styles.py)
        self.setStyleSheet(STYLESHEET)

        self.setStyleSheet(STYLESHEET)
        self._criar_interface()
        self._criar_atalhos()
        self._criar_barra_exportacao()

    def _criar_interface(self) -> None:
        """
        Constrói a interface completa: painel lateral + área de visualização 3D.
        """
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

        # Define a largura fixa do painel
        sidebar_frame = QFrame(objectName="sidebar")
        sidebar_frame.setFixedWidth(330)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)

        layout_principal.addWidget(sidebar_frame)

        # ---- Área de visualização ----
        self.viewer = Viewer3D()
        self.viewer.repor_camara_clicked.connect(self._repor_camara)
        layout_principal.addWidget(self.viewer, 1)  # Expande para ocupar o resto

        def _repor_camara(self) -> None:
            """Metodo interno para repor a câmara (chamado pelo sinal do viewer)."""
            self.repor_camara(mostrar_mensagem=True)

        def repor_camara(self, mostrar_mensagem: bool = True) -> None:
            """Repõe a câmara para a posição padrão do modo actual."""
            self.viewer.repor_camara(self.modo, self.eixo_corte)
            if mostrar_mensagem:
                self.mostrar_mensagem("Câmara reposta.")

        def mostrar_mensagem(self, texto: str) -> None:
            """Actualiza a mensagem no viewer e na barra de estado (quando existir)."""
            # Por enquanto, apenas no viewer
            self.viewer.mostrar_mensagem(texto)
            print(f"[MENSAGEM] {texto}")

        placeholder = QLabel("Área 3D (será implementada no próximo commit)")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #9fb0c9; font-size: 16px;")
        layout_principal.addWidget(placeholder, 1)

        # Conecta o sinal da sidebar ao metodo de cálculo (será implementado depois)
        self.sidebar.calcular_clicked.connect(self.calcular)

    # Metodo calcular (esqueleto para já)
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
        """
        Mostra uma mensagem na barra de estado (será melhorada depois).
        """
        # Como ainda não temos a barra de estado, usamos print para teste
        print(f"[MENSAGEM] {texto}")
        # Futuramente, actualizará a QLabel de estado

def iniciar_interface(self) -> int:
    """
    Função principal que inicia a aplicação Qt e mostra a janela.

    :return: Código de saída do loop de eventos.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("TerraMEF")
    janela = JanelaMEF()
    janela.show()
    return app.exec()
