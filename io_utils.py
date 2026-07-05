"""
io_utils.py
===========
Módulo de entrada e saída (I/O) de dados para o simulador de Elementos Finitos (MEF).
"""
import numpy as np

def ler_nos_e_condicoes(caminho_ficheiro):
    """
    Lê as coordenadas dos nós da malha.
    """
    Matriz_Nos = []

    with open(caminho_ficheiro, 'r') as ficheiro_aberto:
        for linha_texto in ficheiro_aberto:
            linha_texto = linha_texto.strip()

            # Ignorar linhas vazias ou comentários (que começam por #)
            if linha_texto and not linha_texto.startswith('#'):
                valores_linha = list(map(float, linha_texto.split()))

                if len(valores_linha) == 4:
                    # Extrair apenas as 3 primeiras colunas (coordenadas x, y, z)
                    Matriz_Nos.append(valores_linha[:3])

    return np.array(Matriz_Nos)

def ler_elementos_finais(caminho_ficheiro):
    """
    Lê a conectividade dos tetraedros e a condutividade do material.
    """
    pass