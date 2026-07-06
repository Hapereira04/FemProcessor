"""
io_utils.py
===========
Módulo de entrada e saída (I/O) de dados para o simulador de Elementos Finitos (MEF).

Este ficheiro é responsável por fazer a ponte entre os ficheiros de texto em bruto
(fornecidos pelo gerador de malha ou pelo utilizador) e a matemática do simulador.
Ele extrai a geometria da peça (nós e coordenadas), a conectividade dos tetraedros,
as propriedades dos materiais (condutividade) e as voltagens da bateria.
"""

import numpy as np

def ler_nos_e_condicoes(caminho_ficheiro):
    """
    Lê as coordenadas dos nós e as condições de fronteira (voltagens conhecidas).

    Formato esperado no ficheiro de texto:
    x y z potencial

    potencial = -1.0 -> nó livre (para o programa calcular)
    potencial != -1.0 -> condição de Dirichlet (ex: cabo da bateria ligado)

    :param caminho_ficheiro: String contendo o caminho ou o nome do ficheiro de
                             texto a ser lido (exemplo: "pontos.txt").

    :return Matriz_Nos: Array NumPy de tamanho (N x 3) contendo as coordenadas
                        espaciais (x, y, z) de todos os nós da malha.
    :return Condicoes_Fronteira: Dicionário onde a chave (int) é o índice do nó
                                 e o valor (float) é a tensão aplicada em Volts.
    """
    Matriz_Nos = []
    Condicoes_Fronteira = {}

    with open(caminho_ficheiro, 'r') as ficheiro_aberto:
        for linha_texto in ficheiro_aberto:
            linha_texto = linha_texto.strip()

            # Ignorar linhas vazias ou comentários (que começam por #)
            if linha_texto and not linha_texto.startswith('#'):
                valores_linha = list(map(float, linha_texto.split()))

                if len(valores_linha) == 4:
                    # As 3 primeiras colunas são as coordenadas (x, y, z)
                    Matriz_Nos.append(valores_linha[:3])

                    indice_do_no = len(Matriz_Nos) - 1
                    valor_potencial = valores_linha[3]

                    # Se for diferente de -1.0, guardamos no dicionário de fronteiras
                    if valor_potencial != -1.0:
                        Condicoes_Fronteira[indice_do_no] = valor_potencial

    return np.array(Matriz_Nos), Condicoes_Fronteira


def ler_elementos_finais(caminho_ficheiro):
    """
    Lê a conectividade dos tetraedros e a condutividade do material.

    Formato esperado no ficheiro de texto:
    n0 n1 n2 n3 condutividade

    :param caminho_ficheiro: String contendo o caminho ou o nome do ficheiro de
                             texto a ser lido (exemplo: "elementos.txt").

    :return Matriz_Elementos: Array NumPy de inteiros (tamanho M x 4) onde cada linha
                              contém os índices dos 4 nós que compõem um tetraedro.
    :return Lista_Condutividades: Array NumPy 1D (tamanho M) contendo o valor da
                                  condutividade elétrica para cada tetraedro lido.
    """
    Matriz_Elementos = []
    Lista_Condutividades = []

    with open(caminho_ficheiro, 'r') as ficheiro_aberto:
        for linha_texto in ficheiro_aberto:
            linha_texto = linha_texto.strip()

            if linha_texto and not linha_texto.startswith('#'):
                valores_linha = list(map(float, linha_texto.split()))

                if len(valores_linha) == 5:
                    # Extrair os 4 nós que formam o tetraedro (convertendo para inteiros)
                    # Nota: Pressupõe que os nós começam no índice 0
                    nos_do_tetraedro = [int(indice) for indice in valores_linha[:4]]
                    Matriz_Elementos.append(nos_do_tetraedro)

                    # A 5ª coluna é a propriedade do material
                    valor_condutividade = valores_linha[4]
                    Lista_Condutividades.append(valor_condutividade)

    return np.array(Matriz_Elementos, dtype=int), np.array(Lista_Condutividades)