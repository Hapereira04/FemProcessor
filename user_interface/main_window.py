"""
main_window.py
==============
Define a janela principal da aplicação TerraMEF.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from PySide6.QtCore import QThread, Qt, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QFrame, QScrollArea, QMessageBox, QMenu, QFileDialog, QVBoxLayout
)

from .result_dataclass import ResultadoMEF
from .sidebar import Sidebar
from .styles import STYLESHEET
from .visualizer import Visualizer3D
from .worker import TrabalhadorCalculo


class JanelaMEF(QMainWindow):
    """
    Janela principal do simulador TerraMEF.
    Gerencia a interface, o cálculo, a visualização 3D e a exportação.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TerraMEF | Simulador de aterramento")
        self.resize(1420, 860)

        # Estado da simulação
        self.resultado: Optional[ResultadoMEF] = None
        self.malha = None

        # Thread de cálculo
        self.thread: Optional[QThread] = None
        self.trabalhador: Optional[TrabalhadorCalculo] = None

        # Atalhos
        self.atalhos: list[QShortcut] = []

        self.setStyleSheet(STYLESHEET)
        self._criar_interface()
        self._criar_atalhos()
        self._criar_barra_exportacao()

    def _criar_interface(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.sidebar = Sidebar()
        scroll.setWidget(self.sidebar)

        sidebar_frame = QFrame(objectName="sidebar")
        sidebar_frame.setFixedWidth(330)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)
        layout.addWidget(sidebar_frame)

        # Visualizador 3D
        self.visualizer = Visualizer3D()
        layout.addWidget(self.visualizer, 1)

        # Ligações
        self.sidebar.calcular_clicked.connect(self.calcular)
        self.sidebar.modo_alterado.connect(self._definir_modo)
        self.sidebar.eixo_alterado.connect(self._definir_eixo)
        self.sidebar.posicao_corte_alterada.connect(self._posicao_corte_alterada)
        self.sidebar.mostrar_contornos_alterado.connect(self._atualizar_visualizacao)
        self.sidebar.mostrar_setas_alterado.connect(self._atualizar_visualizacao)
        self.sidebar.mostrar_malha_alterado.connect(self._atualizar_visualizacao)
        self.visualizer.repor_camara_clicked.connect(self._repor_camara)

        self.visualizer.mostrar_mensagem("Carregue uma malha e calcule para iniciar.")

    # ---- Visualização ----
    @Slot(str)
    def _definir_modo(self, modo: str) -> None:
        self.visualizer.definir_modo(modo)
        self._atualizar_visualizacao(repor_vista=True)

    @Slot(str)
    def _definir_eixo(self, eixo: str) -> None:
        self.visualizer.definir_eixo_corte(eixo)
        if self.malha is not None:
            limites = self._obter_limites_corte(eixo)
            self.sidebar.definir_limites_corte(*limites)
        self._atualizar_visualizacao(repor_vista=True)

    @Slot(float)
    def _posicao_corte_alterada(self, posicao: float) -> None:
        self.visualizer.definir_posicao_corte(posicao)
        self._atualizar_visualizacao()

    def _atualizar_visualizacao(self, repor_vista: bool = False) -> None:
        if self.resultado is None or self.malha is None:
            return

        mostrar_contornos = self.sidebar.mostrar_contornos.isChecked()
        mostrar_setas = self.sidebar.mostrar_setas.isChecked()
        mostrar_arestas = self.sidebar.mostrar_malha.isChecked()

        self.visualizer.definir_opcoes_visualizacao(
            contornos=mostrar_contornos,
            setas=mostrar_setas,
            arestas=mostrar_arestas
        )

        if self.visualizer.malha is None:
            self.visualizer.definir_dados(self.resultado, self.malha)

        self.visualizer.atualizar(repor_vista=repor_vista)

    def _obter_limites_corte(self, eixo: str) -> tuple[float, float]:
        if self.malha is None:
            return (0.0, 1.0)
        bounds = self.malha.bounds
        indices = {"x": (0, 1), "y": (2, 3), "z": (4, 5)}
        i_min, i_max = indices[eixo]
        return (bounds[i_min], bounds[i_max])

    @Slot()
    def _repor_camara(self) -> None:
        self.visualizer.repor_camara(mostrar_mensagem=True)
        self.mostrar_mensagem("Câmara reposta.")

    # ---- Cálculo ----
    def calcular(self) -> None:
        pontos, elementos = self.sidebar.obter_caminhos()
        if not os.path.isfile(pontos) or not os.path.isfile(elementos):
            QMessageBox.warning(
                self,
                "Ficheiros em falta",
                "Selecione ficheiros válidos para os nós e os elementos."
            )
            return

        self.sidebar.definir_botao_calcular_habilitado(False)
        self.mostrar_mensagem("A preparar o cálculo...")

        self.thread = QThread(self)
        self.trabalhador = TrabalhadorCalculo(pontos, elementos)
        self.trabalhador.moveToThread(self.thread)

        self.thread.started.connect(self.trabalhador.executar)
        self.trabalhador.estado.connect(self.mostrar_mensagem)
        self.trabalhador.concluido.connect(self._calculo_concluido)
        self.trabalhador.falhou.connect(self._calculo_falhou)
        self.trabalhador.concluido.connect(self.thread.quit)
        self.trabalhador.falhou.connect(self.thread.quit)
        self.thread.finished.connect(self._limpar_thread)

        self.thread.start()

    @Slot(object)
    def _calculo_concluido(self, resultado: ResultadoMEF) -> None:
        self.resultado = resultado
        self.malha = self.visualizer.criar_malha_vtk(resultado.nos, resultado.elementos)
        self.malha.point_data["Potencial (V)"] = resultado.potenciais
        self.malha.cell_data["Campo elétrico (V/m)"] = resultado.gradientes

        limites = self._obter_limites_corte(self.visualizer.eixo_corte)
        self.sidebar.definir_limites_corte(*limites)

        # Atualizar indicadores
        delta_v = max(resultado.condicoes.values()) - min(resultado.condicoes.values())
        corrente = delta_v / resultado.resistencia if resultado.resistencia else None
        self.sidebar.atualizar_indicadores(
            resistencia=resultado.resistencia,
            corrente=corrente,
            num_nos=len(resultado.nos),
            num_elementos=len(resultado.elementos)
        )

        self.mostrar_mensagem("Cálculo concluído. Use os controlos para explorar os resultados.")
        self._atualizar_visualizacao(repor_vista=True)

    @Slot(str)
    def _calculo_falhou(self, erro: str) -> None:
        self.mostrar_mensagem("Erro no cálculo.")
        QMessageBox.critical(self, "Erro no cálculo", erro.splitlines()[-1])

    def _limpar_thread(self) -> None:
        self.sidebar.definir_botao_calcular_habilitado(True)
        if self.trabalhador is not None:
            self.trabalhador.deleteLater()
        if self.thread is not None:
            self.thread.deleteLater()
        self.trabalhador = None
        self.thread = None

    # ---- Mensagens ----
    def mostrar_mensagem(self, texto: str) -> None:
        self.visualizer.mostrar_mensagem(texto)

    # ---- Atalhos ----
    def _criar_atalhos(self) -> None:
        atalhos = {
            "A": lambda: self._mover_corte(-1),
            "D": lambda: self._mover_corte(1),
            "Shift+A": lambda: self._mover_corte(-10),
            "Shift+D": lambda: self._mover_corte(10),
            "Left": lambda: self._mover_corte(-1),
            "Right": lambda: self._mover_corte(1),
            "R": self._repor_camara,
            "P": self._guardar_imagem,
        }
        for tecla, funcao in atalhos.items():
            shortcut = QShortcut(QKeySequence(tecla), self)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(funcao)
            self.atalhos.append(shortcut)

    def _mover_corte(self, passos: int) -> None:
        if self.visualizer.modo != "corte" or self.malha is None:
            return
        valor = self.sidebar.slider_corte.value() + passos
        valor = max(0, min(1000, valor))
        self.sidebar.slider_corte.setValue(valor)

    def _guardar_imagem(self) -> None:
        if self.malha is None:
            return
        destino, _ = QFileDialog.getSaveFileName(
            self, "Guardar imagem", "resultado_mef.png", "PNG (*.png)"
        )
        if destino:
            self.visualizer.guardar_imagem(destino)
            self.mostrar_mensagem(f"Imagem guardada: {os.path.basename(destino)}")

    # ---- Barra de exportação ----
    def _criar_barra_exportacao(self) -> None:
        barra = self.menuBar()
        barra.setNativeMenuBar(False)

        menu = QMenu("Exportar", self)
        menu.addAction("Imagem da vista atual...", self._guardar_imagem)
        menu.addSeparator()
        menu.addAction("Livro Excel completo (.xlsx)...", self._exportar_excel)
        menu.addSeparator()

        sub_rigidez = menu.addMenu("Matriz de rigidez")
        sub_rigidez.addAction("NPZ esparso (.npz)...", self._exportar_matriz)
        sub_rigidez.addAction("Matrix Market (.mtx)...", self._exportar_matriz)
        sub_rigidez.addAction("Texto tabulado (.txt)...", self._exportar_matriz)

        sub_pot = menu.addMenu("Potenciais por nó")
        sub_pot.addAction("CSV (.csv)...", self._exportar_potenciais)
        sub_pot.addAction("Texto tabulado (.txt)...", self._exportar_potenciais)
        sub_pot.addAction("TSV (.tsv)...", self._exportar_potenciais)

        sub_campo = menu.addMenu("Campo elétrico")
        sub_campo.addAction("CSV (.csv)...", self._exportar_campo)
        sub_campo.addAction("Texto tabulado (.txt)...", self._exportar_campo)
        sub_campo.addAction("TSV (.tsv)...", self._exportar_campo)

        sub_elem = menu.addMenu("Elementos")
        sub_elem.addAction("CSV (.csv)...", self._exportar_elementos)
        sub_elem.addAction("Texto tabulado (.txt)...", self._exportar_elementos)
        sub_elem.addAction("TSV (.tsv)...", self._exportar_elementos)

        barra.addMenu(menu)

    # ---- Exportações (placeholders a serem implementados nos próximos commits) ----
    def _exportar_excel(self) -> None:
        QMessageBox.information(self, "Exportar Excel", "Funcionalidade em desenvolvimento.")
    def _exportar_matriz(self) -> None:
        QMessageBox.information(self, "Exportar Matriz", "Funcionalidade em desenvolvimento.")
    def _exportar_potenciais(self) -> None:
        QMessageBox.information(self, "Exportar Potenciais", "Funcionalidade em desenvolvimento.")
    def _exportar_campo(self) -> None:
        QMessageBox.information(self, "Exportar Campo", "Funcionalidade em desenvolvimento.")
    def _exportar_elementos(self) -> None:
        QMessageBox.information(self, "Exportar Elementos", "Funcionalidade em desenvolvimento.")


# ------------------------------------------------------------
# Função de arranque
# ------------------------------------------------------------
def iniciar_interface() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("TerraMEF")
    janela = JanelaMEF()
    janela.show()
    return app.exec()