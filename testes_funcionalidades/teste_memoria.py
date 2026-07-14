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

    # ---------------------------------------------------------
    # 2. Matriz Esparsa (SciPy CSR)
    # ---------------------------------------------------------
    total_valores_nao_nulos = numero_nos * ligacoes_por_no
    dados = np.ones(total_valores_nao_nulos, dtype=np.float64)
    colunas = np.random.randint(0, numero_nos, total_valores_nao_nulos, dtype=np.int32)
    linhas_ptr = np.linspace(0, total_valores_nao_nulos, numero_nos + 1, dtype=np.int32)

    matriz_esparsa = sparse.csr_matrix(
        (dados, colunas, linhas_ptr),
        shape=(numero_nos, numero_nos)
    )

    peso_dados = matriz_esparsa.data.nbytes
    peso_indices = matriz_esparsa.indices.nbytes
    peso_ponteiros = matriz_esparsa.indptr.nbytes
    memoria_esparsa_mb = (peso_dados + peso_indices + peso_ponteiros) / (1024 * 1024)

    print(f"[SciPy]  Matriz Esparsa (CSR): {memoria_esparsa_mb:,.2f} MB")

    # ---------------------------------------------------------
    # 3. Conclusão
    # ---------------------------------------------------------
    if 'memoria_densa_mb' in locals():
        poupanca = (1 - (memoria_esparsa_mb / memoria_densa_mb)) * 100
        print("-" * 50)
        print(f"CONCLUSÃO: O formato CSR poupou {poupanca:.4f}% de memória RAM!")
        print("-" * 50 + "\n")


executar_teste_memoria(5000)
executar_teste_memoria(10000)
executar_teste_memoria(30000)