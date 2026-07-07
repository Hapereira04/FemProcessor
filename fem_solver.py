"""
fem_solver.py
=============
Motor matemático do Metodo dos Elementos Finitos (MEF) 3D para tetraedros lineares.

Este módulo contém o "cérebro" da simulação de condução elétrica. É responsável
por toda a álgebra linear e física do problema: desde a formulação das matrizes
de rigidez (condutividade) até à resolução de sistemas de equações de grande escala.

Módulo concebido para trabalhar com matrizes esparsas do SciPy, garantindo
máxima velocidade e eficiência de memória na resolução de malhas 3D complexas.

Funções Disponíveis:
--------------------
* matriz_local_tetraedro :
    Calcula a contribuição de condutividade (Matriz 4x4) de um único tetraedro.

* montar_matriz_global :
    Agrupa todos os elementos da malha numa única Matriz Global esparsa (formato CSR).

* aplicar_condicoes_eliminacao :
    Aplica as voltagens da bateria através de particionamento matricial (Eliminação),
    descobre a voltagem de todos os nós e calcula a Resistência Elétrica da peça.

* gradiente_por_elemento :
    Usa o mapa de potenciais para calcular o vetor do Campo Elétrico (Ex, Ey, Ez)
    no interior de cada tetraedro.

Dependências:
-------------
* numpy
* scipy.sparse
* scipy.sparse.linalg
"""

import scipy.sparse as sparse
import scipy.sparse.linalg as spla
import numpy as np

def matriz_local_tetraedro(Coordenadas_Elemento, Condutividade=1.0):
    """
    Calcula a Matriz de Condutividade (Rigidez) local de um tetraedro linear (4 nós).

    :param Coordenadas_Elemento: Array NumPy ou lista (tamanho 4x3) contendo as
                                 coordenadas espaciais (x, y, z) dos 4 nós do tetraedro.
    :param Condutividade: Valor (float) correspondente à condutividade do material
                          específico deste tetraedro (Padrão = 1.0).

    :return: Matriz_Rigidez_Local, um Array NumPy (4x4) representando a contribuição
             deste elemento para o sistema global.
    """
    Coordenadas = Coordenadas_Elemento

    # 1. Matriz Jacobiana (Cálculo dos vetores direcionais a partir do Nó 0)
    Matriz_Jacobiana = np.array([
        Coordenadas[1] - Coordenadas[0],
        Coordenadas[2] - Coordenadas[0],
        Coordenadas[3] - Coordenadas[0]
    ])

    Inversa_Jacobiana = np.linalg.inv(Matriz_Jacobiana)

    # 2. Tabela de Gradientes (Derivadas das funções de forma N0, N1, N2, N3)
    Tabela_Gradientes = np.zeros((4, 3))

    # Os gradientes dos nós 1, 2 e 3 vêm diretamente da matriz inversa
    Tabela_Gradientes[1:] = Inversa_Jacobiana

    # O gradiente do nó 0 é o negativo da soma dos restantes
    Tabela_Gradientes[0] = -np.sum(Inversa_Jacobiana, axis=0)

    # 3. Cálculo do Volume do tetraedro
    Determinante_Jacobiana = np.linalg.det(Matriz_Jacobiana)
    Volume_Tetraedro = abs(Determinante_Jacobiana) / 6.0

    if Volume_Tetraedro < 1e-12:
        raise ValueError("Volume zero ou negativo detetado. Verifique a qualidade da malha.")

    # 4. Construção da Matriz de Rigidez Local (4x4)
    Matriz_Rigidez_Local = np.zeros((4, 4))

    for linha in range(4):
        for coluna in range(4):
            # O produto escalar entre os vetores gradientes
            produto_escalar = np.dot(Tabela_Gradientes[linha], Tabela_Gradientes[coluna])

            # Preenchimento da posição na matriz
            Matriz_Rigidez_Local[linha, coluna] = Condutividade * Volume_Tetraedro * produto_escalar

    return Matriz_Rigidez_Local


def montar_matriz_global(Matriz_Nos, Matriz_Elementos, Lista_Condutividades):
    """
    Monta a Matriz Global de Rigidez utilizando o formato esparso (COO -> CSR).
    Distribui os valores locais de cada tetraedro para as posições globais da peça.

    :param Matriz_Nos: Array NumPy (N x 3) contendo as coordenadas espaciais (x, y, z)
                       de todos os nós globais da malha.
    :param Matriz_Elementos: Array NumPy (M x 4) de inteiros, onde cada linha contém
                             os índices dos 4 nós que formam um tetraedro.
    :param Lista_Condutividades: Array NumPy (1D, tamanho M) contendo o valor da
                                 condutividade do material para cada tetraedro.

    :return: Matriz_Global_CSR, uma matriz esparsa do SciPy (formato CSR) de tamanho
             (N x N), pronta para receber as condições de fronteira e ser resolvida.
    """
    Numero_Nos = len(Matriz_Nos)
    Numero_Elementos = len(Matriz_Elementos)

    # Cada tetraedro gera uma matriz 4x4, logo contribui com 16 valores
    Total_Entradas = 16 * Numero_Elementos

    # 1. Preparação dos "Livros de Registos" (Pré-alocação super rápida do NumPy)
    lista_linhas = np.zeros(Total_Entradas, dtype=int)
    lista_colunas = np.zeros(Total_Entradas, dtype=int)
    lista_valores = np.zeros(Total_Entradas, dtype=float)

    contador = 0

    # 2. Ciclo principal: Calcular e espalhar a matriz de cada tetraedro
    for index_elemento, nos_do_tetraedro in enumerate(Matriz_Elementos):

        # Extrair as coordenadas e o material exclusivamente para este tetraedro
        Coordenadas_Elemento = Matriz_Nos[nos_do_tetraedro]
        Condutividade_Elemento = Lista_Condutividades[index_elemento]

        # Obter a matriz 4x4 da função que limpámos no passo anterior
        Matriz_Rigidez_Local = matriz_local_tetraedro(Coordenadas_Elemento, Condutividade=Condutividade_Elemento)

        # 3. Mapeamento Local -> Global (Distribuir os 16 valores)
        for linha_local in range(4):
            no_global_linha = nos_do_tetraedro[linha_local]

            for coluna_local in range(4):
                no_global_coluna = nos_do_tetraedro[coluna_local]

                # Preencher as listas esparsas na posição do contador atual
                lista_linhas[contador] = no_global_linha
                lista_colunas[contador] = no_global_coluna
                lista_valores[contador] = Matriz_Rigidez_Local[linha_local, coluna_local]

                contador += 1

    # 4. Construção da Matriz Global Esparsa (A função COO soma nós repetidos automaticamente)
    Matriz_Global_COO = sparse.coo_matrix(
        (lista_valores, (lista_linhas, lista_colunas)),
        shape=(Numero_Nos, Numero_Nos)
    )

    # Converter para o formato CSR que é o mais rápido para resolver equações
    return Matriz_Global_COO.tocsr()


def aplicar_condicoes_eliminacao(Matriz_Rigidez_Global, Condicoes_Fronteira):
    """
    Aplica as condições de contorno de Dirichlet e resolve o sistema de equações.
    Também calcula a resistência equivalente global do domínio.

    :param Matriz_Rigidez_Global: Matriz esparsa do SciPy (idealmente no formato CSR)
                                  de tamanho (N x N), representando a condutividade
                                  global da malha.
    :param Condicoes_Fronteira: Dicionário contendo as voltagens conhecidas (bateria).
                                A chave (int) é o índice do nó e o valor (float) é
                                a tensão em Volts. Exemplo: {0: 100.0, 14: 0.0}.

    :return Vetor_Potenciais_Final: Array NumPy 1D (tamanho N) contendo o mapa completo
                                    de voltagens da peça (nós conhecidos + calculados).
    :return Resistencia_Total: Valor (float) da resistência elétrica equivalente da peça
                               em Ohms. Retorna 'None' se não for possível calcular
                               (ex: diferença de tensão zero).
    """
    Numero_Nos = Matriz_Rigidez_Global.shape[0]

    # Identificar nós fixos (fronteira) e nós desconhecidos (livres)
    nos_fixos = list(Condicoes_Fronteira.keys())
    mascara_desconhecidos = np.ones(Numero_Nos, dtype=bool)
    mascara_desconhecidos[nos_fixos] = False
    nos_desconhecidos = np.where(mascara_desconhecidos)[0]

    # Vector de potenciais fixos conhecidos
    Potenciais_Fixos = np.array([Condicoes_Fronteira[no] for no in nos_fixos])

    # Extração de submatrizes esparsas
    K_dd = Matriz_Rigidez_Global[nos_desconhecidos, :][:, nos_desconhecidos]
    K_df = Matriz_Rigidez_Global[nos_desconhecidos, :][:, nos_fixos]

    # Construção do vetor de forças/cargas (lado direito da equação)
    Vetor_Cargas = -K_df @ Potenciais_Fixos

    # Resolver o sistema linear esparso principal
    Potenciais_Desconhecidos = spla.spsolve(K_dd, Vetor_Cargas)

    # Montar a matriz final de resultados (juntando os calculados com os fixos)
    Vetor_Potenciais_Final = np.zeros(Numero_Nos)
    Vetor_Potenciais_Final[nos_desconhecidos] = Potenciais_Desconhecidos
    Vetor_Potenciais_Final[nos_fixos] = Potenciais_Fixos

    # --- Cálculo Dinâmico da Resistência ---
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

    :param Matriz_Nos: Array NumPy (N x 3) contendo as coordenadas espaciais (x, y, z) de todos os nós da malha.
    :param Matriz_Elementos: Array NumPy (M x 4) contendo os índices dos 4 nós que compõem cada elemento tetraédrico.
    :param Vetor_Potenciais_Final: Array NumPy 1D contendo a voltagem calculada para cada nó da peça inteira.

    :return: Matriz_Campos_Eletricos, um Array NumPy (M x 3) onde cada linha representa o vetor 3D do Campo Elétrico (Ex, Ey, Ez) no respetivo tetraedro.
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

        # O gradiente matemático escalar do elemento
        Gradiente_Matematico = np.zeros(3)
        for no_local in range(4):
            Gradiente_Matematico += Voltagens_Locais[no_local] * Tabela_Gradientes[no_local]

        # O Campo Elétrico aponta na direção descendente do potencial (sinal negativo)
        Matriz_Campos_Eletricos[index_elemento] = -Gradiente_Matematico

    return Matriz_Campos_Eletricos