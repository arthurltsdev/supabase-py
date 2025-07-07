# 💰 SISTEMA DE COBRANÇAS - PLANEJAMENTO COMPLETO

## 🎯 **Objetivo**

Implementar um sistema robusto para gerenciar **cobranças adicionais** além das mensalidades regulares, permitindo:

- **Formatura parcelada** (6 parcelas mensais)
- **Eventos e taxas** (festa junina, material, uniforme)
- **Dívidas anteriores** e **renegociações**
- **Cobranças pontuais** com diferentes prioridades

## 📊 **Estrutura Implementada**

### 1. **Nova Tabela: `cobrancas`**

```sql
CREATE TABLE cobrancas (
    id_cobranca TEXT PRIMARY KEY,           -- COB_XXXXXX
    id_aluno TEXT NOT NULL,                 -- FK: alunos(id)
    id_responsavel TEXT,                    -- FK: responsaveis(id)
    titulo TEXT NOT NULL,                   -- "Formatura 2025 - Parcela 1/6"
    descricao TEXT,                         -- Detalhes adicionais
    valor NUMERIC NOT NULL,                 -- Valor da cobrança
    data_vencimento DATE NOT NULL,          -- Data de vencimento
    data_pagamento DATE,                    -- NULL se não pago
    status TEXT DEFAULT 'Pendente',         -- Pendente/Pago/Vencido/Cancelado
    tipo_cobranca TEXT DEFAULT 'outros',    -- formatura/evento/taxa/etc
    grupo_cobranca TEXT,                    -- Agrupa parcelas relacionadas
    parcela_numero INTEGER DEFAULT 1,       -- Número da parcela
    parcela_total INTEGER DEFAULT 1,        -- Total de parcelas
    id_pagamento TEXT,                      -- FK: pagamentos(id_pagamento)
    observacoes TEXT,                       -- Observações
    prioridade INTEGER DEFAULT 1,           -- 1=baixa, 5=urgente
    inserted_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. **Funcionalidades Python Desenvolvidas**

✅ **`listar_cobrancas_aluno()`** - Lista cobranças com estatísticas  
✅ **`cadastrar_cobranca_individual()`** - Cobrança única  
✅ **`cadastrar_cobranca_parcelada()`** - Múltiplas parcelas  
✅ **`atualizar_cobranca()`** - Editar cobrança  
✅ **`marcar_cobranca_como_paga()`** - Marcar como paga  
✅ **`cancelar_cobranca()`** - Cancelar cobrança  
✅ **`listar_cobrancas_por_grupo()`** - Ver todas as parcelas  

## 🚀 **Plano de Implementação**

### **Etapa 1: Criação da Tabela** ✅ CONCLUÍDA
- [x] Script SQL criado: `script_criacao_tabela_cobrancas.sql`
- [x] Índices e triggers configurados
- [x] Relacionamentos com tabelas existentes

### **Etapa 2: Funções Backend** ✅ CONCLUÍDA  
- [x] Schema da tabela adicionado ao `models/base.py`
- [x] Todas as funções implementadas em `gestao_cobrancas.py`
- [x] Integração pronta para `models/pedagogico.py`

### **Etapa 3: Interface Streamlit** 🔄 PRÓXIMA ETAPA

#### **3.1 Nova Tab "Cobranças" na Interface do Aluno**

**Localização:** `interface_pedagogica_teste.py` → função `mostrar_detalhes_aluno()`

**Estrutura proposta:**
```python
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Dados do Aluno", 
    "👥 Responsáveis", 
    "💰 Pagamentos", 
    "📊 Extrato PIX",
    "📅 Mensalidades",
    "💰 Cobranças"  # ← NOVA TAB
])
```

#### **3.2 Conteúdo da Tab "Cobranças"**

**Métricas no topo:**
```
⏳ Pendentes: 3    ⚠️ Vencidas: 1    ✅ Pagas: 2    💰 Total: R$ 850,00
```

**Seções:**
1. **📋 Lista de Cobranças** - Tabela com todas as cobranças
2. **➕ Nova Cobrança** - Formulário para cadastrar
3. **📦 Cobranças Agrupadas** - Exibir parcelas relacionadas

#### **3.3 Formulários de Cadastro**

**Cobrança Individual:**
```python
with st.form("nova_cobranca_individual"):
    col1, col2 = st.columns(2)
    
    with col1:
        titulo = st.text_input("Título*")
        valor = st.number_input("Valor (R$)*", min_value=0.01)
        data_vencimento = st.date_input("Data de Vencimento*")
    
    with col2:
        tipo_cobranca = st.selectbox("Tipo*", TIPOS_COBRANCA)
        prioridade = st.selectbox("Prioridade", PRIORIDADES_COBRANCA)
        descricao = st.text_area("Descrição")
```

**Cobrança Parcelada:**
```python
with st.form("nova_cobranca_parcelada"):
    col1, col2 = st.columns(2)
    
    with col1:
        titulo_base = st.text_input("Título Base*")
        valor_parcela = st.number_input("Valor por Parcela (R$)*")
        numero_parcelas = st.number_input("Número de Parcelas*", min_value=2, max_value=24)
    
    with col2:
        data_primeira = st.date_input("Primeira Parcela*")
        tipo_cobranca = st.selectbox("Tipo*", TIPOS_COBRANCA)
```

#### **3.4 Exibição das Cobranças**

**Lista principal:**
```python
for cobranca in cobrancas:
    with st.expander(f"{cobranca['emoji']} {cobranca['titulo_completo']} - {cobranca['valor_br']}", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"📅 Vencimento: {cobranca['data_vencimento_br']}")
            st.write(f"🎯 Tipo: {cobranca['tipo_display']}")
        
        with col2:
            st.write(f"🔢 Status: {cobranca['status_real']}")
            st.write(f"⚡ Prioridade: {cobranca['prioridade_display']}")
        
        with col3:
            if cobranca['status_real'] == 'Pendente':
                if st.button("✅ Marcar como Pago", key=f"pagar_{cobranca['id_cobranca']}"):
                    # Processar pagamento
            elif cobranca['status_real'] == 'Pago':
                st.success(f"Pago em: {cobranca['data_pagamento_br']}")
```

### **Etapa 4: Integração com Sistema de Pagamentos** 🔄 FUTURA

- [ ] Processar pagamentos de PIX para cobranças
- [ ] Integrar com extrato PIX existente
- [ ] Relatórios financeiros incluindo cobranças

## 💡 **Exemplos de Casos de Uso**

### **Caso 1: Formatura Parcelada**
```python
dados_formatura = {
    "titulo": "Formatura 2025",
    "valor_parcela": 150.00,
    "numero_parcelas": 6,
    "data_primeira_parcela": "2025-02-05",
    "tipo_cobranca": "formatura",
    "descricao": "Formatura da turma Infantil III",
    "prioridade": 3
}

resultado = cadastrar_cobranca_parcelada(id_aluno, id_responsavel, dados_formatura)
# Cria: FORM_2025_ALU123456 (6 parcelas de fev a jul)
```

### **Caso 2: Taxa de Material**
```python
dados_material = {
    "titulo": "Taxa de Material Escolar 2025",
    "valor": 280.00,
    "data_vencimento": "2025-01-15",
    "tipo_cobranca": "material",
    "descricao": "Kit completo de material para o ano letivo",
    "prioridade": 2
}

resultado = cadastrar_cobranca_individual(id_aluno, id_responsavel, dados_material)
```

### **Caso 3: Dívida Anterior**
```python
dados_divida = {
    "titulo": "Mensalidade Dezembro 2024",
    "valor": 300.00,
    "data_vencimento": "2025-01-10",
    "tipo_cobranca": "divida",
    "observacoes": "Renegociado para pagamento até 10/01/2025",
    "prioridade": 4
}

resultado = cadastrar_cobranca_individual(id_aluno, id_responsavel, dados_divida)
```

## 📈 **Benefícios do Sistema**

### **Para a Escola:**
✅ **Controle total** de cobranças extras  
✅ **Flexibilidade** para diferentes tipos de cobrança  
✅ **Relatórios consolidados** financeiros  
✅ **Histórico completo** de pendências  

### **Para os Responsáveis:**
✅ **Visibilidade clara** de todas as cobranças  
✅ **Parcelamento** facilitado para valores altos  
✅ **Priorização** das cobranças mais urgentes  
✅ **Integração** com sistema de pagamentos PIX  

### **Para o Sistema:**
✅ **Separação clara** entre mensalidades e cobranças extras  
✅ **Escalabilidade** para novos tipos de cobrança  
✅ **Integração** com sistema existente  
✅ **Auditoria completa** de todas as transações  

## 🛠️ **Próximos Passos**

### **Imediatos:**
1. ✅ Criar tabela no banco de dados
2. ✅ Integrar funções ao `models/pedagogico.py`  
3. 🔄 Implementar interface na tab "Cobranças"
4. 🔄 Testar com dados reais

### **Médio Prazo:**
5. 🔄 Integrar com processamento de PIX
6. 🔄 Adicionar aos relatórios financeiros
7. 🔄 Implementar notificações automáticas

### **Longo Prazo:**
8. 🔄 API para integrações externas
9. 🔄 Dashboard administrativo
10. 🔄 Análises e métricas avançadas

---

## 📁 **Arquivos Criados**

- `script_criacao_tabela_cobrancas.sql` - Script para criar a tabela
- `gestao_cobrancas.py` - Funções Python completas
- `PLANEJAMENTO_SISTEMA_COBRANCAS.md` - Esta documentação

## 🎯 **Status Atual**

**✅ BACKEND COMPLETO** - Tabela e funções prontas  
**🔄 FRONTEND EM PLANEJAMENTO** - Interface Streamlit  
**🔄 INTEGRAÇÃO PENDENTE** - Conexão com sistema atual  

O sistema está **tecnicamente pronto** para implementação! 