# 🚀 Guia de Instalação das Dependências

Este projeto utiliza **Poetry** para gerenciar dependências Python de forma eficiente e organizada.

## 📋 Dependências Principais

O projeto inclui as seguintes dependências principais:

### 🗃️ Backend e Banco de Dados
- **supabase**: Cliente Python para Supabase
- **postgrest**: Interface para PostgreSQL
- **realtime**: Comunicação em tempo real
- **gotrue**: Autenticação
- **storage3**: Armazenamento de arquivos
- **supafunc**: Funções serverless
- **httpx**: Cliente HTTP assíncrono

### 🌐 Interface Web
- **streamlit**: Framework para aplicações web interativas
- **pandas**: Manipulação e análise de dados
- **plotly**: Gráficos e visualizações interativas

### 🤖 Inteligência Artificial
- **openai**: Cliente da API OpenAI para recursos de IA

### ⚙️ Utilitários
- **python-dotenv**: Gerenciamento de variáveis de ambiente

## 📦 Instalação

### 1. Instalar Poetry (se não tiver)
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Instalar Dependências do Projeto
```bash
# Navegar para o diretório do projeto
cd supabase-py

# Instalar todas as dependências
poetry install

# Ou instalar apenas dependências de produção (sem dev)
poetry install --only=main
```

### 3. Ativar Ambiente Virtual
```bash
# Ativar shell do Poetry
poetry shell

# Ou executar comandos diretamente
poetry run python assistente_escolar_ia.py
poetry run streamlit run interface_processamento_extrato.py
```

## 🔧 Comandos Úteis

### Gerenciar Dependências
```bash
# Adicionar nova dependência
poetry add nome-da-dependencia

# Adicionar dependência de desenvolvimento
poetry add --group dev nome-da-dependencia

# Remover dependência
poetry remove nome-da-dependencia

# Atualizar dependências
poetry update

# Ver dependências instaladas
poetry show
```

### Executar Aplicações
```bash
# Executar interface web Streamlit
poetry run streamlit run interface_processamento_extrato.py

# Executar assistente de IA
poetry run python assistente_escolar_ia.py

# Executar executor unificado
poetry run python executor_unificado.py
```

## 🌍 Variáveis de Ambiente

Antes de executar as aplicações, configure as variáveis de ambiente:

```bash
# Criar arquivo .env na raiz do projeto
cp .env.example .env

# Editar com suas chaves
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

## 🔍 Verificar Instalação

```bash
# Verificar se Poetry está funcionando
poetry --version

# Verificar dependências instaladas
poetry show

# Executar testes (se disponíveis)
poetry run pytest
```

## 📚 Estrutura de Arquivos Principais

```
supabase-py/
├── pyproject.toml              # Configuração do Poetry
├── poetry.lock                 # Lock das versões
├── .env                        # Variáveis de ambiente
├── interface_processamento_extrato.py  # Interface Streamlit
├── assistente_escolar_ia.py    # Assistente com IA
├── funcoes_extrato_otimizadas.py      # Funções core
├── executor_unificado.py       # Executor principal
└── supabase_functions.py       # Funções Supabase
```

## 🚨 Resolução de Problemas

### Erro: "poetry: command not found"
```bash
# Adicionar Poetry ao PATH
export PATH="$HOME/.local/bin:$PATH"

# Ou reinstalar Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

### Erro: "No module named 'streamlit'"
```bash
# Reinstalar dependências
poetry install --sync

# Ou instalar manualmente
poetry add streamlit pandas plotly openai python-dotenv
```

### Erro: "ModuleNotFoundError"
```bash
# Verificar se está no ambiente virtual do Poetry
poetry shell

# Ou executar com poetry run
poetry run python seu_script.py
```

## 🎯 Próximos Passos

1. ✅ Instalar Poetry
2. ✅ Executar `poetry install`
3. ✅ Configurar arquivo `.env`
4. ✅ Executar `poetry shell`
5. 🚀 Executar as aplicações!

---

💡 **Dica**: Use sempre `poetry run` antes dos comandos Python para garantir que está usando o ambiente virtual correto. 