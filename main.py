"""
main.py
=======
Script principal de orquestração do Metodo dos Elementos Finitos (MEF).

Este script coordena o fluxo de trabalho completo da simulação.
"""
import os
import io_utils
import fem_solver
import visualization


def main():
    """
    Função principal que orquestra a execução do simulador MEF.
    """
    print("=====================================")
    print("      INICIO DO SIMULADOR MEF        ")
    print("=====================================\n")

    pasta = "ficheiros"
    ficheiro_pontos = os.path.join(pasta, "pontos.txt")
    ficheiro_elementos = os.path.join(pasta, "elementos.txt")

    # 1. Leitura de Dados (Integração do módulo IO)
    print("-> A ler geometria e propriedades dos materiais...")

    if os.path.exists(ficheiro_pontos) and os.path.exists(ficheiro_elementos):
        nos, condicoes = io_utils.ler_nos_e_condicoes(ficheiro_pontos)
        elementos, resistividades = io_utils.ler_elementos_finais(ficheiro_elementos)

        print(f"[SUCESSO] Malha carregada:")
        print(f"  - Nós encontrados: {len(nos)}")
        print(f"  - Elementos tetraédricos: {len(elementos)}")
        print(f"  - Condições de fronteira (bateria): {len(condicoes)} pontos\n")

        # A preparação da matemática (fem_solver) será chamada aqui futuramente
        print("-> A aguardar a integração do motor matemático (fem_solver)...")

    else:
        print(f"[ERRO] Ficheiros não encontrados na diretoria '{pasta}/'.")
        print("Certifique-se que 'pontos.txt' e 'elementos.txt' existem.")


if __name__ == "__main__":
    main()