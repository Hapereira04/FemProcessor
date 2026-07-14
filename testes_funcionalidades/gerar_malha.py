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

    print("A iniciar o motor Gmsh...")
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("Malha_Vara_Terra")


if __name__ == "__main__":
    gerar_malha_avancada(".")