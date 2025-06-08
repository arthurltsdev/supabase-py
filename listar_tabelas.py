import os
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

# Carrega as variáveis do .env
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Tabelas de interesse
TABELAS_DESEJADAS = {
    "alunos",
    "alunos_responsaveis",
    "responsaveis",
    "turmas",
    "mensalidades",
    "pagamentos",
    "pagamentos_itens", 
    "extrato_pix"
}

def match_tabela_fk(nome_coluna, tabelas):
    """Tenta encontrar a tabela de destino para a coluna FK, considerando singular/plural."""
    if not nome_coluna.startswith("id_"):
        return None
    sufixo = nome_coluna[3:]
    for t in tabelas:
        if sufixo == t:
            return t
        if sufixo + "s" == t:
            return t
        if sufixo.endswith("s") and sufixo[:-1] == t:
            return t
        # Também aceita se o nome da tabela for o plural do sufixo
        if t.endswith("s") and t[:-1] == sufixo:
            return t
    return None

# Chama a função RPC criada no Supabase
resp = supabase.rpc("get_table_metadata").execute()

# Organiza e exibe os metadados
tabelas = defaultdict(list)
for row in resp.data:
    if row['table_name'] not in TABELAS_DESEJADAS:
        continue
    tabelas[row['table_name']].append({
        'coluna': row['column_name'],
        'tipo': row['data_type'],
        'nullable': row['is_nullable'],
        'pk': row['is_pk'],
        'fk': row['is_fk'],
    })

# Heurística para identificar relacionamentos FK
relacionamentos = []
for tabela, colunas in tabelas.items():
    for col in colunas:
        if col['fk']:
            ref_table = match_tabela_fk(col['coluna'], TABELAS_DESEJADAS)
            if ref_table:
                # Assume que a PK da tabela de destino é 'id' ou a primeira PK encontrada
                pk_col = next((c['coluna'] for c in tabelas[ref_table] if c['pk']), 'id')
                relacionamentos.append({
                    'tabela_origem': tabela,
                    'coluna_origem': col['coluna'],
                    'tabela_destino': ref_table,
                    'coluna_destino': pk_col,
                    'papel': f"Cada registro em '{tabela}' está relacionado a um registro em '{ref_table}' através da coluna '{col['coluna']}' (referencia '{ref_table}.{pk_col}')."
                })

for tabela, colunas in tabelas.items():
    print(f"Tabela: {tabela}")
    for col in colunas:
        extras = []
        if col['pk']:
            extras.append("PK")
        if col['fk']:
            extras.append("FK")
        extras_str = f" ({', '.join(extras)})" if extras else ""
        print(f"  - {col['coluna']} [{col['tipo']}] {extras_str}")
    print()

print("Relacionamentos encontrados:")
if not relacionamentos:
    print("Nenhum relacionamento identificado.")
else:
    for rel in relacionamentos:
        print(f"{rel['tabela_origem']}.{rel['coluna_origem']} referencia {rel['tabela_destino']}.{rel['coluna_destino']}")
        print(f"  Papel: {rel['papel']}") 