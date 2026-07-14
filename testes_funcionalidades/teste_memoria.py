"""
teste_memoria.py
=================
Script de validação para o RNF01: Desempenho e Gestão de Memória.

Compara o tamanho em RAM de uma Matriz Densa (NumPy) vs Matriz Esparsa (SciPy)
para demonstrar a eficiência do formato CSR (Compressed Sparse Row) no contexto
do Metodo dos Elementos Finitos (MEF).

O script executa o teste para três tamanhos de malha: 5 000, 10 000 e 30 000 nós.
"""

import numpy as np
import scipy.sparse as sparse


def executar_teste_memoria(numero_nos: int, ligacoes_por_no: int = 15) -> None:
    """
    Executa o teste de memória para um determinado número de nós.

    O teste:
        1. Tenta alocar uma matriz densa (N×N) em NumPy – se falhar por falta de
           memória, regista o erro e estima o tamanho teórico.
        2. Constrói uma matriz esparsa no formato CSR (SciPy) com um número fixo
           de ligações por nó (por omissão, 15) e calcula o seu peso real em RAM.
        3. Apresenta a poupança percentual de memória.

    :param numero_nos: Número de nós (dimensão N da matriz N×N).
    :param ligacoes_por_no: Número médio de vizinhos por nó (afeta a densidade).
    :return: None (apenas imprime os resultados no ecrã).
    """
    print("=" * 50)
    print(f" TESTE DE MEMÓRIA MEF: MALHA DE {numero_nos} NÓS")
    print("=" * 50)

    # 1. Matriz Densa (NumPy) – abordagem clássica mas pesada
    try:
        # Tenta alocar uma matriz N×N de doubles (8 bytes cada)
        matriz_densa = np.zeros((numero_nos, numero_nos), dtype=np.float64)
        # Acede ao atributo .nbytes para obter o tamanho exato em bytes
        memoria_densa_mb = matriz_densa.nbytes / (1024 * 1024)
        print(f"[NumPy]  Matriz Densa alocada: {memoria_densa_mb:,.2f} MB")

        # Liberta imediatamente a memória para evitar sobrecarga
        del matriz_densa
    except MemoryError:
        # Se a alocação falhar, calcula o valor teórico (N² × 8 bytes)
        memoria_densa_mb = (numero_nos ** 2 * 8) / (1024 * 1024)
        print(f"[NumPy]  ERRO FATAL: Falta de RAM! Exigiria {memoria_densa_mb:,.2f} MB.")

    # 2. Matriz Esparsa (SciPy CSR) – solução eficiente
    # Cada nó liga-se a um número fixo de vizinhos (parâmetro)
    total_valores_nao_nulos = numero_nos * ligacoes_por_no

    # Cria arrays fictícios para ocupar o espaço correto da matriz CSR
    dados = np.ones(total_valores_nao_nulos, dtype=np.float64)
    colunas = np.random.randint(0, numero_nos, total_valores_nao_nulos, dtype=np.int32)
    # O array indptr tem tamanho (N + 1) e define os inícios de cada linha
    linhas_ptr = np.linspace(0, total_valores_nao_nulos, numero_nos + 1, dtype=np.int32)

    matriz_esparsa = sparse.csr_matrix(
        (dados, colunas, linhas_ptr),
        shape=(numero_nos, numero_nos)
    )

    # O peso em RAM de uma CSR é a soma dos três arrays internos:
    #   - data: valores não nulos
    #   - indices: índices das colunas
    #   - indptr: ponteiros para o início de cada linha
    peso_dados = matriz_esparsa.data.nbytes
    peso_indices = matriz_esparsa.indices.nbytes
    peso_ponteiros = matriz_esparsa.indptr.nbytes
    memoria_esparsa_mb = (peso_dados + peso_indices + peso_ponteiros) / (1024 * 1024)

    print(f"[SciPy]  Matriz Esparsa (CSR): {memoria_esparsa_mb:,.2f} MB")

    # 3. Conclusão
    if 'memoria_densa_mb' in locals():
        poupanca = (1 - (memoria_esparsa_mb / memoria_densa_mb)) * 100
        print("-" * 50)
        print(f"CONCLUSÃO: O formato CSR poupou {poupanca:.4f}% de memória RAM!")
        print("-" * 50 + "\n")

# Execução automática dos testes para três tamanhos de malha
if __name__ == "__main__":
    executar_teste_memoria(5000)   # densa ≈ 200 MB, CSR ≈ 2.4 MB
    executar_teste_memoria(10000)  # densa ≈ 800 MB, CSR ≈ 4.8 MB
    executar_teste_memoria(30000)  # densa ≈ 7.2 GB, CSR ≈ 14.4 MB