"""
visualization.py
================
Módulo dedicado à renderização 3D e pós-processamento visual dos resultados MEF.

Este módulo utiliza a biblioteca PyVista para transformar os dados numéricos
(nós, elementos e potenciais) em representações gráficas interativas,
permitindo a análise de cortes transversais e a visualização do campo elétrico.
"""
import pyvista as pv
import numpy as np


def preparar_malha_vtk(nos, elementos):
    """
    Converte a malha do Python (nós e elementos) para o formato UnstructuredGrid do VTK.

    :param nos: Array NumPy (N x 3) com as coordenadas (x, y, z) dos nós.
    :param elementos: Array NumPy (M x 4) com os índices dos 4 nós de cada tetraedro.
    :return: Objeto pv.UnstructuredGrid formatado para renderização 3D.
    """
    M = len(elementos)

    # PyVista exige que os arrays comecem com o número de nós da célula (4 para tetraedros)
    celulas_vtk = np.empty((M, 5), dtype=int)
    celulas_vtk[:, 0] = 4
    celulas_vtk[:, 1:] = elementos
    celulas_vtk = celulas_vtk.flatten()

    # O código VTK universal para 'Linear Tetrahedron' é 10
    tipos_celulas = np.full(M, 10, dtype=np.uint8)

    return pv.UnstructuredGrid(celulas_vtk, tipos_celulas, nos)


def visualizar_resultados_3d(nos, elementos, potenciais):
    """
    Gera uma janela 3D interativa com um mapa de cores (heatmap) dos potenciais.
    """
    malha = preparar_malha_vtk(nos, elementos)

    # Injetar os valores matemáticos nos nós da malha gráfica
    malha.point_data["Potencial (V)"] = potenciais

    plotter = pv.Plotter(title="Visualização MEF 3D")
    plotter.add_mesh(malha, show_edges=True, scalars="Potencial (V)", cmap="jet", lighting=True)
    plotter.add_axes()
    plotter.add_bounding_box(color='gray')

    plotter.show()


def visualizar_corte_interativo(nos, elementos, potenciais, gradientes, condicoes):
    """
    Gera uma interface gráfica avançada com um plano de corte dinâmico.
    """
    pass