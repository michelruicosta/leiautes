# -*- coding: utf-8 -*-
"""O robô não cruza papéis diferentes (Modelo vs Contas, AMCC001 vs AMCC002)."""
from persistencia.arquivos_db import (
    _extensao_arquivo,
    _familia_nome_arquivo,
    _frase_arquivo_novo_comparado,
    _rotulo_comparado_com,
    _versao_no_nome,
    escolher_nome_versao_parente,
)

# Inventário de produção (26/08/2026) — só os nomes que o teste precisa.
DLO_PLANILHAS = [
    "2061-202508-v3-vi3-Modelo documento (contas).xlsx",
    "2061-202509-v3-vi3-Modelo documento (contas).xlsx",
    "2061-202607-v1-vi1-Modelo documento (contas).xlsx",
    "2061-202607-v2-vi2-Modelo documento (contas).xlsx",
    "2061-202508-v2-vi4-Leiaute do DLO.xlsx",
    "2061-202509-v2-vi2-Leiaute do DLO.xlsx",
    "2061-202607-v1-vi1-Leiaute do DLO.xlsx",
    "2061-202510-v1-Planilha de configuração.xlsx",
    "2061-202601-v3-Planilha de configuração.xlsx",
    "2061-202607-v2-Planilha de configuração.xlsx",
    "2061-202407-v1-Críticas de pós processamento.xlsx",
    "2061-202411-v3-Críticas de pós processamento.xlsx",
    "Críticas de Pós-Processamento DLO_2061_V5 Ajustada.xlsx",
]

DLI_XSD = ["2062_v2.xsd", "2062_v3.xsd"]
MCC_XSD = ["AMCC001.xsd", "AMCC002.xsd", "AMCCComum.xsd"]
DRL_PLANILHAS = [
    "DRL_2160_leiaute_v201801.xlsx",
    "DRL_2160_leiaute_v202607.xlsx",
    "DRL_2160_Relacao_de_contas_v201801.xlsx",
    "DRL_2160_Modelo_de_calculo_v201801.xlsx",
    "DRL_2160_II_leiaute_v201701.xlsx",
]


def test_dli_v5_nao_e_mesma_familia_que_v3():
    novo = "Esquema de validação XSD v5.xsd"
    antigo = "2062_v3.xsd"
    assert _familia_nome_arquivo(novo) != _familia_nome_arquivo(antigo)
    assert _extensao_arquivo(novo) == _extensao_arquivo(antigo) == ".xsd"
    assert _versao_no_nome(novo) == 5
    assert _versao_no_nome(antigo) == 3
    assert _versao_no_nome("2062_v2.xsd") == 2


def test_dli_xsd_v5_compara_com_v3_nao_com_v2():
    escolhido = escolher_nome_versao_parente(
        "Esquema de validação XSD v5.xsd",
        DLI_XSD,
    )
    assert escolhido == "2062_v3.xsd"


def test_dlo_nao_compara_modelo_com_contas():
    assert escolher_nome_versao_parente("DLO_Modelo.XLS", ["DLO_Contas.XLS"]) is None
    assert escolher_nome_versao_parente("DLO_Contas.XLS", ["DLO_Modelo.XLS"]) is None


def test_dlo_modelo_nao_cruza_leiaute_nem_criticas():
    novo = "2061-202608-v1-Modelo documento (contas).xlsx"
    escolhido = escolher_nome_versao_parente(novo, DLO_PLANILHAS)
    assert escolhido == "2061-202607-v2-vi2-Modelo documento (contas).xlsx"


def test_dlo_criticas_v5_compara_com_a_mais_recente_do_papel():
    """Michel 26/08: V5 Ajustada é o mesmo papel das críticas."""
    escolhido = escolher_nome_versao_parente(
        "Críticas de Pós-Processamento DLO_2061_V5 Ajustada.xlsx",
        [n for n in DLO_PLANILHAS if "V5 Ajustada" not in n],
    )
    assert escolhido == "2061-202411-v3-Críticas de pós processamento.xlsx"


def test_mesmo_mes_escolhe_versao_mais_alta():
    """Dois arquivos no mesmo mês (202607): usa v2, não v1."""
    escolhido = escolher_nome_versao_parente(
        "2061-202608-v1-Modelo documento (contas).xlsx",
        [
            "2061-202607-v1-vi1-Modelo documento (contas).xlsx",
            "2061-202607-v2-vi2-Modelo documento (contas).xlsx",
        ],
    )
    assert escolhido == "2061-202607-v2-vi2-Modelo documento (contas).xlsx"


def test_mesmo_mes_mesma_v_escolhe_vi_mais_alta():
    escolhido = escolher_nome_versao_parente(
        "2061-202608-v8-vi10 - Instruções de Preenchimento.pdf",
        [
            "2061-202607-v8-vi8 - Instruções de Preenchimento.pdf",
            "2061-202607-v8-vi9 - Instruções de Preenchimento.pdf",
        ],
    )
    assert escolhido == "2061-202607-v8-vi9 - Instruções de Preenchimento.pdf"


def test_drm_instrucoes_v11_compara_com_v9():
    escolhido = escolher_nome_versao_parente(
        "InstrucoesPreenchimentoDRM_v11_Jan25.pdf",
        [
            "InstrucoesPreenchimentoDRM_v9.pdf",
            "InstrucoesPreenchimentoDRM_v10_Abril2021.pdf",
            "Lista_de_Erros_DRM.pdf",
        ],
    )
    assert escolhido == "InstrucoesPreenchimentoDRM_v10_Abril2021.pdf"


def test_drm_criticas_v5_mesmo_papel():
    escolhido = escolher_nome_versao_parente(
        "Criticas_Pos_Processamento_2060_V5_Jul26.pdf",
        ["Criticas_Pos_Processamento_2060.pdf", "Lista_de_Erros_DRM.pdf"],
    )
    assert escolhido == "Criticas_Pos_Processamento_2060.pdf"


def test_ddr_e_scd_instrucoes_nome_mudou():
    assert escolher_nome_versao_parente(
        "2011-202407-v7-vi7-Instruções de Preenchimento.pdf",
        ["Instruções de Preenchimento  2011 - versão publicação V3.01032021.pdf"],
    ) == "Instruções de Preenchimento  2011 - versão publicação V3.01032021.pdf"
    assert escolher_nome_versao_parente(
        "Leiaute_DDR_2011_Versao_Publicacao.v5 01072023.xls",
        ["Leiaute DDR - 2011 Versão Publicação.xls"],
    ) == "Leiaute DDR - 2011 Versão Publicação.xls"
    assert escolher_nome_versao_parente(
        "saldosDiariosInstrucoesPreenchimentoV2.pdf",
        ["Documento de Saldos Contábeis Diários - Instruções de Preenchimento.pdf"],
    ) == "Documento de Saldos Contábeis Diários - Instruções de Preenchimento.pdf"


def test_mcc_nao_cruza_os_tres_xsd():
    assert escolher_nome_versao_parente("AMCC001.xsd", ["AMCC002.xsd", "AMCCComum.xsd"]) is None
    assert escolher_nome_versao_parente("AMCC002.xsd", MCC_XSD) is None
    assert escolher_nome_versao_parente("AMCCComum.xsd", MCC_XSD) is None
    novo = "EsquemaNovoQualquer.xsd"
    assert escolher_nome_versao_parente(novo, MCC_XSD) is None


def test_planilha_unica_nao_cruza_por_extensao():
    """XLS/XLSX/PDF não usam a folga do XSD — evita Modelo vs Contas."""
    assert escolher_nome_versao_parente(
        "Leiaute-DRSAC-novo-nome.xlsx",
        ["Leiaute-DRSAC.xlsx"],
    ) is None
    assert escolher_nome_versao_parente(
        "Instrucoes-DRSAC-v2.pdf",
        ["Instrucoes-de-Preenchimento-DRSAC.pdf"],
    ) is None


def test_xsd_unico_do_cadastro_aceita_nome_novo():
    escolhido = escolher_nome_versao_parente(
        "Esquema de validação XSD v5.xsd",
        ["DDR_2011_XSD_V01072020.xsd"],
    )
    assert escolhido == "DDR_2011_XSD_V01072020.xsd"


def test_mesmo_papel_xsd_dlo_v10_com_v11():
    escolhido = escolher_nome_versao_parente(
        "2061_v11.xsd",
        ["2061_v9.xsd", "2061_v10.xsd"],
    )
    assert escolhido == "2061_v10.xsd"


def test_drl_leiaute_nao_cruza_com_contas():
    escolhido = escolher_nome_versao_parente(
        "DRL_2160_leiaute_v202701.xlsx",
        DRL_PLANILHAS,
    )
    assert escolhido == "DRL_2160_leiaute_v202607.xlsx"


def test_aviso_explicito_quando_nome_muda():
    texto = _frase_arquivo_novo_comparado(
        "Esquema de validação XSD v5.xsd",
        "2062_v3.xsd",
    )
    assert "nome no site mudou" in texto.lower()
    assert "2062_v3.xsd" in texto
    rotulo = _rotulo_comparado_com("2062_v3.xsd", nome_atual="Esquema de validação XSD v5.xsd")
    assert rotulo.startswith("[Comparado com a versão anterior")
    assert "antes: 2062_v3.xsd" in rotulo
    assert "nome no site mudou" in rotulo


def test_aviso_sem_nome_mudou_quando_e_a_mesma_serie():
    texto = _frase_arquivo_novo_comparado("2061_v11.xsd", "2061_v10.xsd")
    assert "nome no site mudou" not in texto.lower()
    assert "2061_v10.xsd" in texto


def test_dli_modelo_contas_nao_cruza_com_leiaute():
    dli = [
        "2062-202505-v1-Leiaute do DLi.xlsx",
        "2062-202607-v2-vi3-Leiaute do DLi.xlsx",
        "2062-202505-v1-Modelo documento (contas).xlsx",
        "2062-202607-v1-vi1-Modelo documento (contas).xlsx",
        "2062-202505-v1-Planilha de configuração.xlsx",
    ]
    escolhido = escolher_nome_versao_parente(
        "2062-202608-v1-Modelo documento (contas).xlsx",
        dli,
    )
    assert escolhido is not None
    assert "Modelo documento (contas)" in escolhido
    assert "Leiaute" not in escolhido


if __name__ == "__main__":
    test_dli_v5_nao_e_mesma_familia_que_v3()
    test_dli_xsd_v5_compara_com_v3_nao_com_v2()
    test_dlo_nao_compara_modelo_com_contas()
    test_dlo_modelo_nao_cruza_leiaute_nem_criticas()
    test_dlo_criticas_v5_compara_com_a_mais_recente_do_papel()
    test_mesmo_mes_escolhe_versao_mais_alta()
    test_mesmo_mes_mesma_v_escolhe_vi_mais_alta()
    test_drm_instrucoes_v11_compara_com_v9()
    test_drm_criticas_v5_mesmo_papel()
    test_ddr_e_scd_instrucoes_nome_mudou()
    test_mcc_nao_cruza_os_tres_xsd()
    test_planilha_unica_nao_cruza_por_extensao()
    test_xsd_unico_do_cadastro_aceita_nome_novo()
    test_mesmo_papel_xsd_dlo_v10_com_v11()
    test_drl_leiaute_nao_cruza_com_contas()
    test_aviso_explicito_quando_nome_muda()
    test_aviso_sem_nome_mudou_quando_e_a_mesma_serie()
    test_dli_modelo_contas_nao_cruza_com_leiaute()
    print("ok")
