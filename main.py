"""
main.py
=======
Script principal de orquestração do Metodo dos Elementos Finitos (MEF).

Este script coordena o fluxo de trabalho completo da simulação:
1. Leitura dos dados de geometria e condições de contorno.
2. Montagem da matriz global de rigidez (condutividade).
3. Resolução do sistema linear para obter potenciais elétricos.
4. Cálculo da resistência equivalente e do campo elétrico.
5. Visualização 3D interativa dos resultados.
"""
import os

import io_utils
import fem_solver
import visualization
import sys
from user_interface import iniciar_interface


def main():
    """
    Função principal que orquestra a execução do simulador MEF.
    Não requer parâmetros de entrada; assume a existência da pasta 'ficheiros'.
    """
    pasta = "ficheiros"
    ficheiro_pontos = os.path.join(pasta, "pontos.txt")
    ficheiro_elementos = os.path.join(pasta, "elementos.txt")

    for f in [ficheiro_pontos, ficheiro_elementos]:
        if f and not os.path.exists(f):
            print(f"Erro crítico: Ficheiro '{f}' não encontrado.")
            return

    # 1. Leitura (Delega para io_utils)
    print("A ler geometria e materiais...")
    nos, condicoes = io_utils.ler_nos_e_condicoes(ficheiro_pontos)
    elementos, condutividades = io_utils.ler_elementos_finais(ficheiro_elementos)

    # NOVO: Repara a malha estragada do Gmsh colando a vara ao solo!
    nos, elementos, condicoes = io_utils.reparar_malha_desconectada(nos, elementos, condicoes)

    # 2. Resolução Matemática (Delega para fem_solver)
    print("A montar matriz global de rigidez...")
    S = fem_solver.montar_matriz_global(nos, elementos, condutividades)

    print("A calcular campo elétrico e potenciais...")
    potenciais, resistencia = fem_solver.aplicar_condicoes_eliminacao(S, condicoes)
    gradientes = fem_solver.gradiente_por_elemento(nos, elementos, potenciais)

    # 3. Impressão de Resultados
    print("\n" + "=" * 40)
    print("RELATÓRIO DE CÁLCULO MEF")
    print("=" * 40)

    if resistencia is not None:
        print(f"Resistência Total Equivalente : {resistencia:.2f} Ohms")

        # Opcional: Calcular a corrente (I = V / R) assumindo os valores max/min lidos
        v_max = max(condicoes.values())
        v_min = min(condicoes.values())
        corrente = (v_max - v_min) / resistencia
        print(f"Corrente Total Estimada     : {corrente:.4f} A")

    print("-" * 40)
    print("Amostra de Potenciais (Nós Livres):")
    for i, pot in enumerate(potenciais):
        if i not in condicoes:
            print(f"  Nó {i}: {pot:.2f} V")

    # 4. Renderização 3D (Delega para visualization)
    print("\nA inicializar motores gráficos...")
    visualization.visualizar_resultados_3d(nos, elementos, potenciais)
    visualization.visualizar_corte_interativo(nos, elementos, potenciais, gradientes, condicoes)

if __name__ == "__main__":
    sys.exit(iniciar_interface())
    main()