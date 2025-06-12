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

# Carrega o arquivo CSV com separador correto
df = pd.read_csv('pix_recebidos_04_06_a_11_06.csv', sep=';')

# Selecionar e renomear apenas as colunas necessárias
df = df[['origemDestinatario', 'dataEHora', 'chavesPix', 'idOperacao', 'valor', 'lancamento']].copy()
df.columns = ['nome_remetente', 'data_pagamento', 'chave_pix', 'idOperacao', 'valor', 'observacoes']

# As datas já estão no formato YYYY-MM-DD, apenas garantir que seja string
df['data_pagamento'] = df['data_pagamento'].astype(str)

# Preencher valores nulos na coluna chave_pix com string vazia
df['chave_pix'] = df['chave_pix'].fillna('').astype(str)

# Adicionar colunas adicionais com valores padrão
df['status'] = 'novo'
df['id_responsavel'] = None
df['id_aluno'] = None
df['tipo_pagamento'] = None
df['parcelas_identificadas'] = None

# Limitar observacoes a 5000 caracteres
df['observacoes'] = df['observacoes'].astype(str).str[:5000]

print(f"📊 Processando {len(df)} registros do CSV...")

# ✅ VERIFICAÇÃO DE DUPLICATAS
print("🔍 Verificando registros já existentes na base de dados...")

# Buscar todos os IDs existentes na tabela extrato_pix
try:
    registros_existentes = supabase.table('extrato_pix').select('id').execute()
    ids_existentes = {registro['id'] for registro in registros_existentes.data}
    print(f"📋 Encontrados {len(ids_existentes)} registros existentes na base")
except Exception as e:
    print(f"⚠️ Erro ao verificar registros existentes: {e}")
    ids_existentes = set()

# Contadores
inseridos = 0
duplicatas = 0
erros = 0

# Inserir dados no Supabase com verificação de duplicatas
for index, row in df.iterrows():
    id_operacao = row['idOperacao']
    
    # ✅ Verificar se já existe
    if id_operacao in ids_existentes:
        duplicatas += 1
        if duplicatas <= 5:  # Mostrar apenas os primeiros 5
            print(f"⚠️ Duplicata ignorada: {row['nome_remetente']} - ID: {id_operacao}")
        elif duplicatas == 6:
            print(f"... (mais {len(df) - index - 1} duplicatas serão ignoradas silenciosamente)")
        continue
    
    data = {
        'id': id_operacao,  # Usar idOperacao como id
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
    
    try:
        resultado = supabase.table('extrato_pix').insert(data).execute()
        inseridos += 1
        if inseridos <= 50:  # Mostrar apenas os primeiros 5
            print(f"✅ Inserido: {row['nome_remetente']} - {row['data_pagamento']} - R${row['valor']}")
        elif inseridos == 51:
            print("... (continuando inserções em segundo plano)")
        
        # Adicionar à lista de existentes para próximas verificações
        ids_existentes.add(id_operacao)
        
    except Exception as e:
        erros += 1
        if erros <= 30:  # Mostrar apenas os primeiros 3 erros
            print(f"❌ Erro ao inserir registro {index + 1} (ID: {id_operacao}): {e}")

# 📊 RELATÓRIO FINAL
print("\n" + "="*60)
print("📊 RELATÓRIO FINAL DE INSERÇÃO")
print("="*60)
print(f"📁 Registros no CSV: {len(df)}")
print(f"✅ Registros inseridos: {inseridos}")
print(f"⚠️ Duplicatas ignoradas: {duplicatas}")
print(f"❌ Erros encontrados: {erros}")
print(f"📋 Total na base após inserção: {len(ids_existentes)}")

if duplicatas > 0:
    print(f"\n💡 IMPORTANTE: {duplicatas} registros já existiam na base de dados")
    print("   (baseado no campo idOperacao). Isso é normal e esperado!")

if erros > 0:
    print(f"\n⚠️ ATENÇÃO: {erros} registros apresentaram erros durante a inserção")
    print("   Verifique os detalhes acima para mais informações")

print("\n🎉 Processamento concluído!") 