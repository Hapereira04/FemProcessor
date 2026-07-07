"""
fem_solver.py
=============
Motor matemático do Metodo dos Elementos Finitos (MEF) 3D para tetraedros lineares.

Este módulo contém o "cérebro" da simulação de condução elétrica. É responsável
por toda a álgebra linear e física do problema: desde a formulação das matrizes
de rigidez (condutividade) até à resolução de sistemas de equações de grande escala.
"""

import scipy.sparse as sparse
import scipy.sparse.linalg as spla
import numpy as np

def matriz_local_tetraedro(Coordenadas_Elemento, Condutividade=1.0):
    """
    Calcula a Matriz de Condutividade (Rigidez) local de um tetraedro linear (4 nós).
    """
    Coordenadas = Coordenadas_Elemento

    Matriz_Jacobiana = np.array([
        Coordenadas[1] - Coordenadas[0],
        Coordenadas[2] - Coordenadas[0],
        Coordenadas[3] - Coordenadas[0]
    ])

    Inversa_Jacobiana = np.linalg.inv(Matriz_Jacobiana)

    Tabela_Gradientes = np.zeros((4, 3))
    Tabela_Gradientes[1:] = Inversa_Jacobiana
    Tabela_Gradientes[0] = -np.sum(Inversa_Jacobiana, axis=0)

    Determinante_Jacobiana = np.linalg.det(Matriz_Jacobiana)
    Volume_Tetraedro = abs(Determinante_Jacobiana) / 6.0

    if Volume_Tetraedro < 1e-12:
        raise ValueError("Volume zero ou negativo detetado. Verifique a qualidade da malha.")

    Matriz_Rigidez_Local = np.zeros((4, 4))
    for linha in range(4):
        for coluna in range(4):
            produto_escalar = np.dot(Tabela_Gradientes[linha], Tabela_Gradientes[coluna])
            Matriz_Rigidez_Local[linha, coluna] = Condutividade * Volume_Tetraedro * produto_escalar

    return Matriz_Rigidez_Local


def montar_matriz_global(Matriz_Nos, Matriz_Elementos, Lista_Condutividades):
    """
    Monta a Matriz Global de Rigidez utilizando o formato esparso (COO -> CSR).
    """
    Numero_Nos = len(Matriz_Nos)
    Numero_Elementos = len(Matriz_Elementos)
    Total_Entradas = 16 * Numero_Elementos

    lista_linhas = np.zeros(Total_Entradas, dtype=int)
    lista_colunas = np.zeros(Total_Entradas, dtype=int)
    lista_valores = np.zeros(Total_Entradas, dtype=float)

    contador = 0

    for index_elemento, nos_do_tetraedro in enumerate(Matriz_Elementos):
        Coordenadas_Elemento = Matriz_Nos[nos_do_tetraedro]
        Condutividade_Elemento = Lista_Condutividades[index_elemento]

        Matriz_Rigidez_Local = matriz_local_tetraedro(Coordenadas_Elemento, Condutividade=Condutividade_Elemento)

        for linha_local in range(4):
            no_global_linha = nos_do_tetraedro[linha_local]
            for coluna_local in range(4):
                no_global_coluna = nos_do_tetraedro[coluna_local]
                lista_linhas[contador] = no_global_linha
                lista_colunas[contador] = no_global_coluna
                lista_valores[contador] = Matriz_Rigidez_Local[linha_local, coluna_local]
                contador += 1

    Matriz_Global_COO = sparse.coo_matrix(
        (lista_valores, (lista_linhas, lista_colunas)),
        shape=(Numero_Nos, Numero_Nos)
    )

    return Matriz_Global_COO.tocsr()


def aplicar_condicoes_eliminacao(Matriz_Rigidez_Global, Condicoes_Fronteira):
    """
    Aplica as condições de contorno de Dirichlet e resolve o sistema de equações.
    """
    Numero_Nos = Matriz_Rigidez_Global.shape[0]

    nos_fixos = list(Condicoes_Fronteira.keys())
    mascara_desconhecidos = np.ones(Numero_Nos, dtype=bool)
    mascara_desconhecidos[nos_fixos] = False
    nos_desconhecidos = np.where(mascara_desconhecidos)[0]

    Potenciais_Fixos = np.array([Condicoes_Fronteira[no] for no in nos_fixos])

    K_dd = Matriz_Rigidez_Global[nos_desconhecidos, :][:, nos_desconhecidos]
    K_df = Matriz_Rigidez_Global[nos_desconhecidos, :][:, nos_fixos]

    Vetor_Cargas = -K_df @ Potenciais_Fixos
    Potenciais_Desconhecidos = spla.spsolve(K_dd, Vetor_Cargas)

    Vetor_Potenciais_Final = np.zeros(Numero_Nos)
    Vetor_Potenciais_Final[nos_desconhecidos] = Potenciais_Desconhecidos
    Vetor_Potenciais_Final[nos_fixos] = Potenciais_Fixos

    valores_voltagem = list(Condicoes_Fronteira.values())
    if len(valores_voltagem) > 0:
        Diferenca_Tensao = max(valores_voltagem) - min(valores_voltagem)
        Potencia_Dissipada = Vetor_Potenciais_Final @ (Matriz_Rigidez_Global @ Vetor_Potenciais_Final)

        if Diferenca_Tensao > 0 and abs(Potencia_Dissipada) > 1e-12:
            Resistencia_Total = (Diferenca_Tensao ** 2) / Potencia_Dissipada
        else:
            Resistencia_Total = None
    else:
        Resistencia_Total = None

    return Vetor_Potenciais_Final, Resistencia_Total


def gradiente_por_elemento(Matriz_Nos, Matriz_Elementos, Vetor_Potenciais_Final):
    """
    Calcula o gradiente do potencial elétrico (Campo Elétrico) no interior de cada tetraedro.

    :param Matriz_Nos: Array NumPy (N x 3) contendo as coordenadas espaciais.
    :param Matriz_Elementos: Array NumPy (M x 4) contendo os índices da malha.
    :param Vetor_Potenciais_Final: Array 1D com os potenciais (Volts) calculados.

    :return: Matriz (M x 3) com o vetor 3D do Campo Elétrico (Ex, Ey, Ez) por elemento.
    """
    Numero_Elementos = len(Matriz_Elementos)
    Matriz_Campos_Eletricos = np.zeros((Numero_Elementos, 3))

    for index_elemento, nos_do_tetraedro in enumerate(Matriz_Elementos):
        Coordenadas_Elemento = Matriz_Nos[nos_do_tetraedro]

        # Matriz Jacobiana sem a transposta (.T), alinhada com a formulação local
        Matriz_Jacobiana = np.array([
            Coordenadas_Elemento[1] - Coordenadas_Elemento[0],
            Coordenadas_Elemento[2] - Coordenadas_Elemento[0],
            Coordenadas_Elemento[3] - Coordenadas_Elemento[0]
        ]).T

        Inversa_Jacobiana = np.linalg.inv(Matriz_Jacobiana)

        Tabela_Gradientes = np.zeros((4, 3))
        Tabela_Gradientes[1:] = Inversa_Jacobiana
        Tabela_Gradientes[0] = -np.sum(Inversa_Jacobiana, axis=0)

        Voltagens_Locais = Vetor_Potenciais_Final[nos_do_tetraedro]

        Gradiente_Matematico = np.zeros(3)
        for no_local in range(4):
            Gradiente_Matematico += Voltagens_Locais[no_local] * Tabela_Gradientes[no_local]

        # O Campo Elétrico aponta na direção descendente do potencial (sinal negativo)
        Matriz_Campos_Eletricos[index_elemento] = -Gradiente_Matematico

    return Matriz_Campos_Eletricos