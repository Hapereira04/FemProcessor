"""
Estruturas de dados para o armazenamento dos resultados da simulação.
"""

from dataclasses import dataclass
import numpy as np

@dataclass
class ResultadoMEF:
    """
    Agrupa todos os resultados numéricos obtidos pelo motor matemático MEF.

    :param nos: Array NumPy (N x 3) com as coordenadas globais da malha.
    :param elementos: Array NumPy (M x 4) com a conectividade dos tetraedros.
    :param potenciais: Array NumPy 1D (tamanho N) com a voltagem em cada nó.
    :param gradientes: Array NumPy (M x 3) com o vetor do Campo Elétrico (Ex, Ey, Ez) por elemento.
    :param condicoes: Dicionário contendo as voltagens fixas aplicadas {id_no: voltagem}.
    :param resistencia: Valor em Ohms da resistência equivalente calculada (pode ser None se falhar).
    :param matriz_rigidez: Objeto da matriz esparsa global gerada pelo SciPy.
    """
    nos: np.ndarray
    elementos: np.ndarray
    potenciais: np.ndarray
    gradientes: np.ndarray
    condicoes: dict[int, float]  # no, volts
    resistencia: float | None
    matriz_rigidez: object