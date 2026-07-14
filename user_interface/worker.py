"""
worker.py
==========
Define o trabalhador que executa a simulação MEF numa thread separada.
"""

from __future__ import annotations

import traceback
from typing import Optional

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

import io_utils
import fem_solver
from .result_dataclass import ResultadoMEF


class TrabalhadorCalculo(QObject):
    """
    Executa o cálculo do MEF numa thread separada, mantendo a interface responsiva.

    Emite sinais para comunicar o progresso, o resultado final ou uma falha.

    :param ficheiro_pontos: Caminho para o ficheiro de nós e condições.
    :param ficheiro_elementos: Caminho para o ficheiro de elementos e condutividades.
    """

    # Sinais
    estado = Signal(str)                    # Mensagens de progresso
    concluido = Signal(ResultadoMEF)        # Resultado da simulação
    falhou = Signal(str)                    # Mensagem de erro (traceback)

    def __init__(self, ficheiro_pontos: str, ficheiro_elementos: str) -> None:
        super().__init__()
        self.ficheiro_pontos = ficheiro_pontos
        self.ficheiro_elementos = ficheiro_elementos

    @Slot()
    def executar(self) -> None:
        """
        Executa a simulação: leitura, reparação, montagem da matriz,
        resolução do sistema e cálculo dos gradientes.

        Em caso de sucesso, emite o sinal `concluido` com um objecto ResultadoMEF.
        Em caso de falha, emite `falhou` com o traceback da excepção.
        """
        try:
            self.estado.emit("A ler geometria e condições de fronteira...")
            nos, condicoes = io_utils.ler_nos_e_condicoes(self.ficheiro_pontos)
            elementos, condutividades = io_utils.ler_elementos_finais(self.ficheiro_elementos)

            self.estado.emit("A reparar a malha (fundir nós duplicados)...")
            nos, elementos, condicoes = io_utils.reparar_malha_desconectada(
                nos, elementos, condicoes
            )

            # Validações básicas
            if len(condicoes) < 2:
                raise ValueError(
                    "São necessárias pelo menos duas condições de potencial "
                    "(ex: eléctrodo e referência)."
                )
            if np.max(elementos) >= len(nos) or np.min(elementos) < 0:
                raise ValueError(
                    "O ficheiro de elementos contém um índice de nó inválido."
                )

            self.estado.emit("A montar a matriz de rigidez global...")
            matriz = fem_solver.montar_matriz_global(nos, elementos, condutividades)

            self.estado.emit("A resolver o sistema (potenciais e campo eléctrico)...")
            potenciais, resistencia = fem_solver.aplicar_condicoes_eliminacao(
                matriz, condicoes
            )

            # Verifica se os potenciais são finitos
            if not np.all(np.isfinite(potenciais)):
                raise ValueError(
                    "O cálculo produziu potenciais inválidos (NaN ou infinito). "
                    "Verifique a malha e as condições de fronteira."
                )

            gradientes = fem_solver.gradiente_por_elemento(nos, elementos, potenciais)

            # Prepara o resultado
            resultado = ResultadoMEF(
                nos=nos,
                elementos=elementos,
                potenciais=potenciais,
                gradientes=gradientes,
                condicoes=condicoes,
                resistencia=resistencia,
                matriz_rigidez=matriz,
            )

            self.estado.emit("Cálculo concluído com sucesso.")
            self.concluido.emit(resultado)

        except Exception as e:
            # Emite o traceback completo para diagnóstico
            self.falhou.emit(traceback.format_exc())