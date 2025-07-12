# 💰 Modal de Detalhamento e Ações de Mensalidade

## 📋 Visão Geral

O **Modal de Detalhamento e Ações de Mensalidade** é um componente completo e moderno para gerenciar mensalidades individuais no sistema de gestão escolar. Implementado em Streamlit, oferece uma interface intuitiva e funcional com 5 abas especializadas.

## 🎯 Características Principais

### ✨ Design Moderno
- **Header com gradiente** - Título elegante com informações contextuais
- **Badges coloridos** - Status visual com cores e emojis
- **CSS personalizado** - Interface responsiva e atrativa
- **Footer informativo** - Timestamp e atalhos

### 🚀 5 Abas Funcionais

#### 1. 📋 **Detalhes**
- **Informações completas** do aluno, responsável e mensalidade
- **Status visual** com cores e emojis dinâmicos
- **Métricas importantes** (valor, vencimento, situação)
- **Ações rápidas** para navegação

#### 2. ✏️ **Edição**
- **Formulário completo** com validações
- **Edição de valores** e datas
- **Aplicação de descontos/acréscimos**
- **Alteração de status** e observações
- **Salvamento automático**

#### 3. ⚡ **Ações**
- **Marcar como pago** (completo ou parcial)
- **Cancelar mensalidade** com confirmação
- **Aplicar descontos** específicos
- **Gerar documentos** (recibos, boletos)
- **Formulários secundários** para cada ação

#### 4. 📚 **Histórico**
- **Timeline visual** de alterações
- **Auditoria completa** de modificações
- **Metadados técnicos** de criação/atualização
- **Sistema de log** básico e expandível

#### 5. 📊 **Relatórios**
- **Documentos básicos** (recibo, boleto, declaração)
- **Relatórios personalizados** com configurações
- **Envio por email/WhatsApp**
- **Preview dos dados** incluídos

## 📁 Estrutura de Arquivos

```
modal_mensalidade_completo.py     # Modal principal com todas as funcionalidades
exemplo_uso_modal_mensalidade.py  # Exemplo de integração e uso
README_MODAL_MENSALIDADE.md       # Esta documentação
```

## 🚀 Como Usar

### 1. **Instalação e Configuração**

```python
# Importar o modal no seu projeto
from modal_mensalidade_completo import abrir_modal_mensalidade

# Configurar dependências necessárias
from models.base import supabase, formatar_data_br, formatar_valor_br
```

### 2. **Integração Básica**

```python
import streamlit as st

# Estado da sessão para controlar o modal
if 'modal_aberto' not in st.session_state:
    st.session_state.modal_aberto = False
if 'id_mensalidade_modal' not in st.session_state:
    st.session_state.id_mensalidade_modal = None

# Botão para abrir o modal
if st.button("🔍 Ver Detalhes"):
    st.session_state.modal_aberto = True
    st.session_state.id_mensalidade_modal = "seu_id_mensalidade"
    st.rerun()

# Renderizar o modal se estiver aberto
if st.session_state.modal_aberto and st.session_state.id_mensalidade_modal:
    abrir_modal_mensalidade(st.session_state.id_mensalidade_modal)
```

### 3. **Exemplo Completo**

Execute o arquivo de exemplo:

```bash
streamlit run exemplo_uso_modal_mensalidade.py
```

## 🔧 Funcionalidades Detalhadas

### 📋 Aba Detalhes

**Informações Exibidas:**
- Dados completos do aluno (nome, turma, turno, datas)
- Informações dos responsáveis (financeiro destacado)
- Detalhes da mensalidade (valor, vencimento, status)
- Métricas visuais (situação, dias para vencimento)

**Recursos:**
- Status com cores dinâmicas
- Cards informativos organizados
- Ações rápidas para outras abas
- Validação de dados em tempo real

### ✏️ Aba Edição

**Campos Editáveis:**
- Valor da mensalidade
- Data de vencimento
- Status (A vencer, Atrasado, Pago, etc.)
- Data de pagamento (condicional)
- Forma de pagamento
- Observações
- Desconto/Acréscimo

**Validações:**
- Valores mínimos e máximos
- Datas futuras limitadas
- Motivo obrigatório para alterações
- Confirmação antes de salvar

### ⚡ Aba Ações

**Ações Financeiras:**
- ✅ Marcar como Pago
- 🔶 Pagamento Parcial
- 💸 Aplicar Desconto
- 🧾 Gerar Recibo/Boleto

**Ações Administrativas:**
- ❌ Cancelar Mensalidade
- 📧 Enviar Cobrança
- 🤝 Renegociar
- 🔄 Transferir/Trocar

**Características:**
- Formulários secundários para confirmação
- Validações específicas para cada ação
- Registros automáticos no histórico
- Feedback visual para o usuário

### 📚 Aba Histórico

**Informações do Timeline:**
- Data e hora das alterações
- Usuário responsável
- Tipo de ação realizada
- Detalhes da modificação

**Recursos:**
- Timeline visual com ícones
- Cards coloridos por tipo de ação
- Metadados técnicos expandíveis
- Auditoria básica integrada

### 📊 Aba Relatórios

**Documentos Básicos:**
- 🧾 Recibo de Pagamento (apenas para pagas)
- 📄 Boleto/Cobrança (para pendentes)
- ⚠️ Declaração de Débito
- 📚 Relatório Completo

**Relatórios Personalizados:**
- Configuração de campos incluídos
- Escolha de formato (PDF, Word, Excel)
- Opções de gráficos e timeline
- Observações específicas

**Envio e Compartilhamento:**
- 📧 Email para responsáveis
- 📱 WhatsApp com link
- 💾 Download direto

## 🎨 Personalização

### CSS Customizado

O modal inclui CSS personalizado para:
- Header com gradiente
- Badges coloridos para status
- Cards informativos
- Animações e transições
- Responsividade

### Temas e Cores

```css
/* Principais cores utilizadas */
--primary-color: #667eea
--secondary-color: #764ba2
--success-color: #28a745
--warning-color: #ffc107
--error-color: #dc3545
```

## 📊 Integração com Banco de Dados

### Estrutura Esperada da Tabela `mensalidades`

```sql
CREATE TABLE mensalidades (
    id_mensalidade TEXT PRIMARY KEY,
    id_aluno TEXT NOT NULL,
    mes_referencia TEXT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    status TEXT NOT NULL,
    forma_pagamento TEXT,
    valor_pago DECIMAL(10,2),
    observacoes TEXT,
    inserted_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Relacionamentos Necessários

- `alunos` - Informações básicas do aluno
- `turmas` - Dados da turma
- `responsaveis` - Informações dos responsáveis
- `alunos_responsaveis` - Vinculação aluno-responsável

## ⚡ Performance e Otimização

### Cache de Dados
- Implementado com `@st.cache_data`
- TTL configurável (padrão: 5 minutos)
- Invalidação automática em alterações

### Otimizações
- Consultas SQL otimizadas
- Carregamento sob demanda
- Estados de sessão eficientes
- Renderização condicional

## 🔒 Segurança

### Validações Implementadas
- Sanitização de inputs
- Validação de tipos de dados
- Limites de valores e datas
- Confirmações para ações críticas

### Auditoria
- Log de alterações
- Registro de usuários
- Timestamp de operações
- Backup automático

## 🐛 Solução de Problemas

### Problemas Comuns

**Modal não abre:**
- Verifique se `st.session_state.modal_aberto = True`
- Confirme se `id_mensalidade_modal` está definido
- Teste com `st.rerun()` após definir o estado

**Dados não carregam:**
- Verifique conexão com Supabase
- Confirme estrutura das tabelas
- Teste consultas SQL isoladamente

**Erro de CSS:**
- Confirme que `aplicar_css_modal()` é chamado
- Verifique conflitos com CSS global
- Teste sem CSS customizado

**Salvamento falha:**
- Verifique permissões no banco
- Confirme formato dos dados
- Teste validações individualmente

### Debug

```python
# Adicionar logs para debug
import logging
logging.basicConfig(level=logging.DEBUG)

# Verificar estado da sessão
st.write("Debug:", st.session_state)

# Testar conexão
try:
    test = supabase.table("mensalidades").select("*").limit(1).execute()
    st.success("Conexão OK")
except Exception as e:
    st.error(f"Erro: {e}")
```

## 🚀 Próximas Funcionalidades

### Em Desenvolvimento
- [ ] Sistema de auditoria completo
- [ ] Geração real de PDFs
- [ ] Integração com email SMTP
- [ ] API WhatsApp Business
- [ ] Backup automático
- [ ] Relatórios avançados com gráficos

### Melhorias Planejadas
- [ ] Modo escuro
- [ ] Atalhos de teclado
- [ ] Notificações push
- [ ] Múltiplos idiomas
- [ ] Exportação em lote
- [ ] Dashboard analytics

## 📞 Suporte

### Documentação
- Código comentado em português
- Exemplos práticos incluídos
- Casos de uso documentados

### Contribuições
- Issues e PRs bem-vindos
- Código aberto e extensível
- Padrões de desenvolvimento claros

---

## 🎯 Conclusão

O Modal de Detalhamento e Ações de Mensalidade oferece uma solução completa e moderna para gestão de mensalidades escolares. Com interface intuitiva, funcionalidades abrangentes e código bem estruturado, é ideal para sistemas educacionais que precisam de eficiência e profissionalismo.

**Recursos Destacados:**
✅ Interface moderna e responsiva  
✅ 5 abas funcionais completas  
✅ Validações e segurança  
✅ Integração com Supabase  
✅ Código documentado  
✅ Exemplo prático incluído  

**Pronto para produção e fácil de personalizar! 🚀** 