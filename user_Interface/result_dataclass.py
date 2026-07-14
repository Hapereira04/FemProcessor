"""
result_dataclass.py
===================
Define a estrutura de dados que transporta os resultados da simulação.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np


@dataclass
class ResultadoMEF:
    """
    Agrupa todos os dados resultantes da simulação de Elementos Finitos.

    :param nos: Coordenadas dos nós (N×3).
    :param elementos: Conectividade dos tetraedros (M×4), índices 0‑based.
    :param potenciais: Potencial eléctrico em cada nó (array N).
    :param gradientes: Campo eléctrico (gradiente do potencial) em cada elemento (M×3).
    :param condicoes: Dicionário {índice_do_nó: potencial_fixo_em_Volts}.
    :param resistencia: Resistência equivalente do sistema (Ohm), ou None.
    :param matriz_rigidez: Matriz de rigidez global (objecto esparso, ex: CSR).
    """
    nos: np.ndarray
    elementos: np.ndarray
    potenciais: np.ndarray
    gradientes: np.ndarray
    condicoes: dict[int, float]
    resistencia: Optional[float]
    matriz_rigidez: Any  # scipy.sparse.csr_matrix ou similar