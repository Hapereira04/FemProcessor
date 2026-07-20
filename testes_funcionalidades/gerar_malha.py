"""
gerar_malha.py
==============
Script para gerar malhas 3D de tetraedros para simulação de aterramento.

Utiliza o Gmsh para criar uma geometria composta por uma caixa de terra
e uma ou mais varas cilíndricas. Gera os ficheiros `pontos.txt` e
`elementos.txt` no formato esperado pelo simulador MEF (io_utils).

O script:
    1. Define os parâmetros da simulação (dimensões, resistividade, potencial).
    2. Constrói a geometria (caixa + cilindros) e subtrai as varas.
    3. Gera uma malha de tetraedros com refinamento local.
    4. Extrai os nós e elementos, reconstruindo índices locais.
    5. Atribui condições de fronteira (0 V nas faces exteriores, V_vara na vara).
    6. Grava os ficheiros de entrada para o simulador.
"""

import gmsh
import numpy as np
import os


def gerar_malha_avancada(pasta: str = ".") -> None:
    """
    Gera a malha 3D e os ficheiros de entrada para o simulador MEF.

    Os parâmetros da simulação são definidos internamente (podem ser
    alterados directamente no código). A função cria:
        - pontos.txt: cada linha com "x y z potencial"
        - elementos.txt: cada linha com "n0 n1 n2 n3 resistividade"

    :param pasta: Diretório onde serão criados os ficheiros (por omissão, o atual).
    :return: None (apenas grava ficheiros e imprime diagnóstico).
    """
    # 1. PARÂMETROS DA SIMULAÇÃO
    num_varas = 1                # Número de varas (1 ou 2)
    dist_varas = 2.0             # Distância entre varas (apenas para num_varas=2)
    diam_vara = 0.0218           # Diâmetro da vara (m)
    comp_vara = 3.0              # Comprimento da vara (m)
    L_terra = 60.0               # Largura/comprimento da caixa de terra (m)
    prof_terra = 40.0            # Profundidade da caixa de terra (m)
    V_vara = 1000000.0           # Potencial aplicado à vara (V)
    Resistividade_Terra = 1000.0 # Resistividade do solo (Ohm.m) - (Equivalente a 0.001 S/m)

    print("A iniciar o motor Gmsh...")
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)  # Suprime output do Gmsh
    gmsh.model.add("Malha_Vara_Terra")

    # 2. CONSTRUÇÃO DA GEOMETRIA
    # Caixa de terra (centrada em X,Y; topo em z=0, fundo em z=-prof_terra)
    terra = gmsh.model.occ.addBox(-L_terra / 2, -L_terra / 2, -prof_terra,
                                  L_terra, L_terra, prof_terra)

    varas = []
    raio = diam_vara / 2.0
    margem = 0.1  # Pequena extensão para garantir que a vara atravessa o topo

    if num_varas == 1:
        # Vara única ao centro
        v1 = gmsh.model.occ.addCylinder(0, 0, margem, 0, 0, -comp_vara - margem, raio)
        varas.append((3, v1))
    else:
        # Duas varas simétricas em X
        v1 = gmsh.model.occ.addCylinder(-dist_varas / 2, 0, margem,
                                        0, 0, -comp_vara - margem, raio)
        v2 = gmsh.model.occ.addCylinder(dist_varas / 2, 0, margem,
                                        0, 0, -comp_vara - margem, raio)
        varas.append((3, v1))
        varas.append((3, v2))

    # Subtrai as varas da terra (cria o furo)
    gmsh.model.occ.cut([(3, terra)], varas, removeObject=True, removeTool=True)
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()

    # 3. GERAÇÃO DA MALHA
    print("A gerar a malha de tetraedros...")
    # Algoritmos de malha (6 = Frontal-Delaunay para 2D, 10 = HXT para 3D)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)
    # Tamanhos de elemento (refinamento junto à vara)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", diam_vara)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
    gmsh.option.setNumber("Mesh.MinimumElementsPerTwoPi", 12)

    gmsh.model.mesh.generate(3)

    # 4. EXTRAÇÃO EXCLUSIVA DE TETRAEDROS (Tipo 4)
    elemTypes, elemTags, elemNodeTags = gmsh.model.mesh.getElements(dim=3)
    idx_tetra = -1
    for i, etype in enumerate(elemTypes):
        if etype == 4:  # 4 = tetraedro
            idx_tetra = i
            break

    if idx_tetra == -1:
        print("ERRO: Não foram gerados tetraedros.")
        gmsh.finalize()
        return

    # Matriz bruta de tetraedros contendo as tags globais do Gmsh (1‑based)
    tetra_nodes_tags = np.array(elemNodeTags[idx_tetra]).reshape(-1, 4)

    # 5. RECONSTRUÇÃO DOS NÓS E ELEMENTOS COM ÍNDICES LOCAIS
    # Obtém a lista única de tags de nós usadas nos tetraedros
    tags_dos_tetraedros = np.unique(tetra_nodes_tags)

    coords_validas = []
    tag_para_novo_indice = {}

    print("A extrair coordenadas limpas para os nós dos tetraedros...")
    for novo_idx, tag in enumerate(tags_dos_tetraedros):
        coord, _, _, _ = gmsh.model.mesh.getNode(tag)
        coords_validas.append(coord)
        tag_para_novo_indice[tag] = novo_idx

    coords_validas = np.array(coords_validas)

    # Mapeia os tetraedros para os novos índices (0‑based)
    elementos = []
    for elem_tags in tetra_nodes_tags:
        idx0 = tag_para_novo_indice[elem_tags[0]]
        idx1 = tag_para_novo_indice[elem_tags[1]]
        idx2 = tag_para_novo_indice[elem_tags[2]]
        idx3 = tag_para_novo_indice[elem_tags[3]]
        elementos.append([idx0, idx1, idx2, idx3])

    # 6. ATRIBUIÇÃO DE CONDIÇÕES DE FRONTEIRA E GRAVAÇÃO
    print("A gravar os ficheiros prontos para simulação...")
    # Cria a pasta de saída (e a subpasta 'ficheiros' se necessário)
    os.makedirs(pasta, exist_ok=True)
    pasta_ficheiros = os.path.join(pasta, "ficheiros")
    os.makedirs(pasta_ficheiros, exist_ok=True)

    tol_bordo = 1e-4      # Tolerância para detectar faces da caixa
    tol_cilindro = 1e-3   # Tolerância para detectar superfície da vara

    # Grava pontos.txt: cada linha com "x y z potencial"
    with open(os.path.join(pasta_ficheiros, "pontos.txt"), "w") as f_nos:
        for coord in coords_validas:
            x, y, z = coord
            potencial = -1.0  # Valor por omissão (será ignorado)

            # Verifica se o nó está numa face exterior da terra
            is_bordo_x = (abs(x + L_terra / 2) < tol_bordo) or (abs(x - L_terra / 2) < tol_bordo)
            is_bordo_y = (abs(y + L_terra / 2) < tol_bordo) or (abs(y - L_terra / 2) < tol_bordo)
            is_fundo = abs(z + prof_terra) < tol_bordo

            # Verifica se o nó está na superfície da vara
            is_vara = False
            if z >= -comp_vara - tol_cilindro and z <= 0 + tol_cilindro:
                if num_varas == 1:
                    raio_n = np.sqrt(x ** 2 + y ** 2)
                    if raio_n <= raio + tol_cilindro:
                        is_vara = True
                else:
                    raio_n1 = np.sqrt((x + dist_varas / 2) ** 2 + y ** 2)
                    raio_n2 = np.sqrt((x - dist_varas / 2) ** 2 + y ** 2)
                    if raio_n1 <= raio + tol_cilindro or raio_n2 <= raio + tol_cilindro:
                        is_vara = True

            # Atribui o potencial conforme o tipo de nó
            if is_vara:
                potencial = V_vara
            elif is_bordo_x or is_bordo_y or is_fundo:
                potencial = 0.0

            f_nos.write(f"{x:.6f} {y:.6f} {z:.6f} {potencial:.1f}\n")

    # Grava elementos.txt: cada linha com "n0 n1 n2 n3 resistividade"
    with open(os.path.join(pasta_ficheiros, "elementos.txt"), "w") as f_elem:
        for el in elementos:
            f_elem.write(f"{el[0]} {el[1]} {el[2]} {el[3]} {Resistividade_Terra:.6f}\n")

    # Finaliza o Gmsh
    gmsh.finalize()

    # Estatísticas finais
    usados = np.unique(np.array(elementos))
    print(f"Nós escritos: {len(coords_validas)}")
    print(f"Nós usados nos elementos: {len(usados)}")
    print(f"Maior índice: {usados.max()}")
    print(f"Menor índice: {usados.min()}")

    print("\n" + "=" * 50)
    print("FICHEIROS GERADOS.")
    print(f"Total de Nós no pontos.txt: {len(coords_validas)}")
    print(f"Total de Elementos no elementos.txt: {len(elementos)}")
    print("=" * 50)

# Execução apenas se o script for chamado directamente

if __name__ == "__main__":
    gerar_malha_avancada(".")