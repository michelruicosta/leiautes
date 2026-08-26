# -*- coding: utf-8 -*-
from persistencia.arquivos_db import (
    _extensao_arquivo,
    _familia_nome_arquivo,
    _versao_no_nome,
)


def test_dli_v5_nao_e_mesma_familia_que_v3():
    novo = "Esquema de validação XSD v5.xsd"
    antigo = "2062_v3.xsd"
    assert _familia_nome_arquivo(novo) != _familia_nome_arquivo(antigo)
    assert _extensao_arquivo(novo) == _extensao_arquivo(antigo) == ".xsd"
    assert _versao_no_nome(novo) == 5
    assert _versao_no_nome(antigo) == 3
    assert _versao_no_nome("2062_v2.xsd") == 2


def test_escolhe_v3_antes_de_v2_para_v5():
    v5 = 5
    candidatos = [
        (3, "2062_v3.xsd", 30),
        (2, "2062_v2.xsd", 20),
    ]
    melhores = []
    for v_ant, nome, vid in candidatos:
        chave = (0, v5 - v_ant, -vid) if v_ant < v5 else (2, v_ant, -vid)
        melhores.append((chave, nome))
    melhores.sort(key=lambda x: x[0])
    assert melhores[0][1] == "2062_v3.xsd"


if __name__ == "__main__":
    test_dli_v5_nao_e_mesma_familia_que_v3()
    test_escolhe_v3_antes_de_v2_para_v5()
    print("ok")
