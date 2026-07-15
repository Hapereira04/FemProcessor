"""
user_interface
==============
Módulo que contém toda a interface gráfica do simulador TerraMEF.
"""
from .main_window import JanelaMEF, iniciar_interface
from .result_dataclass import ResultadoMEF
from .utils import formatar
from .worker import TrabalhadorCalculo
from .visualizer import Visualizer3D

__all__ = [
    "JanelaMEF",
    "iniciar_interface",
    "ResultadoMEF",
    "formatar",
    "TrabalhadorCalculo",
    "Visualizer3D",
]