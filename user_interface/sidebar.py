"""
sidebar.py
==========
Define o painel lateral da aplicação, com controlos de ficheiros, cálculo e visualização.
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QScrollArea, QFrame, QButtonGroup,
    QCheckBox, QSlider, QDoubleSpinBox
)


class Sidebar(QWidget):
    """
    Painel lateral da aplicação, contendo controlos de entrada, cálculo e visualização.

    :param parent: Widget pai (normalmente a janela principal).
    """

    # Sinais principais
    calcular_clicked = Signal()

    # Sinais de visualização
    modo_alterado = Signal(str)               # "superficie" ou "corte"
    eixo_alterado = Signal(str)               # "x", "y", "z"
    posicao_corte_alterada = Signal(float)
    mostrar_contornos_alterado = Signal(bool)
    mostrar_setas_alterado = Signal(bool)
    mostrar_malha_alterado = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Caminhos dos ficheiros (predefinições)
        self.caminho_pontos: str = "ficheiros/pontos.txt"
        self.caminho_elementos: str = "ficheiros/elementos.txt"

        # Limites do corte (inicializados depois)
        self._limite_min: float = 0.0
        self._limite_max: float = 1.0

        self._setup_ui()
        self._atualizar_visibilidade_corte(False)  # modo 3D por omissão

    def _setup_ui(self) -> None:
        """Constrói a interface do painel lateral."""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 24, 22, 20)
        layout.setSpacing(12)

        # Títulos
        titulo = QLabel("TerraMEF", objectName="titulo")
        subtitulo = QLabel("Simulador de potencial e aterramento", objectName="subtitulo")
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addSpacing(14)

        # Separador DADOS DA MALHA
        layout.addWidget(self._separador("DADOS DA MALHA"))

        # Campo: ficheiro de pontos
        self._adicionar_campo_ficheiro(
            layout,
            "Nós e fronteiras",
            self.caminho_pontos,
            self._escolher_pontos
        )

        # Campo: ficheiro de elementos
        self._adicionar_campo_ficheiro(
            layout,
            "Tetraedros e material",
            self.caminho_elementos,
            self._escolher_elementos
        )

        # Botão Calcular
        self.botao_calcular = QPushButton("Calcular simulação", objectName="primario")
        self.botao_calcular.clicked.connect(self.calcular_clicked.emit)
        layout.addWidget(self.botao_calcular)

        # Separador VISUALIZAÇÃO
        layout.addSpacing(10)
        layout.addWidget(self._separador("VISUALIZAÇÃO"))

        # ---- Modos 3D/Corte ----
        modos_layout = QHBoxLayout()
        self.botao_3d = QPushButton("3D")
        self.botao_corte = QPushButton("Corte")
        self.botao_3d.setCheckable(True)
        self.botao_corte.setCheckable(True)
        self.botao_3d.setChecked(True)
        grupo_modos = QButtonGroup(self)
        grupo_modos.setExclusive(True)
        grupo_modos.addButton(self.botao_3d)
        grupo_modos.addButton(self.botao_corte)
        self.botao_3d.clicked.connect(lambda: self.modo_alterado.emit("superficie"))
        self.botao_corte.clicked.connect(lambda: self.modo_alterado.emit("corte"))
        modos_layout.addWidget(self.botao_3d)
        modos_layout.addWidget(self.botao_corte)
        layout.addLayout(modos_layout)

        # ---- Eixos do corte (visíveis apenas no modo corte) ----
        self.label_eixo = QLabel("Orientação do corte", objectName="rotulo")
        layout.addWidget(self.label_eixo)
        eixos_layout = QHBoxLayout()
        self.grupo_eixos = QButtonGroup(self)
        self.grupo_eixos.setExclusive(True)
        self.botoes_eixos = []
        for eixo in ("x", "y", "z"):
            btn = QPushButton(eixo.upper())
            btn.setCheckable(True)
            btn.setChecked(eixo == "y")
            btn.clicked.connect(lambda checked, e=eixo: self.eixo_alterado.emit(e))
            self.grupo_eixos.addButton(btn)
            eixos_layout.addWidget(btn)
            self.botoes_eixos.append(btn)
        layout.addLayout(eixos_layout)

        # ---- Posição do plano de corte ----
        self.label_posicao = QLabel("Posição do plano", objectName="rotulo")
        layout.addWidget(self.label_posicao)

        self.slider_corte = QSlider(Qt.Horizontal)
        self.slider_corte.setRange(0, 1000)
        self.slider_corte.setValue(500)
        self.slider_corte.setSingleStep(1)
        self.slider_corte.setPageStep(10)
        self.slider_corte.valueChanged.connect(self._slider_alterado)
        layout.addWidget(self.slider_corte)

        self.posicao_corte = QDoubleSpinBox()
        self.posicao_corte.setDecimals(3)
        self.posicao_corte.setSuffix(" m")
        self.posicao_corte.setKeyboardTracking(False)
        self.posicao_corte.valueChanged.connect(self._posicao_alterada)
        layout.addWidget(self.posicao_corte)

        self.label_limites = QLabel("Limites: --", objectName="ajuda")
        layout.addWidget(self.label_limites)

        # ---- Checkboxes ----
        self.mostrar_contornos = QCheckBox("Mostrar curvas de potencial")
        self.mostrar_contornos.setChecked(True)
        self.mostrar_contornos.toggled.connect(self.mostrar_contornos_alterado.emit)
        layout.addWidget(self.mostrar_contornos)

        self.mostrar_setas = QCheckBox("Mostrar campo elétrico")
        self.mostrar_setas.toggled.connect(self.mostrar_setas_alterado.emit)
        layout.addWidget(self.mostrar_setas)

        self.mostrar_malha = QCheckBox("Mostrar arestas da malha")
        self.mostrar_malha.setChecked(True)
        self.mostrar_malha.toggled.connect(self.mostrar_malha_alterado.emit)
        layout.addWidget(self.mostrar_malha)

        # Espaço flexível para empurrar os widgets para cima
        layout.addStretch(1)

    # ---- Métodos auxiliares de UI ----
    def _separador(self, texto: str) -> QLabel:
        """Cria um rótulo com estilo de separador."""
        label = QLabel(texto, objectName="separador")
        return label

    def _adicionar_campo_ficheiro(
        self,
        layout: QVBoxLayout,
        titulo: str,
        valor_inicial: str,
        callback
    ) -> None:
        """
        Adiciona um campo de seleção de ficheiro ao layout.

        :param layout: Layout onde adicionar.
        :param titulo: Texto do rótulo.
        :param valor_inicial: Caminho inicial do ficheiro.
        :param callback: Função chamada ao clicar no botão "Abrir".
        """
        layout.addWidget(QLabel(titulo, objectName="rotulo"))
        linha = QHBoxLayout()
        campo = QLineEdit(valor_inicial)
        campo.setReadOnly(True)
        campo.setObjectName("campo_ficheiro")
        botao = QPushButton("Abrir")
        botao.clicked.connect(callback)
        linha.addWidget(campo, 1)
        linha.addWidget(botao)
        layout.addLayout(linha)

    # ---- Métodos para seleção de ficheiros ----
    def _escolher_pontos(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar ficheiro de nós",
            self.caminho_pontos, "Texto (*.txt)"
        )
        if caminho:
            self.caminho_pontos = caminho
            self._atualizar_campo_ficheiro("pontos", caminho)

    def _escolher_elementos(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar ficheiro de elementos",
            self.caminho_elementos, "Texto (*.txt)"
        )
        if caminho:
            self.caminho_elementos = caminho
            self._atualizar_campo_ficheiro("elementos", caminho)

    def _atualizar_campo_ficheiro(self, tipo: str, caminho: str) -> None:
        """Atualiza o QLineEdit correspondente ao tipo de ficheiro."""
        for child in self.findChildren(QLineEdit):
            if child.objectName() == f"campo_{tipo}":
                child.setText(caminho)
                break

    # ---- Métodos públicos ----
    def obter_caminhos(self) -> tuple[str, str]:
        """Devolve os caminhos atuais dos ficheiros."""
        return self.caminho_pontos, self.caminho_elementos

    def definir_botao_calcular_habilitado(self, habilitado: bool) -> None:
        """Habilita ou desabilita o botão Calcular."""
        self.botao_calcular.setEnabled(habilitado)

    def definir_limites_corte(self, limite_min: float, limite_max: float) -> None:
        """
        Define os limites do corte e actualiza os controlos.

        :param limite_min: Valor mínimo do eixo.
        :param limite_max: Valor máximo do eixo.
        """
        self._limite_min = limite_min
        self._limite_max = limite_max
        self.label_limites.setText(f"Limites: {limite_min:.3f} a {limite_max:.3f} m")
        self.posicao_corte.setRange(limite_min, limite_max)
        self.posicao_corte.setSingleStep((limite_max - limite_min) / 1000)
        # Repõe o slider para o centro
        self.slider_corte.setValue(500)
        self._slider_alterado(500)

    # ---- Slots internos ----
    def _slider_alterado(self, valor: int) -> None:
        """Emite a posição do corte quando o slider é movido."""
        frac = valor / 1000.0
        pos = self._limite_min + frac * (self._limite_max - self._limite_min)
        self.posicao_corte.blockSignals(True)
        self.posicao_corte.setValue(pos)
        self.posicao_corte.blockSignals(False)
        self.posicao_corte_alterada.emit(pos)

    def _posicao_alterada(self, pos: float) -> None:
        """Emite a posição do corte quando o spinbox é alterado."""
        self.posicao_corte_alterada.emit(pos)

    def _atualizar_visibilidade_corte(self, visivel: bool) -> None:
        """Mostra ou esconde os controlos do corte."""
        self.label_eixo.setVisible(visivel)
        for btn in self.botoes_eixos:
            btn.setVisible(visivel)
        self.label_posicao.setVisible(visivel)
        self.slider_corte.setVisible(visivel)
        self.posicao_corte.setVisible(visivel)
        self.label_limites.setVisible(visivel)