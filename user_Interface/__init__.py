"""
user_interface
==============
Módulo que contém toda a interface gráfica do simulador TerraMEF.
"""
from .main_window import JanelaMEF
from .result_dataclass import ResultadoMEF
from .utils import formatar
from .main_window import JanelaMEF, iniciar_interface

__all__ = ["JanelaMEF", "ResultadoMEF", "formatar"]