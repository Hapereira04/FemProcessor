"""
Módulo para a janela 3D da direita, contendo o wrapper do PyVista.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor


class ViewerWidget(QWidget):
    """
    Controla o lado direito da interface: o visualizador OpenGL 3D
    e o menu de atalhos em sobreposição (overlay).
    """

    def __init__(self, parent=None):
        """
        Constrói o cabeçalho e incorpora o QtInteractor da biblioteca PyVista.

        :param parent: QWidget pai (geralmente a janela principal).
        """
        super().__init__(parent)
        area_layout = QVBoxLayout(self)
        area_layout.setContentsMargins(0, 0, 0, 0)

        # ====== CABEÇALHO DO VISUALIZADOR ======
        cabecalho = QFrame(objectName="cabecalho")
        cabecalho_layout = QHBoxLayout(cabecalho)
        cabecalho_layout.setContentsMargins(22, 12, 18, 12)

        self.titulo_vista = QLabel("Vista 3D do potencial", objectName="titulo_vista")
        cabecalho_layout.addWidget(self.titulo_vista)

        self.mensagem_topo = QLabel("Pronto para calcular", objectName="mensagem_topo")
        cabecalho_layout.addWidget(self.mensagem_topo, 1)
        cabecalho_layout.addStretch(1)

        self.botao_repor = QPushButton("Repor camara")
        cabecalho_layout.addWidget(self.botao_repor)

        area_layout.addWidget(cabecalho)

        # ====== MOTOR 3D DO PYVISTA ======
        self.visualizador = QtInteractor(self)
        self.visualizador.interactor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.visualizador.set_background("#101827", top="#172238")  # Fundo gradiente
        self.visualizador.add_text("Carregue uma malha e calcule para iniciar.", position="upper_left", font_size=13,
                                   color="#cbd5e1")
        self.visualizador.add_axes(color="#cbd5e1")  # Eixos XYZ no canto

        corpo_vista = QWidget()
        corpo_layout = QHBoxLayout(corpo_vista)
        corpo_layout.setContentsMargins(0, 0, 0, 0)
        corpo_layout.setSpacing(0)
        corpo_layout.addWidget(self.visualizador.interactor, 1)

        # ====== NAVEGAÇÃO DE CORTE (VISUAL ON-CANVAS) ======
        self.navegacao_corte = QFrame(objectName="navegacao")
        self.navegacao_corte.setFixedWidth(92)
        nav_layout = QVBoxLayout(self.navegacao_corte)
        nav_layout.setContentsMargins(12, 18, 12, 18)
        nav_layout.setSpacing(8)

        titulo_nav = QLabel("CORTE", objectName="separador")
        titulo_nav.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(titulo_nav)

        self.posicao_lateral = QLabel("--", objectName="posicao_lateral")
        self.posicao_lateral.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.posicao_lateral)

        # Geração dos botões de passo rápido (+1, +10, etc.)
        self.botoes_navegacao = []
        opcoes_passo = (("-10", -10, "Mover 10 passos"), ("-", -1, "Mover 1 passo"),
                        ("+", 1, "Mover 1 passo"), ("+10", 10, "Mover 10 passos"))

        for texto, passo, dica in opcoes_passo:
            botao = QPushButton(texto)
            botao.setToolTip(dica)
            botao.setProperty("passo", passo)
            self.botoes_navegacao.append(botao)
            nav_layout.addWidget(botao)

        ajuda = QLabel("A / D\n1 passo\nShift+A / D\n10 passos", objectName="ajuda")
        nav_layout.addWidget(ajuda)
        nav_layout.addStretch(1)

        corpo_layout.addWidget(self.navegacao_corte)
        area_layout.addWidget(corpo_vista, 1)