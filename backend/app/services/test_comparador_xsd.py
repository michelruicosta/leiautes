# -*- coding: utf-8 -*-
"""O comparador de XSD precisa ver receita do tipo (CNPJ) e cabeçalho, não só o nome do campo."""
from __future__ import annotations

from pathlib import Path

from backend.app.services.comparador_arquivos import comparar_arquivos

NS = 'xmlns:xs="http://www.w3.org/2001/XMLSchema"'

V3 = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- +  Leiautes por data-base:  03/2019 e seguintes                      + -->
<!-- +  Atualizado em 23/02/2021                                          + -->
<xs:schema {NS}>
  <xs:attribute name="cnpj" type="tipoCNPJ"/>
  <xs:simpleType name="tipoCNPJ">
    <xs:restriction base="xs:string">
      <xs:pattern value="[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]"/>
      <xs:minLength value="8"/>
      <xs:maxLength value="8"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>
"""

V5 = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- +  Leiautes por data-base:  02/2026 e seguintes                      + -->
<!-- +  Atualizado em 12/02/2026                                          + -->
<xs:schema {NS}>
  <xs:attribute name="cnpj" type="tipoCNPJ"/>
  <xs:simpleType name="tipoCNPJ">
    <xs:restriction base="xs:string">
      <xs:pattern value="[a-zA-Z0-9]{{8}}"/>
      <xs:minLength value="8"/>
      <xs:maxLength value="8"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:element name="detalhamentosCosif" type="tipoDetalhamentosCosif"/>
</xs:schema>
"""


def _gravar(tmp: Path, nome: str, texto: str) -> str:
    p = tmp / nome
    p.write_text(texto, encoding="utf-8")
    return str(p)


def test_xsd_lista_cnpj_e_data_base(tmp_path: Path | None = None):
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as d:
        pasta = Path(d)
        ant = _gravar(pasta, "v3.xsd", V3)
        novo = _gravar(pasta, "v5.xsd", V5)
        cmp = comparar_arquivos(
            caminho_anterior=ant,
            caminho_atual=novo,
            tipo_arquivo="xsd",
        )
        assert cmp is not None
        juntos = "\n".join(
            list(cmp["itens_incluidos"])
            + list(cmp["itens_removidos"])
            + list(cmp["itens_alterados"])
        )
        assert "tipoCNPJ" in juntos
        assert "[a-zA-Z0-9]{8}" in juntos
        assert "data-base" in juntos.lower()
        assert "02/2026" in juntos
        assert "detalhamentosCosif" in juntos
        assert len(cmp["itens_alterados"]) >= 2  # CNPJ + data-base (e talvez atualizado)


if __name__ == "__main__":
    test_xsd_lista_cnpj_e_data_base()
    print("ok")
