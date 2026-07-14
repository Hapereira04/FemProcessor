from cmath import nan

import gmsh
import numpy as np
import os


def gerar_malha_avancada(pasta="."):
    # 1. PARÂMETROS DA SIMULAÇÃO
    num_varas = 1
    diam_vara = 0.0218
    comp_vara = 3.0
    L_terra = 60.0
    prof_terra = 40.0
    V_vara = 1000000.0
    Condutividade_Terra = 0.001
    dist_varas = nan

    print("A iniciar o motor Gmsh...")
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("Malha_Vara_Terra")

    # 2. CONSTRUÇÃO DA GEOMETRIA
    terra = gmsh.model.occ.addBox(-L_terra / 2, -L_terra / 2, -prof_terra, L_terra, L_terra, prof_terra)

    varas = []
    raio = diam_vara / 2.0
    margem = 0.1

    if num_varas == 1:
        v1 = gmsh.model.occ.addCylinder(0, 0, margem, 0, 0, -comp_vara - margem, raio)
        varas.append((3, v1))
    else:
        v1 = gmsh.model.occ.addCylinder(-dist_varas / 2, 0, margem, 0, 0, -comp_vara - margem, raio)
        v2 = gmsh.model.occ.addCylinder(dist_varas / 2, 0, margem, 0, 0, -comp_vara - margem, raio)
        varas.append((3, v1))
        varas.append((3, v2))

    gmsh.model.occ.cut([(3, terra)], varas, removeObject=True, removeTool=True)
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()

    # 3. GERAÇÃO DA MALHA
    print("A gerar a malha de tetraedros...")
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", diam_vara)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 2.0)
    gmsh.option.setNumber("Mesh.CharacteristicLengthFromCurvature", 1)
    gmsh.option.setNumber("Mesh.MinimumElementsPerTwoPi", 12)

    gmsh.model.mesh.generate(3)

    # 4. EXTRAÇÃO EXCLUSIVA DE TETRAEDROS (Tipo 4)
    elemTypes, elemTags, elemNodeTags = gmsh.model.mesh.getElements(dim=3)
    idx_tetra = -1
    for i, etype in enumerate(elemTypes):
        if etype == 4:
            idx_tetra = i
            break

    if idx_tetra == -1:
        print("ERRO: Não foram gerados tetraedros.")
        gmsh.finalize()
        return

    # Matriz bruta de tetraedros contendo as Tags globais do Gmsh
    tetra_nodes_tags = np.array(elemNodeTags[idx_tetra]).reshape(-1, 4)


if __name__ == "__main__":
    gerar_malha_avancada(".")