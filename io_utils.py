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
    Lê a conectividade dos tetraedros e a resistividade do material.

    Formato esperado no ficheiro de texto:
    n0 n1 n2 n3 resistividade

    :param caminho_ficheiro: String contendo o caminho ou o nome do ficheiro de
                             texto a ser lido (exemplo: "elementos.txt").

    :return Matriz_Elementos: Array NumPy de inteiros (tamanho M x 4) onde cada linha
                              contém os índices dos 4 nós que compõem um tetraedro.
    :return Lista_Resistividades: Array NumPy 1D (tamanho M) contendo o valor da
                                  resistividade elétrica para cada tetraedro lido.
    """
    Matriz_Elementos = []
    Lista_Resistividades = []

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
                    valor_resistividade = valores_linha[4]
                    Lista_Resistividades.append(valor_resistividade)

    elementos = np.array(Matriz_Elementos, dtype=int)
    resistividades = np.array(Lista_Resistividades, dtype=float)

    if len(elementos) == 0:
        raise ValueError("O ficheiro de elementos nao contem tetraedros validos.")
    if np.any(resistividades <= 0):
        raise ValueError("A resistividade de cada elemento deve ser positiva e maior que zero.")

    return elementos, resistividades


def reparar_malha_desconectada(Matriz_Nos, Matriz_Elementos, Condicoes_Fronteira):
    """
        Cura a malha fundindo nós duplicados (coordenadas praticamente iguais) que
        foram gerados como entidades separadas, atualizando a conectividade dos
        elementos e as condições de fronteira para os novos índices.

        O algoritmo:
            1. Arredonda as coordenadas dos nós para uma precisão de 5 casas decimais.
            2. Usa `np.unique` para identificar nós únicos (mesmo ponto físico).
            3. Cria uma nova matriz de nós apenas com os nós únicos.
            4. Reconstrói os elementos mapeando os índices antigos para os novos.
            5. Reconstrói as condições de fronteira, resolvendo conflitos quando dois
               nós com condições diferentes se fundem (prevalece o potencial mais alto).

        :param Matriz_Nos: np.ndarray de forma (N, 3) com as coordenadas (x, y, z) de cada nó.
        :param Matriz_Elementos: np.ndarray de forma (M, 4) com os índices dos 4 nós que
                                 compõem cada tetraedro (baseados na matriz original).
        :param Condicoes_Fronteira: dict[int, float] que mapeia o índice de um nó (original)
                                    ao potencial fixo (em V) nesse nó.
        :return: Uma tupla (Matriz_Nos_Nova, Matriz_Elementos_Nova, Condicoes_Fronteira_Nova)
                 onde:
                    - Matriz_Nos_Nova: np.ndarray (N', 3) com os nós únicos.
                    - Matriz_Elementos_Nova: np.ndarray (M, 4) com os índices atualizados.
                    - Condicoes_Fronteira_Nova: dict[int, float] com as condições atualizadas.
                 N' <= N, podendo ser menor se houverem duplicados.
        """

    print("\n[Diagnóstico] A procurar falhas na malha (Mesh Welding)...")

    # 1. Arredondar coordenadas para fundir pontos colados (precisão 5 casas decimais)
    #    Isto evita que diferenças mínimas (ex: 1e-8) sejam consideradas nós distintos.
    nos_arredondados = np.round(Matriz_Nos, decimals=5)

    # 2. O NumPy descobre quais nós são o mesmo ponto físico
    #    - axis=0: compara linhas inteiras (coordenadas x,y,z)
    #    - return_index: devolve os índices da primeira ocorrência de cada nó único
    #    - return_inverse: devolve um array que mapeia cada nó original para o índice do nó único
    nos_unicos, indices_unicos, mapa_inverso = np.unique(
        nos_arredondados, axis=0, return_index=True, return_inverse=True
    )

    # 3. Guardar apenas os nós reais (sem duplicados)
    #    Usamos os índices originais para manter a precisão original (não arredondada)
    Matriz_Nos_Nova = Matriz_Nos[indices_unicos]

    # 4. Atualizar os tetraedros para apontarem para a nova rede colada
    #    O mapa_inverso converte cada índice antigo para o índice do nó único correspondente
    Matriz_Elementos_Nova = mapa_inverso[Matriz_Elementos]

    # 5. Fundir as Condições de Fronteira (Bateria e Terra)
    Condicoes_Fronteira_Nova = {}
    for no_antigo, voltagem in Condicoes_Fronteira.items():
        no_novo = mapa_inverso[no_antigo]

        # Se dois nós se fundiram e um deles era a Vara (maior potencial), a Vara domina
        # Isto resolve conflitos: se dois nós se fundem e ambos têm condições fixas,
        # mantém-se o potencial mais elevado (geralmente o eléctrodo)
        if no_novo in Condicoes_Fronteira_Nova:
            if voltagem > Condicoes_Fronteira_Nova[no_novo]:
                Condicoes_Fronteira_Nova[no_novo] = voltagem
        else:
            Condicoes_Fronteira_Nova[no_novo] = voltagem

    # Estatística
    nos_removidos = len(Matriz_Nos) - len(Matriz_Nos_Nova)
    if nos_removidos > 0:
        print(f"O programa juntou {nos_removidos} nós que estavam desconectados.")
    else:
        print("A malha já estava perfeitamente interligada.")

    return Matriz_Nos_Nova, Matriz_Elementos_Nova, Condicoes_Fronteira_Nova