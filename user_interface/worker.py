"""
Módulo responsável pela execução paralela (Multithreading) do cálculo MEF.
Isto evita que a janela principal (GUI) congele durante matrizes grandes.
"""

import traceback
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

import fem_solver
import io_utils
from .result_dataclass import ResultadoMEF

class TrabalhadorCalculo(QObject):
    """
    Classe Operária (Worker) encapsulando o processamento do MEF.
    Executa numa QThread secundária.
    """
    concluido = Signal(object)
    falhou = Signal(str)
    estado = Signal(str)

    def __init__(self, ficheiro_pontos: str, ficheiro_elementos: str) -> None:
        """
        Inicializa o trabalhador com os ficheiros escolhidos na UI.

        :param ficheiro_pontos: Caminho para o ficheiro de nós.
        :param ficheiro_elementos: Caminho para o ficheiro de tetraedros.
        """
        super().__init__()
        self.ficheiro_pontos = ficheiro_pontos
        self.ficheiro_elementos = ficheiro_elementos

    @Slot()
    def executar(self) -> None:
        """
        Metodo principal engatado no arranque da QThread.
        Lê ficheiros, repara a malha, monta o sistema linear e resolve os potenciais.
        """
        try:
            self.estado.emit("A ler geometria e condicoes...")

            # Leitura e reparação de dados
            nos, condicoes = io_utils.ler_nos_e_condicoes(self.ficheiro_pontos)
            elementos, condutividades = io_utils.ler_elementos_finais(self.ficheiro_elementos)
            nos, elementos, condicoes = io_utils.reparar_malha_desconectada(nos, elementos, condicoes)

            # Validações de sanidade
            if len(condicoes) < 2:
                raise ValueError("Sao necessarias pelo menos duas condicoes de potencial (ex: bateria e terra).")
            if np.max(elementos) >= len(nos) or np.min(elementos) < 0:
                raise ValueError("O ficheiro de elementos contem um indice de no invalido (fora dos limites).")

            self.estado.emit("A montar a matriz global...")

            # Cria a matriz de condutividade global (CSR Sparse Matrix)
            matriz = fem_solver.montar_matriz_global(nos, elementos, condutividades)

            self.estado.emit("A resolver potenciais e campo eletrico...")

            # Resolve o sistema linear Ku = F
            potenciais, resistencia = fem_solver.aplicar_condicoes_eliminacao(matriz, condicoes)

            # Validação dos resultados numéricos
            if not np.all(np.isfinite(potenciais)):
                raise ValueError(
                    "O calculo produziu potenciais invalidos (Inf ou NaN). Verifique a malha e as fronteiras.")

            # Cálculo de gradientes (Campo Elétrico)
            gradientes = fem_solver.gradiente_por_elemento(nos, elementos, potenciais)

            # Empacotar resultado e emitir sinal de sucesso
            self.concluido.emit(ResultadoMEF(
                nos=nos, elementos=elementos, potenciais=potenciais,
                gradientes=gradientes, condicoes=condicoes, resistencia=resistencia,
                matriz_rigidez=matriz,
            ))

        except Exception:
            # Em caso de falha, captura o log do erro e emite para a interface
            self.falhou.emit(traceback.format_exc())