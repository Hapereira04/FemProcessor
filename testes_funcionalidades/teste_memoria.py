"""
teste_memoria.py
=================
Script de validação para o RNF01: Desempenho e Gestão de Memória.
Compara o tamanho em RAM de uma Matriz Densa (NumPy) vs Matriz Esparsa (SciPy).
"""
import numpy as np
import scipy.sparse as sparse


def executar_teste_memoria(numero_nos, ligacoes_por_no=15):
    print("=" * 50)
    print(f" TESTE DE MEMÓRIA MEF: MALHA DE {numero_nos} NÓS")
    print("=" * 50)


executar_teste_memoria(5000)
executar_teste_memoria(10000)
executar_teste_memoria(30000)