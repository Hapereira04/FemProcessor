"""
sidebar.py
==========
Define o painel lateral da aplicação, com controlos de ficheiros e cálculo.
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt


class Sidebar(QWidget):
    """
    Painel lateral da aplicação, contendo controlos de entrada e cálculo.

    :param parent: Widget pai (normalmente a janela principal).
    """

    # Sinal emitido quando o utilizador clica no botão "Calcular"
    calcular_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Caminhos dos ficheiros (predefinições)
        self.caminho_pontos: str = "ficheiros/pontos.txt"
        self.caminho_elementos: str = "ficheiros/elementos.txt"

        self._setup_ui()

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

        # Separador
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

        # Espaço flexível para empurrar os widgets para cima
        layout.addStretch(1)

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
        # Rótulo
        layout.addWidget(QLabel(titulo, objectName="rotulo"))

        # Linha com campo e botão
        linha = QHBoxLayout()
        campo = QLineEdit(valor_inicial)
        campo.setReadOnly(True)
        campo.setObjectName("campo_ficheiro")  # para estilização
        botao = QPushButton("Abrir")
        botao.clicked.connect(callback)

        linha.addWidget(campo, 1)
        linha.addWidget(botao)
        layout.addLayout(linha)

    def _escolher_pontos(self) -> None:
        """Abre um diálogo para selecionar o ficheiro de pontos."""
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar ficheiro de nós",
            self.caminho_pontos,
            "Texto (*.txt)"
        )
        if caminho:
            self.caminho_pontos = caminho
            # Atualiza o campo de texto correspondente
            self._atualizar_campo_ficheiro("pontos", caminho)

    def _escolher_elementos(self) -> None:
        """Abre um diálogo para selecionar o ficheiro de elementos."""
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar ficheiro de elementos",
            self.caminho_elementos,
            "Texto (*.txt)"
        )
        if caminho:
            self.caminho_elementos = caminho
            self._atualizar_campo_ficheiro("elementos", caminho)

    def _atualizar_campo_ficheiro(self, tipo: str, caminho: str) -> None:
        """
        Atualiza o QLineEdit correspondente ao tipo de ficheiro.

        :param tipo: "pontos" ou "elementos".
        :param caminho: Novo caminho a mostrar.
        """
        # Procura o campo pelo objectName (poderíamos guardar referências)
        for child in self.findChildren(QLineEdit):
            if child.objectName() == f"campo_{tipo}":
                child.setText(caminho)
                break
        else:
            # Fallback: se não encontrar, cria um novo (não deve acontecer)
            pass

    def obter_caminhos(self) -> tuple[str, str]:
        """
        Devolve os caminhos atuais dos ficheiros.

        :return: Tupla (caminho_pontos, caminho_elementos).
        """
        return self.caminho_pontos, self.caminho_elementos

    def definir_botao_calcular_habilitado(self, habilitado: bool) -> None:
        """Habilita ou desabilita o botão Calcular."""
        self.botao_calcular.setEnabled(habilitado)