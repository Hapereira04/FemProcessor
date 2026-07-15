"""
Módulo de gestão de folhas de estilo (CSS / QSS) da interface.
"""

def get_stylesheet() -> str:
    """
    Fornece a folha de estilos global para a aplicação PySide6.

    :return: String contendo as regras QSS (estilo escuro moderno).
    """
    return """
        QMainWindow { background: #101827; color: #e5edf8; }
        QMenuBar { background: #0b1220; color: #dce7f6; border-bottom: 1px solid #243248; padding: 4px 8px; }
        QMenuBar::item { background: transparent; padding: 6px 12px; border-radius: 5px; }
        QMenuBar::item:selected { background: #1d304b; }
        QMenu { background: #111c2d; color: #dce7f6; border: 1px solid #2b3c56; padding: 5px; }
        QMenu::item { padding: 8px 30px 8px 12px; border-radius: 4px; }
        QMenu::item:selected { background: #1d4e63; }
        #sidebar { background: #0b1220; border-right: 1px solid #243248; }
        #navegacao { background: #0d1727; border-left: 1px solid #243248; }
        #cabecalho { background: #101827; border-bottom: 1px solid #243248; }
        #titulo { font-size: 27px; font-weight: 800; color: #f8fafc; }
        #subtitulo { font-size: 12px; color: #8fa2bd; }
        #separador { color: #6ee7cf; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
        #rotulo { color: #aab9ce; font-size: 11px; font-weight: 600; }
        #titulo_vista { font-size: 16px; font-weight: 700; color: #f8fafc; }
        #estado { color: #9fb0c9; font-size: 11px; padding-top: 6px; }
        #mensagem_topo { color: #9fb0c9; font-size: 12px; padding-left: 18px; }
        #ajuda { color: #7085a4; font-size: 10px; }
        #posicao_lateral { color: #dbeafe; font-size: 12px; font-weight: 700; padding: 7px 0; }
        #indicador { background: #121d30; border: 1px solid #223149; border-radius: 8px; padding: 8px 10px; }
        #indicador span { color: #91a4bf; font-size: 11px; } #indicador b { color: #f8fafc; font-size: 14px; }
        QPushButton { background: #17243a; color: #dce7f6; border: 1px solid #2b3c56; border-radius: 7px; padding: 8px 10px; font-weight: 600; }
        QPushButton:hover { background: #233653; border-color: #42638f; }
        QPushButton:checked { background: #164e63; border-color: #2dd4bf; color: white; }
        QPushButton:disabled { background: #172033; color: #64748b; }
        QLineEdit { background: #111c2d; color: #cbd5e1; border: 1px solid #2b3c56; border-radius: 6px; padding: 7px; font-size: 11px; }
        QCheckBox { color: #c5d2e4; font-size: 12px; spacing: 7px; }
        QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #48617f; border-radius: 3px; background: #111c2d; }
        QCheckBox::indicator:checked { background: #14b8a6; border-color: #14b8a6; }
        QSlider::groove:horizontal { height: 4px; background: #2a3a52; border-radius: 2px; }
        QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px; background: #2dd4bf; }
    """