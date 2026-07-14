"""
utils.py
========
Funções auxiliares para formatação, validação, etc.
"""

from typing import Optional
import numpy as np


def formatar(valor: Optional[float], unidade: str) -> str:
    """
    Formata um valor numérico com prefixo métrico (G, M, k, m, etc.) e unidade.

    Se o valor for None, não finito ou infinito, retorna '--'.
    Caso contrário, escolhe o prefixo adequado (G, M, k, '', m) e arredonda
    para 4 algarismos significativos.

    :param valor: Valor a formatar (pode ser None).
    :param unidade: Unidade base (ex: 'ohm', 'A', 'V').
    :return: String formatada (ex: '1.234 kohm').
    """
    if valor is None or not np.isfinite(valor):
        return "--"
    for limite, prefixo in (
        (1e9, "G"),
        (1e6, "M"),
        (1e3, "k"),
        (1.0, ""),
        (1e-3, "m"),
    ):
        if abs(valor) >= limite:
            return f"{valor / limite:.4g} {prefixo}{unidade}"
    return f"{valor:.4g} {unidade}"