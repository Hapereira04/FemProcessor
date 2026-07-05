"""
io_utils.py
===========
Módulo de entrada e saída (I/O) de dados para o simulador de Elementos Finitos (MEF).
"""
import numpy as np

def ler_nos_e_condicoes(caminho_ficheiro):
    """
    Lê as coordenadas dos nós e as condições de fronteira (voltagens conhecidas).
    """
    Matriz_Nos = []
    Condicoes_Fronteira = {}

    with open(caminho_ficheiro, 'r') as ficheiro_aberto:
        for linha_texto in ficheiro_aberto:
            linha_texto = linha_texto.strip()

            if linha_texto and not linha_texto.startswith('#'):
                valores_linha = list(map(float, linha_texto.split()))

                if len(valores_linha) == 4:
                    Matriz_Nos.append(valores_linha[:3])

                    indice_do_no = len(Matriz_Nos) - 1
                    valor_potencial = valores_linha[3]

                    # Se for diferente de -1.0, é uma Condição de Dirichlet (voltagem fixa)
                    if valor_potencial != -1.0:
                        Condicoes_Fronteira[indice_do_no] = valor_potencial

    return np.array(Matriz_Nos), Condicoes_Fronteira

def ler_elementos_finais(caminho_ficheiro):
    """
    Lê a conectividade dos tetraedros e a condutividade do material.
    """
    pass