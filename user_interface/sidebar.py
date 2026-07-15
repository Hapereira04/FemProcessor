"""
Módulo do painel lateral esquerdo contendo os controlos de entrada,
opções de visualização e indicadores de resultados.
"""
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QWidget, QScrollArea, QLabel,
                               QHBoxLayout, QLineEdit, QPushButton, QButtonGroup,
                               QSlider, QDoubleSpinBox, QCheckBox, QFileDialog)
from PySide6.QtCore import Qt


class Sidebar(QFrame):
    """
    Componente visual que gere o menu lateral esquerdo da UI.
    Inclui scrollbar automática e organização vertical de definições.
    """

    def __init__(self, parent=None):
        """
        Construtor do painel lateral. Configura todos os widgets internos.

        :param parent: QWidget pai (normalmente a janela principal).
        """
        super().__init__(parent)
        self.setFixedWidth(330)
        self.setObjectName("sidebar")

        # Layout raiz do painel
        painel_layout = QVBoxLayout(self)
        painel_layout.setContentsMargins(0, 0, 0, 0)
        painel_layout.setSpacing(0)

        # Configuração da Scroll Area para ecrãs mais pequenos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Conteúdo efetivo da barra lateral
        conteudo_painel = QWidget()
        conteudo_painel.setStyleSheet("background: transparent;")
        lateral = QVBoxLayout(conteudo_painel)
        lateral.setContentsMargins(22, 24, 22, 20)
        lateral.setSpacing(12)

        # ====== TÍTULO ======
        titulo = QLabel("TerraMEF", objectName="titulo")
        subtitulo = QLabel("Simulador de potencial e aterramento", objectName="subtitulo")
        lateral.addWidget(titulo)
        lateral.addWidget(subtitulo)
        lateral.addSpacing(14)

        # ====== DADOS DA MALHA ======
        lateral.addWidget(self._separador("DADOS DA MALHA"))
        caixa_pontos, self.caminho_pontos = self._campo_ficheiro("Nos e fronteiras", "ficheiros/pontos.txt",
                                                                 self.escolher_pontos)
        caixa_elementos, self.caminho_elementos = self._campo_ficheiro("Tetraedros e material",
                                                                       "ficheiros/elementos.txt",
                                                                       self.escolher_elementos)
        lateral.addWidget(caixa_pontos)
        lateral.addWidget(caixa_elementos)

        self.botao_calcular = QPushButton("Calcular simulacao", objectName="primario")
        lateral.addWidget(self.botao_calcular)

        lateral.addSpacing(10)
        lateral.addWidget(self._separador("VISUALIZACAO"))

        # ====== MODOS DE VISTA ======
        linha_modos = QHBoxLayout()
        self.botao_superficie = QPushButton("3D")
        self.botao_corte = QPushButton("Corte")
        self.botao_superficie.setCheckable(True)
        self.botao_corte.setCheckable(True)
        self.botao_superficie.setChecked(True)  # Default ativo

        self.grupo_modos = QButtonGroup(self)
        self.grupo_modos.setExclusive(True)
        self.grupo_modos.addButton(self.botao_superficie)
        self.grupo_modos.addButton(self.botao_corte)
        linha_modos.addWidget(self.botao_superficie)
        linha_modos.addWidget(self.botao_corte)
        lateral.addLayout(linha_modos)

        # ====== FERRAMENTAS DE CORTE ======
        self.label_orientacao_corte = QLabel("Orientacao do corte", objectName="rotulo")
        lateral.addWidget(self.label_orientacao_corte)

        # Botões X, Y, Z
        linha_eixos = QHBoxLayout()
        self.grupo_eixos = QButtonGroup(self)
        self.grupo_eixos.setExclusive(True)
        self.botoes_eixos = []
        for eixo in ("x", "y", "z"):
            botao = QPushButton(eixo.upper())
            botao.setCheckable(True)
            botao.setChecked(eixo == "y")
            botao.setProperty("eixo", eixo)
            self.grupo_eixos.addButton(botao)
            linha_eixos.addWidget(botao)
            self.botoes_eixos.append(botao)
        lateral.addLayout(linha_eixos)

        # Controlo de profundidade de corte
        self.label_posicao_plano = QLabel("Posicao do plano", objectName="rotulo")
        lateral.addWidget(self.label_posicao_plano)

        self.slider_corte = QSlider(Qt.Orientation.Horizontal)
        self.slider_corte.setRange(0, 1000)
        self.slider_corte.setValue(500)  # Inicial no centro
        self.slider_corte.setSingleStep(1)
        self.slider_corte.setPageStep(10)
        lateral.addWidget(self.slider_corte)

        self.posicao_corte = QDoubleSpinBox()
        self.posicao_corte.setDecimals(3)
        self.posicao_corte.setSuffix(" m")
        self.posicao_corte.setKeyboardTracking(False)
        lateral.addWidget(self.posicao_corte)

        self.intervalo_corte = QLabel("Limites do corte: --", objectName="ajuda")
        lateral.addWidget(self.intervalo_corte)

        self.botao_repor_corte = QPushButton("Repor corte ao centro")
        lateral.addWidget(self.botao_repor_corte)

        # ====== OPÇÕES DE RENDERIZAÇÃO ======
        self.mostrar_contornos = QCheckBox("Mostrar curvas de potencial")
        self.mostrar_contornos.setChecked(True)
        lateral.addWidget(self.mostrar_contornos)

        self.mostrar_setas = QCheckBox("Mostrar campo eletrico")
        lateral.addWidget(self.mostrar_setas)

        self.mostrar_malha = QCheckBox("Mostrar arestas da malha")
        lateral.addWidget(self.mostrar_malha)

        # ====== INDICADORES DE RESULTADO ======
        lateral.addSpacing(8)
        lateral.addWidget(self._separador("RESULTADO"))
        self.indicadores = {}
        for chave, texto in (("resistencia", "Resistencia"), ("corrente", "Corrente"),
                             ("nos", "Nos"), ("elementos", "Elementos")):
            caixa = QLabel(f"<span>{texto}</span><b>--</b>", objectName="indicador")
            caixa.setTextFormat(Qt.TextFormat.RichText)
            self.indicadores[chave] = caixa
            lateral.addWidget(caixa)

        lateral.addStretch(1)

        # ====== BARRA DE ESTADO ======
        self.estado = QLabel("Pronto para calcular", objectName="estado")
        self.estado.setWordWrap(True)
        lateral.addWidget(self.estado)

        # Fechar hierarquia
        scroll_area.setWidget(conteudo_painel)
        painel_layout.addWidget(scroll_area)

    def _campo_ficheiro(self, titulo: str, valor: str, acao) -> tuple[QWidget, QLineEdit]:
        """
        Gera o widget combinado para escolher um ficheiro (Label + Caixa de Texto + Botão).

        :param titulo: Texto descritivo acima do campo.
        :param valor: Caminho inicial (default) na caixa de texto.
        :param acao: Função/Slot conectada ao clique do botão.
        :return: Tuplo contendo o widget contentor e o ponteiro para a QLineEdit.
        """
        contentor = QWidget()
        layout = QVBoxLayout(contentor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(QLabel(titulo, objectName="rotulo"))

        linha = QHBoxLayout()
        campo = QLineEdit(valor)
        campo.setReadOnly(True)
        botao = QPushButton("Abrir")
        botao.clicked.connect(acao)

        linha.addWidget(campo, 1)
        linha.addWidget(botao)
        layout.addLayout(linha)

        return contentor, campo

    @staticmethod
    def _separador(texto: str) -> QLabel:
        """Retorna uma Label estilizada como título de secção."""
        return QLabel(texto, objectName="separador")

    def escolher_pontos(self) -> None:
        """Abre a janela de diálogo para selecionar ficheiro de nós."""
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar ficheiro de nos", self.caminho_pontos.text(),
                                                 "Texto (*.txt)")
        if caminho:
            self.caminho_pontos.setText(caminho)

    def escolher_elementos(self) -> None:
        """Abre a janela de diálogo para selecionar ficheiro de elementos."""
        caminho, _ = QFileDialog.getOpenFileName(self, "Selecionar ficheiro de elementos",
                                                 self.caminho_elementos.text(), "Texto (*.txt)")
        if caminho:
            self.caminho_elementos.setText(caminho)