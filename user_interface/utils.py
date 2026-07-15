"""
Funções utilitárias auxiliares para formatação e manipulação de ficheiros.
"""
import numpy as np

def formatar(valor: float | None, unidade: str) -> str:
    """
    Formata um valor numérico utilizando prefixos do Sistema Internacional (SI).

    :param valor: Valor numérico em vírgula flutuante a formatar.
    :param unidade: String representando a unidade base (ex: "ohm", "A", "V").
    :return: String formatada com o valor (4 algarismos significativos) e o prefixo (ex: "1.5 kA").
    """
    if valor is None or not np.isfinite(valor):
        return "--"
    for limite, prefixo in ((1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""), (1e-3, "m")):
        if abs(valor) >= limite:
            return f"{valor / limite:.4g} {prefixo}{unidade}"
    return f"{valor:.4g} {unidade}"

def garantir_extensao(caminho: str, extensao: str) -> str:
    """
    Garante que o caminho de um ficheiro termina com a extensão correta.

    :param caminho: Caminho original fornecido pelo utilizador.
    :param extensao: Extensão desejada (ex: ".txt", ".csv").
    :return: Caminho corrigido com a extensão incluída.
    """
    return caminho if caminho.lower().endswith(extensao) else caminho + extensao

def detalhes_formato(formato: str) -> tuple[str, str, str]:
    """
    Retorna os parâmetros de exportação apropriados consoante o formato escolhido.

    :param formato: Tipo de ficheiro desejado ("csv", "txt" ou "tsv").
    :return: Um tuplo contendo (extensao_ficheiro, filtro_janela_dialogo, delimitador_colunas).
    """
    formatos = {
        "csv": (".csv", "CSV (*.csv)", ","),
        "txt": (".txt", "Texto tabulado (*.txt)", "\t"),
        "tsv": (".tsv", "TSV (*.tsv)", "\t"),
    }
    return formatos[formato]