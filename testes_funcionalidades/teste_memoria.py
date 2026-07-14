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

    # ---------------------------------------------------------
    # 1. Matriz Densa (NumPy)
    # ---------------------------------------------------------
    try:
        matriz_densa = np.zeros((numero_nos, numero_nos), dtype=np.float64)
        memoria_densa_mb = matriz_densa.nbytes / (1024 * 1024)
        print(f"[NumPy]  Matriz Densa alocada: {memoria_densa_mb:,.2f} MB")
        del matriz_densa
    except MemoryError:
        memoria_densa_mb = (numero_nos ** 2 * 8) / (1024 * 1024)
        print(f"[NumPy]  ERRO FATAL: Falta de RAM! Exigiria {memoria_densa_mb:,.2f} MB.")


executar_teste_memoria(5000)
executar_teste_memoria(10000)
executar_teste_memoria(30000)