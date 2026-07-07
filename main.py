"""
main.py
=======
Script principal de orquestração do Metodo dos Elementos Finitos (MEF).

Este script coordena o fluxo de trabalho completo da simulação:
1. Leitura dos dados de geometria e condições de contorno.
2. Montagem da matriz global de rigidez (condutividade).
3. Resolução do sistema linear para obter potenciais elétricos.
4. Cálculo da resistência equivalente e do campo elétrico.
"""
import os
import io_utils
import fem_solver
import visualization

def main():
    """
    Função principal que orquestra a execução do simulador MEF.
    Não requer parâmetros de entrada; assume a existência da pasta 'ficheiros'.
    """
    print("=====================================")
    print("      INICIO DO SIMULADOR MEF        ")
    print("=====================================\n")

    pasta = "ficheiros"
    ficheiro_pontos = os.path.join(pasta, "pontos.txt")
    ficheiro_elementos = os.path.join(pasta, "elementos.txt")

    # Verifica se os ficheiros obrigatórios existem antes de prosseguir
    for f in [ficheiro_pontos, ficheiro_elementos]:
        if f and not os.path.exists(f):
            print(f"[ERRO CRÍTICO] Ficheiro '{f}' não encontrado.")
            return

    # ---------------------------------------------------------
    # 1. Fase de Leitura de Dados (Input / Output)
    # ---------------------------------------------------------
    print("-> A ler geometria e propriedades dos materiais...")
    nos, condicoes = io_utils.ler_nos_e_condicoes(ficheiro_pontos)
    elementos, resistividades = io_utils.ler_elementos_finais(ficheiro_elementos)

    # O solver trabalha com condutividades (inverso da resistividade elétrica do solo/cobre)
    condutividades = 1.0 / resistividades

    print(f"   [SUCESSO] Malha carregada: {len(nos)} nós e {len(elementos)} tetraedros.")

    # ---------------------------------------------------------
    # 2. Fase de Resolução Matemática (Solver MEF)
    # ---------------------------------------------------------
    print("\n-> A montar a matriz global de rigidez (formato esparso CSR)...")
    Matriz_Rigidez_Global = fem_solver.montar_matriz_global(nos, elementos, condutividades)

    print("-> A aplicar condições de contorno e a calcular potenciais no solver...")
    potenciais, resistencia = fem_solver.aplicar_condicoes_eliminacao(Matriz_Rigidez_Global, condicoes)

    print("-> A derivar o campo elétrico (gradiente vetorial) por elemento...")
    gradientes = fem_solver.gradiente_por_elemento(nos, elementos, potenciais)

    # ---------------------------------------------------------
    # 3. Apresentação dos Resultados Numéricos
    # ---------------------------------------------------------
    print("\n" + "=" * 40)
    print("        RELATÓRIO DE CÁLCULO MEF     ")
    print("=" * 40)

    if resistencia is not None:
        print(f"Resistência Total Equivalente : {resistencia:.4f} Ohms")

        # Cálculo da Corrente Total Estimada (Lei de Ohm: I = V / R) assumindo max/min lidos
        v_max = max(condicoes.values())
        v_min = min(condicoes.values())
        corrente = (v_max - v_min) / resistencia
        print(f"Corrente Total Estimada       : {corrente:.4f} A")

    print("-" * 40)
    print("Amostra de Potenciais (Nós Livres):")
    # Imprime apenas os primeiros 5 nós livres para manter a consola limpa e legível
    contador_amostra = 0
    for i, pot in enumerate(potenciais):
        if i not in condicoes:
            print(f"  Nó {i}: {pot:.4f} V")
            contador_amostra += 1
            if contador_amostra >= 5:
                print("  ... (restantes nós omitidos)")
                break

    # A invocação final da visualização 3D será colocada no próximo passo
    print("\n-> A aguardar a integração do motor de visualização 3D...")

if __name__ == "__main__":
    main()