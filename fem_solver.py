"""
fem_solver.py
=============
Motor matemático do Metodo dos Elementos Finitos (MEF) 3D para tetraedros lineares.
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
    Também calcula a resistência equivalente global do domínio.
    """
    Numero_Nos = Matriz_Rigidez_Global.shape[0]

    # 1. Identificar nós fixos (fronteira) e nós desconhecidos (livres)
    nos_fixos = list(Condicoes_Fronteira.keys())
    mascara_desconhecidos = np.ones(Numero_Nos, dtype=bool)
    mascara_desconhecidos[nos_fixos] = False
    nos_desconhecidos = np.where(mascara_desconhecidos)[0]

    Potenciais_Fixos = np.array([Condicoes_Fronteira[no] for no in nos_fixos])

    # 2. Extração de submatrizes esparsas (Particionamento)
    K_dd = Matriz_Rigidez_Global[nos_desconhecidos, :][:, nos_desconhecidos]
    K_df = Matriz_Rigidez_Global[nos_desconhecidos, :][:, nos_fixos]

    # 3. Construção do vetor de forças/cargas (lado direito da equação)
    Vetor_Cargas = -K_df @ Potenciais_Fixos

    # 4. Resolver o sistema linear esparso principal
    Potenciais_Desconhecidos = spla.spsolve(K_dd, Vetor_Cargas)

    # 5. Montar a matriz final de resultados (juntando os calculados com os fixos)
    Vetor_Potenciais_Final = np.zeros(Numero_Nos)
    Vetor_Potenciais_Final[nos_desconhecidos] = Potenciais_Desconhecidos
    Vetor_Potenciais_Final[nos_fixos] = Potenciais_Fixos

    # 6. Cálculo Dinâmico da Resistência Elétrica Equivalente
    valores_voltagem = list(Condicoes_Fronteira.values())
    if len(valores_voltagem) > 0:
        Diferenca_Tensao = max(valores_voltagem) - min(valores_voltagem)
        # Potência Dissipada (Energia) = V * K * V
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
    """
    pass