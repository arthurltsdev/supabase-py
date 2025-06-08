# Sistema de Gestão Escolar - Supabase

Este sistema implementa funções para manipulação de dados de uma escola utilizando o Supabase como backend. O foco principal é o processamento automático de pagamentos PIX e gestão de alunos e responsáveis.

## 📁 Arquivos Principais

- **`supabase_functions.py`** - Contém todas as funções de manipulação do banco de dados
- **`exemplo_uso_supabase.py`** - Exemplos práticos de como usar as funções
- **`.env`** - Configurações de conexão com o Supabase

## 🎯 Funcionalidades Principais

### 1. Gestão do Extrato PIX
- **Identificar responsáveis não cadastrados** no extrato PIX
- **Cadastro automático** de responsáveis baseado no extrato
- **Vinculação automática** de pagamentos aos responsáveis
- **Estatísticas detalhadas** do extrato PIX
- **Remoção de registros** específicos do extrato

### 2. Gestão de Responsáveis
- **Cadastro completo** com CPF, telefone, email, endereço
- **Busca por nome** ou CPF
- **Atualização de dados** existentes
- **Listagem com filtros** personalizados

### 3. Gestão de Alunos
- **Cadastro completo** com turma, data de nascimento, vencimento
- **Busca por nome** ou turma
- **Atualização de dados** existentes
- **Filtros especiais** (sem dia de vencimento, sem data de matrícula, etc.)

### 4. Gestão de Pagamentos
- **Registro de pagamentos** com responsável e aluno
- **Listagem com filtros** por data, tipo, forma de pagamento
- **Vinculação com mensalidades**

### 5. Gestão de Relacionamentos
- **Vinculação aluno-responsável** com tipo de relação
- **Verificação de responsáveis financeiros**
- **Controle de permissões** financeiras

## 🗄️ Estrutura do Banco de Dados

### Tabelas Principais:

#### `alunos`
- `id` (PK) - Formato: ALU_XXXXXX
- `nome`
- `id_turma` (FK para turmas)
- `data_nascimento`
- `dia_vencimento`
- `valor_mensalidade`
- `data_matricula`
- `turno`

#### `responsaveis`
- `id` (PK) - Formato: RES_XXXXXX
- `nome`
- `cpf`
- `telefone`
- `email`
- `endereco`
- `tipo_relacao`
- `responsavel_financeiro`

#### `alunos_responsaveis`
- `id` (PK)
- `id_aluno` (FK)
- `id_responsavel` (FK)
- `responsavel_financeiro`
- `tipo_relacao`

#### `pagamentos`
- `id_pagamento` (PK) - Formato: PAG_XXXXXX
- `id_responsavel` (FK)
- `id_aluno` (FK)
- `data_pagamento`
- `valor`
- `tipo_pagamento`
- `forma_pagamento`
- `descricao`

#### `extrato_pix`
- `nome_remetente`
- `data_pagamento`
- `chave_pix`
- `valor`
- `status`
- `id_responsavel` (FK)
- `id_aluno` (FK)
- `observacoes`

## 🚀 Como Usar

### 1. Configuração Inicial

```python
# Instalar dependências
pip install supabase python-dotenv

# Configurar arquivo .env
SUPABASE_URL="sua_url_do_supabase"
SUPABASE_KEY="sua_chave_do_supabase"
```

### 2. Fluxo Principal - Processamento do Extrato PIX

```python
from supabase_functions import (
    identificar_responsaveis_nao_cadastrados,
    processar_responsaveis_extrato_pix,
    analisar_estatisticas_extrato
)

# 1. Analisar situação atual
stats = analisar_estatisticas_extrato()
print(f"Registros não identificados: {stats['estatisticas']['total_nao_identificados']}")

# 2. Identificar responsáveis não cadastrados
nao_cadastrados = identificar_responsaveis_nao_cadastrados()
print(f"Responsáveis para cadastrar: {nao_cadastrados['count']}")

# 3. Processar automaticamente
resultado = processar_responsaveis_extrato_pix()
print(f"Responsáveis cadastrados: {resultado['total_cadastrados']}")
```

### 3. Cadastro Manual

```python
from supabase_functions import (
    cadastrar_responsavel_completo,
    cadastrar_aluno,
    vincular_aluno_responsavel
)

# Cadastrar responsável
resp = cadastrar_responsavel_completo(
    nome="João Silva",
    cpf="123.456.789-00",
    telefone="(11) 99999-9999",
    email="joao@email.com"
)

# Cadastrar aluno
aluno = cadastrar_aluno(
    nome="Maria Silva",
    nome_turma="Infantil III",
    dia_vencimento=10,
    valor_mensalidade=350.00
)

# Vincular responsável ao aluno
vincular_aluno_responsavel(
    id_aluno=aluno['id_aluno'],
    id_responsavel=resp['id_responsavel'],
    responsavel_financeiro=True,
    tipo_relacao="pai"
)
```

### 4. Consultas e Relatórios

```python
from supabase_functions import (
    listar_alunos,
    listar_responsaveis,
    listar_pagamentos_nao_identificados
)

# Listar alunos por turma
alunos = listar_alunos(filtro_turma="Infantil III")

# Buscar responsáveis por nome
responsaveis = listar_responsaveis(filtro_nome="Silva")

# Ver pagamentos não identificados
nao_identificados = listar_pagamentos_nao_identificados(formato_resumido=True)
```

## 📊 Funções Disponíveis

### Funções de Identificação e Processamento
- `identificar_responsaveis_nao_cadastrados()` - Identifica quem não está cadastrado
- `processar_responsaveis_extrato_pix()` - Cadastra automaticamente os responsáveis
- `analisar_estatisticas_extrato()` - Gera relatório completo do extrato

### Funções de Cadastro
- `cadastrar_responsavel_completo()` - Cadastra novo responsável
- `cadastrar_aluno()` - Cadastra novo aluno
- `registrar_pagamento()` - Registra novo pagamento
- `vincular_aluno_responsavel()` - Cria vinculação entre aluno e responsável

### Funções de Consulta
- `listar_alunos()` - Lista alunos com filtros
- `listar_responsaveis()` - Lista responsáveis com filtros
- `listar_pagamentos()` - Lista pagamentos com filtros
- `listar_mensalidades()` - Lista mensalidades de um aluno
- `consultar_extrato_pix()` - Consulta extrato PIX
- `listar_pagamentos_nao_identificados()` - Lista pagamentos sem identificação

### Funções de Atualização
- `atualizar_dados_aluno()` - Atualiza dados de aluno existente
- `atualizar_dados_responsavel()` - Atualiza dados de responsável
- `atualizar_responsavel_extrato_pix()` - Vincula responsável ao extrato

### Funções de Busca
- `buscar_responsavel_por_nome()` - Busca responsável específico
- `buscar_aluno_por_nome()` - Busca aluno por nome
- `verificar_responsaveis_financeiros()` - Lista responsáveis financeiros de um aluno

### Funções Auxiliares
- `listar_turmas()` - Lista todas as turmas
- `remover_pagamentos_extrato()` - Remove registros do extrato
- `converter_data()` - Converte formatos de data
- `gerar_id_*()` - Gera IDs únicos para diferentes entidades

## 🔧 Utilitários

### Conversão de Datas
O sistema aceita datas nos formatos:
- `DD/MM/YYYY` (ex: 15/03/2024)
- `DD-MM-YYYY` (ex: 15-03-2024)
- `YYYY-MM-DD` (formato do banco)

### Geração de IDs
- Alunos: `ALU_XXXXXX`
- Responsáveis: `RES_XXXXXX`
- Pagamentos: `PAG_XXXXXX`
- Vínculos: `AR_XXXXXXXX`

## 🎯 Fluxo Recomendado de Uso

### Primeiro Uso:
1. Execute `analisar_estatisticas_extrato()` para ver a situação atual
2. Execute `processar_responsaveis_extrato_pix()` para cadastro automático
3. Verifique os resultados com novas estatísticas

### Uso Rotineiro:
1. Importe novos dados para `extrato_pix`
2. Execute o processamento automático
3. Revise casos que precisem de atenção manual
4. Registre pagamentos conforme necessário

### Manutenção:
1. Use as funções de atualização para corrigir dados
2. Use as funções de busca para investigar casos específicos
3. Use as funções de listagem para relatórios gerenciais

## 📝 Exemplos Práticos

Veja o arquivo `exemplo_uso_supabase.py` para exemplos completos de:
- Fluxo completo de processamento
- Cadastro manual passo a passo
- Diferentes tipos de consultas
- Busca específica por responsável

## ⚠️ Considerações Importantes

1. **Backup**: Sempre faça backup antes de executar processamentos em massa
2. **Testes**: Teste as funções com dados limitados primeiro
3. **Validação**: Verifique os resultados após cada operação
4. **Dependências**: Certifique-se de que as tabelas referenciadas existam
5. **Permissões**: Verifique se a chave do Supabase tem as permissões necessárias

## 🐛 Tratamento de Erros

Todas as funções retornam um dicionário com:
```python
{
    "success": True/False,
    "data": dados_retornados,  # se success=True
    "error": "mensagem_erro"   # se success=False
}
```

Sempre verifique o campo `success` antes de usar os dados retornados.

## 🚀 Próximos Passos

- Implementar interface web para as funções
- Adicionar logs detalhados das operações
- Criar relatórios em PDF
- Implementar notificações automáticas
- Adicionar validações mais robustas 