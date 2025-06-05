import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# Configurações do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Carregar o arquivo CSV
csv_file_path = 'novos_pix_completos.csv'
df = pd.read_csv(csv_file_path, sep=';')

# Renomear colunas e ajustar tipos
df.rename(columns={
    'data_pagamento': 'data_pagamento',
    'chavesPix': 'chave_pix',
    'nome': 'nome_remetente',
    'valor': 'valor'
}, inplace=True)

# Converter data_pagamento para string no formato ISO 8601
df['data_pagamento'] = pd.to_datetime(df['data_pagamento'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')

# Substituir NaN por None para compatibilidade com JSON
df = df.where(pd.notnull(df), None)

# Garantir que chave_pix seja uma string válida
df['chave_pix'] = df['chave_pix'].fillna('')

# Adicionar colunas adicionais com valores padrão
df['status'] = 'novo'
df['id_responsavel'] = None
df['id_aluno'] = None
df['tipo_pagamento'] = None
df['parcelas_identificadas'] = None
df['observacoes'] = None

# Inserir dados no Supabase
for index, row in df.iterrows():
    data = {
        'nome_remetente': row['nome_remetente'],
        'data_pagamento': row['data_pagamento'],
        'chave_pix': row['chave_pix'],
        'valor': row['valor'],
        'status': row['status'],
        'id_responsavel': row['id_responsavel'],
        'id_aluno': row['id_aluno'],
        'tipo_pagamento': row['tipo_pagamento'],
        'parcelas_identificadas': row['parcelas_identificadas'],
        'observacoes': row['observacoes']
    }
    supabase.table('extrato_pix').insert(data).execute()

print("Dados inseridos com sucesso na tabela 'extrato_pix'.")