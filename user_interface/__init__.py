"""
Módulo de Interface Gráfica (UI) para o TerraMEF.
Este pacote contém a arquitetura modular da aplicação PyQt/PySide6,
separando a lógica de apresentação, visualização 3D e processamento paralelo.
"""

from .main_window import iniciar_interface

__all__ = ["iniciar_interface"]