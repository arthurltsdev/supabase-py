# 🎓 Assistente Escolar IA - Supabase Edition

## 📋 Visão Geral

O Assistente Escolar IA é uma interface inteligente para gestão escolar que combina o poder da OpenAI GPT-4 com as funcionalidades do Supabase. Ele permite interagir com o banco de dados usando linguagem natural, além de oferecer comandos manuais para tarefas específicas.

## 🚀 Características Principais

### ✅ Funcionalidades Implementadas

- **🤖 Interface IA**: Interpreta comandos em linguagem natural
- **🔍 Identificação Automática**: Encontra responsáveis não cadastrados no extrato PIX  
- **👥 Gestão de Pessoas**: Lista e filtra alunos e responsáveis
- **📝 Cadastros Inteligentes**: Cadastra responsáveis e vincula relacionamentos
- **📊 Análises Financeiras**: Estatísticas completas do extrato PIX
- **🚀 Processamento em Massa**: Cadastra múltiplos responsáveis automaticamente
- **🎯 Interface Manual**: Menu de funções para uso sem IA

### 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **OpenAI GPT-4o** (Function Calling)
- **Supabase** (PostgreSQL)
- **dotenv** (Variáveis de ambiente)

## 📁 Estrutura dos Arquivos

```
supabase-py/
├── assistente_escolar_ia.py    # 🤖 Interface principal do assistente
├── functions.json              # 🔧 Definições das funções OpenAI
├── executor_unificado.py       # ⚡ Executor que mapeia IA → Supabase
├── supabase_functions.py       # 🔗 Funções do Supabase
├── .env                        # 🔑 Variáveis de ambiente
└── README_ASSISTENTE_IA.md     # 📖 Esta documentação
```

## ⚙️ Configuração e Instalação

### 1. 📦 Instalar Dependências

```bash
pip install openai supabase python-dotenv
```

### 2. 🔑 Configurar Variáveis de Ambiente

Adicione ao arquivo `.env`:

```env
# Supabase (obrigatório)
SUPABASE_URL="sua_url_do_supabase"
SUPABASE_KEY="sua_chave_do_supabase"

# OpenAI (opcional - para usar IA)
OPENAI_API_KEY="sua_chave_openai"
```

**Nota:** O sistema funciona sem OpenAI (modo manual), mas perde a capacidade de IA.

### 3. 🚀 Executar o Assistente

```bash
python assistente_escolar_ia.py
```

## 🎯 Como Usar

### 🤖 Comandos com IA (se configurado)

Use linguagem natural para interagir. **A IA mantém contexto entre comandos**, permitindo fluxos sequenciais:

```
"Liste responsáveis do extrato PIX não cadastrados"
"Cadastre Maria Santos com CPF 123.456.789-00 como mãe do aluno João Silva"
"Mostre alunos da turma Infantil III sem data de matrícula"
"Liste todos os registros em extrato_pix que estão cadastrados em responsaveis"
"Analise estatísticas do extrato PIX"
```

### 🔄 Fluxo Sequencial Inteligente

**Exemplo de conversa com contexto:**

1. **Usuário:** "Liste responsáveis não cadastrados"
   **IA:** [Lista 5 responsáveis não cadastrados]

2. **Usuário:** "cadastre Maria Santos com CPF 123.456.789-00 como mãe do aluno João Silva"
   **IA:** ✅ Executa cadastro + vinculação automaticamente

3. **Usuário:** "analise as estatísticas novamente"
   **IA:** 📊 Mostra estatísticas atualizadas após o cadastro

### 📋 Comandos Manuais

#### Comandos Rápidos:
- `menu` - Exibe menu de funções
- `identificar` - Lista responsáveis não cadastrados
- `estatisticas` - Analisa extrato PIX
- `responsaveis` - Lista responsáveis
- `alunos` - Lista alunos com filtros
- `turmas` - Mostra turmas disponíveis

#### Menu Numerado:
1. **Identificar responsáveis não cadastrados**
2. **Analisar estatísticas do extrato PIX**
3. **Listar pagamentos não identificados**
4. **Listar responsáveis** (com filtros)
5. **Listar alunos** (com filtros avançados)
6. **Listar turmas**
7. **Buscar aluno por nome**
8. **Cadastrar responsável**
9. **Vincular aluno a responsável**
10. **Processar responsáveis automaticamente**

### 🔍 Exemplos de Filtros Avançados

#### Filtros para Alunos (Opção 5):
- **Nome**: Busca parcial por nome
- **Turma**: Filtrar por turma específica
- **Sem matrícula**: Apenas alunos sem data de matrícula
- **Sem vencimento**: Alunos sem dia de vencimento
- **Sem valor**: Alunos sem valor de mensalidade

#### Filtros para Responsáveis (Opção 4):
- **Nome**: Busca parcial por nome
- **CPF**: Busca por CPF específico

## 📊 Principais Funcionalidades

### 🔍 1. Identificação de Responsáveis Não Cadastrados

**O que faz:**
- Compara nomes únicos do extrato PIX (nome_remetente) com nomes na tabela responsáveis
- **LÓGICA CORRETA**: Se nome_remetente existe no extrato mas NÃO existe em responsáveis = não cadastrado
- Lista responsáveis que aparecem no extrato mas não estão na base
- Mostra quantidade de pagamentos e valor total por responsável

**Como usar:**
```
# Com IA
"Liste responsáveis do extrato PIX não cadastrados"

# Manual
identificar
```

**📊 Exemplo de saída quando há não cadastrados:**
```
📊 **5 RESPONSÁVEIS NÃO CADASTRADOS ENCONTRADOS:**

 1. Maria Santos
    📄 3 pagamento(s) • 💰 R$ 450.00

 2. João Oliveira  
    📄 2 pagamento(s) • 💰 R$ 300.00
```

### 📊 2. Análise de Estatísticas

**O que faz:**
- Total de registros no extrato PIX
- Percentual de identificação
- Valores totais e não identificados
- Indicador visual de status

**Como usar:**
```
# Com IA
"Analise estatísticas do extrato PIX"

# Manual
estatisticas
```

### 🚀 3. Processamento Automático

**O que faz:**
- Cadastra automaticamente todos os responsáveis não identificados
- Vincula os registros do extrato aos novos responsáveis
- Atualiza as estatísticas de identificação

**Como usar:**
```
# Com IA  
"Processe automaticamente responsáveis não cadastrados"

# Manual
10 (no menu)
```

**⚠️ IMPORTANTE:** Esta operação modifica o banco de dados. Sempre confirme antes de executar.

### 👥 4. Gestão de Alunos e Responsáveis

**Filtros Disponíveis para Alunos:**
- Por turma (ex: "Infantil III", "1º Ano")
- Por nome (busca parcial)
- Sem data de matrícula
- Sem dia de vencimento
- Sem valor de mensalidade

**Exemplos:**
```
# Com IA
"Mostre alunos da turma Berçário sem data de matrícula"
"Liste alunos sem valor de mensalidade definido"

# Manual
alunos (seguir prompts de filtro)
```

### 📝 5. Cadastros e Vinculações

**🔄 Cadastro com Vinculação Automática (NOVO):**
```
"cadastre Maria Santos com CPF 123.456.789-00 como mãe do aluno João Silva"
```
**O que acontece automaticamente:**
1. 🔍 Busca aluno por nome
2. 📝 Cadastra responsável  
3. 🔗 Vincula automaticamente
4. ✅ Confirma operação

**Cadastrar Responsável (Manual):**
- Nome (obrigatório)
- CPF, telefone, email (opcionais)
- Tipo de relação (pai, mãe, avô, etc.)

**Vincular Relacionamentos:**
- ID do aluno
- ID do responsável  
- Tipo de relação
- Responsável financeiro (automático: sim)

### 🔍 6. Listar Registros Identificados (NOVO)

**O que faz:**
- Lista registros do extrato PIX cujos remetentes JÁ estão cadastrados como responsáveis
- Útil para registrar pagamentos na tabela pagamentos
- Ordena por data (mais recentes primeiro)

**Como usar:**
```
# Com IA
"Liste todos os registros em extrato_pix que estão cadastrados em responsaveis"

# Manual  
Função: listar_registros_extrato_com_responsaveis_cadastrados
```

## 🎨 Interface e Experiência

### 🌈 Recursos Visuais

- **Emojis informativos** para categorização
- **Cores em texto** para status e alertas
- **Formatação organizada** em tabelas e listas
- **Contadores e estatísticas** para acompanhamento

### 🔄 Fluxo de Trabalho Recomendado

1. **📊 Análise inicial:**
   ```
   estatisticas
   ```

2. **🔍 Identificação:**
   ```
   identificar
   ```

3. **📝 Processamento (se necessário):**
   ```
   10 → s (confirmar)
   ```

4. **✅ Verificação:**
   ```
   estatisticas
   ```

## 🚨 Avisos e Limitações

### ⚠️ Operações Destrutivas

**CUIDADO** com estas operações que modificam dados:
- Cadastrar responsável (opção 8)
- Vincular aluno-responsável (opção 9)  
- **Processar automaticamente (opção 10)**

Sempre confirme antes de executar!

### 🔧 Limitações Técnicas

- **Limite de exibição**: 20-25 registros por consulta (para performance)
- **Histórico de IA**: Máximo 15 mensagens (controle de contexto)
- **Dependência de rede**: Requer conexão com Supabase e OpenAI

### 🔑 Configurações Opcionais

- **OpenAI**: Sistema funciona sem IA (modo manual apenas)
- **Timeouts**: API pode ter limitações de tempo
- **Rate Limits**: OpenAI tem limites de requisições

## 🆘 Solução de Problemas

### ❌ Erros Comuns

1. **"OPENAI_API_KEY não encontrada"**
   - Adicione a chave no arquivo `.env`
   - Sistema ainda funciona em modo manual

2. **"Erro ao carregar functions.json"**
   - Verifique se o arquivo existe e está válido
   - Execute no diretório correto

3. **"Função não encontrada"**
   - Verifique se `supabase_functions.py` está no diretório
   - Confirme se todas as dependências estão instaladas

4. **"Erro de conexão Supabase"**
   - Verifique URL e KEY no `.env`
   - Confirme conectividade de rede

### 🔧 Debug e Logs

O sistema exibe logs detalhados:
- ✅ Operações bem-sucedidas
- ⚠️ Avisos e limitações
- ❌ Erros com descrição
- 🔄 Status de processamento

## 📈 Métricas e Acompanhamento

### 📊 KPIs Principais

- **Taxa de identificação** do extrato PIX
- **Quantidade de responsáveis** não cadastrados
- **Valor total** não identificado
- **Evolução** após processamento

### 🎯 Metas Sugeridas

- **Taxa de identificação > 80%**
- **Tempo de processamento < 2 minutos**
- **Zero responsáveis não identificados**

## 🔮 Próximas Funcionalidades

### 🚀 Planejadas

- **Relatórios PDF** automatizados
- **Notificações** de inconsistências
- **Dashboard web** complementar
- **Backup automático** de dados críticos
- **Integração** com outros sistemas

### 💡 Sugestões de Uso

- **Rotina semanal** de análise de extratos
- **Verificação mensal** de dados de alunos
- **Backup regular** antes de processamentos
- **Treinamento** de usuários no sistema

---

## 👥 Suporte

Para dúvidas, problemas ou sugestões:

1. **Verifique** esta documentação primeiro
2. **Teste** em modo manual se IA falhar
3. **Consulte** logs de erro para debugging
4. **Documente** problemas recorrentes

---

**🎓 Sistema desenvolvido para otimizar a gestão educacional com inteligência artificial e automação inteligente.** 