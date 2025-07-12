# 🚀 GUIA TESTE - PROCESSAMENTO AUTOMATIZADO SIMPLIFICADO

## 📋 Resumo do Sistema

Sistema automatizado que gera mensalidades para turmas específicas e correlaciona com pagamentos PIX usando **tabelas originais** com identificação `[TESTE]`.

**🎯 Turmas processadas:** Berçário, Infantil I, Infantil II, Infantil III

## 🗂️ Arquivos Essenciais

- `exemplo_uso_modal_mensalidade.py` - Interface principal
- `modal_mensalidade_completo.py` - Modal com aba de processamento
- `processamento_automatizado_simplificado.py` - Lógica de negócio
- `models/base.py` - Configurações e conexão

## 🚀 Como Executar o Teste

### 1. **Executar a Interface Principal**
```bash
streamlit run exemplo_uso_modal_mensalidade.py
```

### 2. **Acessar o Processamento**
1. Na interface, clique em **qualquer mensalidade** para abrir o modal
2. Clique na aba **"🤖 Processamento"**
3. Você verá a tela de configuração do processamento

### 3. **Etapa 1: Configuração**
- ✅ **Modo Teste** deve estar **MARCADO** (padrão)
- Define nome da sessão
- Mostra preview dos alunos elegíveis
- Clique **"🚀 Iniciar Processamento"**

### 4. **Etapa 2: Validação das Mensalidades**
- Lista todos os alunos elegíveis encontrados
- Mostra mensalidades que serão geradas automaticamente
- Permite **editar valores** antes de prosseguir
- Permite **incluir/excluir alunos** via checkbox
- Clique **"▶️ Próxima Etapa"** para continuar

### 5. **Etapa 3: Correlação PIX**
- Mostra correlações automáticas com pagamentos PIX
- Apresenta resumo das ações que serão executadas
- Clique **"🚀 EXECUTAR AÇÕES"** para processar

### 6. **Resultado Final**
- Confirmação das mensalidades criadas
- Resumo das correlações registradas
- Todos os dados marcados com `[TESTE]` nas observações

## 🔍 Verificando os Resultados

### **Mensalidades Criadas**
1. Volte para a interface principal (feche o modal)
2. Na barra lateral, use o filtro **"🔍 Nome do Aluno"**
3. Digite parte de um nome processado
4. Ou use o filtro **"📅 Período"** para ver mensalidades recentes

### **Identificação de Teste**
- Todas as mensalidades criadas terão `[TESTE]` no campo observações
- Isso facilita identificação e limpeza posterior

### **Correlações PIX**
- Pagamentos PIX correlacionados terão status atualizado no extrato
- Mensalidades vinculadas mostrarão data de pagamento

## 🧪 Características do Modo Teste

✅ **Seguro**: Usa tabelas originais com identificação especial  
✅ **Rastreável**: Fácil identificação dos dados de teste  
✅ **Reversível**: Dados podem ser facilmente removidos  
✅ **Auditável**: Todas as ações ficam registradas  

## 🎯 Critérios de Elegibilidade

Para ser processado, o aluno deve:
- ❌ **NÃO** ter mensalidades já geradas
- ✅ Estar em uma das 4 turmas-alvo
- ✅ Ter data de matrícula definida
- ✅ Ter dia de vencimento definido  
- ✅ Ter valor de mensalidade > 0

## 🛡️ Validações de Segurança

1. **Modo teste padrão**: Sempre inicia em modo seguro
2. **Validação em 2 etapas**: Usuário deve confirmar cada passo
3. **Identificação especial**: `[TESTE]` em todas as observações
4. **Reversibilidade**: Fácil identificação para limpeza
5. **Auditoria completa**: Histórico de todas as ações

## 🔧 Resolução de Problemas

### **Erro: "Nenhum aluno elegível"**
- Verifique se existem alunos nas turmas-alvo
- Confirme se não têm mensalidades já geradas
- Verifique se têm dados básicos preenchidos

### **Erro de conexão**
- Verifique arquivo `.env` com credenciais Supabase
- Teste a conexão com `python testar_conexao.py`

### **Modal não abre**
- Verifique se existem mensalidades no banco
- Tente recarregar a página

## 📊 Exemplo de Execução

**Input esperado:**
- 5 alunos elegíveis nas turmas-alvo
- Mensalidades geradas de julho/2024 até dezembro/2024
- Correlações automáticas com PIX existentes

**Output esperado:**
- ~30 mensalidades criadas (5 alunos × 6 meses)
- Dados marcados com `[TESTE]`
- Correlações PIX registradas

## ✅ Checklist Pós-Teste

- [ ] Mensalidades apareceram na lista principal
- [ ] Todas contêm `[TESTE]` nas observações  
- [ ] Correlações PIX foram registradas corretamente
- [ ] Dados podem ser identificados facilmente
- [ ] Sistema funcionou sem erros

---

**🎯 Objetivo:** Testar geração automatizada de mensalidades de forma segura e controlada, usando o fluxo completo de 2 etapas com validações objetivas. 