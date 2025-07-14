"""
create_extrato_pix.py – v2025-06-12 (sem coluna nome_norm)
Insere PIX no extrato_pix_novo com idOperacao como PK.
CSV: dataEHora,chavesPix,idOperacao,origemDestinatario,valor
"""

import os, unicodedata
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# ─── Config ────────────────────────────────────────────────
load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

CSV_PATH   = "C:/Users/arthu/OneDrive/Desktop/supabase-py/extratos_pix/recebimentos_unificados.csv"
TABLE_NAME = "extrato_pix"
BATCH      = 500          # lote de inserção

# ─── Helpers ───────────────────────────────────────────────
def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    txt = unicodedata.normalize("NFD", text)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return " ".join(t for t in txt.lower().split()
                    if t not in {"de", "da", "do", "dos", "das"})

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", dtype={"valor": "float"})
    
    # Primeiro, renomear as colunas
    df = df.rename(columns={
        "origemDestinatario": "nome_remetente",
        "dataEHora"        : "data_pagamento",
        "chavesPix"        : "chave_pix",
        "idOperacao"       : "id"
    })
    
    # Depois, aplicar as transformações
    df = df.assign(
        nome_remetente=lambda d: d["nome_remetente"].map(normalize),
        data_pagamento=lambda d: pd.to_datetime(
            d["data_pagamento"],
            format='%d/%m/%Y',
            errors='coerce'
        ).dt.date.astype(str),
        chave_pix      = lambda d: d["chave_pix"].fillna(""),
        status         = "novo",
        id_responsavel = None,
        id_aluno       = None,
        tipo_pagamento = None,
        parcelas_identificadas = None,
        observacoes    = ""
    )

    df["observacoes"] = df["observacoes"].astype(str).str[:5000]
    return df.drop_duplicates(subset="id")

def chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

# ─── Main ──────────────────────────────────────────────────
def main():
    df = load_csv(CSV_PATH)
    print(f"📊 CSV lido: {len(df)} linhas únicas")

    # evita duplicar se rodar novamente
    ids_exist = {r["id"] for r in sb.table(TABLE_NAME)
                                   .select("id").execute().data}
    df = df[~df["id"].isin(ids_exist)]
    print(f"➕ Novos registros a inserir: {len(df)}")

    inserted = errors = 0
    for lote in chunk(df.to_dict("records"), BATCH):
        try:
            sb.table(TABLE_NAME).upsert(lote, on_conflict="id").execute()
            inserted += len(lote)
        except Exception as e:
            errors += len(lote)
            print(f"❌ Falha em lote ({len(lote)}): {e}")

    print("\n" + "="*50)
    print(f"Total no CSV        : {len(df) + len(ids_exist)}")
    print(f"Já existiam na base : {len(ids_exist)}")
    print(f"Inseridos agora     : {inserted}")
    print(f"Erros               : {errors}")
    print("🎉  Importação concluída")

if __name__ == "__main__":
    main()
