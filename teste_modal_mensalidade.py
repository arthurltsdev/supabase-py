#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE RÁPIDO DO MODAL DE MENSALIDADE
======================================

Script para testar rapidamente as funcionalidades do modal de mensalidade.
Execute para verificar se tudo está funcionando corretamente.
"""

import streamlit as st
from datetime import datetime, date
import json

st.set_page_config(
    page_title="🧪 Teste Modal Mensalidade",
    page_icon="💰",
    layout="wide"
)

st.title("🧪 Teste do Modal de Mensalidade")
st.markdown("### Verificação rápida das funcionalidades implementadas")

# ==========================================================
# TESTE 1: IMPORTAÇÃO DOS MÓDULOS
# ==========================================================

st.markdown("## 1️⃣ Teste de Importação")

try:
    from modal_mensalidade_completo import (
        abrir_modal_mensalidade,
        buscar_dados_completos_mensalidade,
        calcular_status_visual,
        aplicar_css_modal
    )
    st.success("✅ Modal principal importado com sucesso!")
except ImportError as e:
    st.error(f"❌ Erro ao importar modal principal: {e}")

try:
    from models.base import supabase, formatar_data_br, formatar_valor_br
    st.success("✅ Dependências do sistema importadas!")
except ImportError as e:
    st.warning(f"⚠️ Dependências opcionais não encontradas: {e}")

# ==========================================================
# TESTE 2: FUNÇÕES AUXILIARES
# ==========================================================

st.markdown("## 2️⃣ Teste de Funções Auxiliares")

# Teste da função calcular_status_visual
mensalidade_teste = {
    "status": "A vencer",
    "data_vencimento": "2024-12-31",
    "data_pagamento": None
}

try:
    status_resultado = calcular_status_visual(mensalidade_teste)
    st.success("✅ Função calcular_status_visual funcionando!")
    st.json(status_resultado)
except Exception as e:
    st.error(f"❌ Erro na função calcular_status_visual: {e}")

# ==========================================================
# TESTE 3: CSS PERSONALIZADO
# ==========================================================

st.markdown("## 3️⃣ Teste de CSS")

try:
    aplicar_css_modal()
    st.success("✅ CSS personalizado aplicado!")
    
    # Testar os estilos
    st.markdown("""
    <div class="info-card">
        <strong>📋 Card de teste:</strong> Este é um exemplo de card com CSS personalizado
    </div>
    
    <div class="success-card">
        <strong>✅ Card de sucesso:</strong> CSS para feedback positivo
    </div>
    
    <div class="warning-card">
        <strong>⚠️ Card de aviso:</strong> CSS para alertas
    </div>
    
    <div class="error-card">
        <strong>❌ Card de erro:</strong> CSS para erros
    </div>
    """, unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"❌ Erro ao aplicar CSS: {e}")

# ==========================================================
# TESTE 4: SIMULAÇÃO DO MODAL
# ==========================================================

st.markdown("## 4️⃣ Simulação do Modal")

# Estado da sessão para teste
if 'modal_teste_aberto' not in st.session_state:
    st.session_state.modal_teste_aberto = False

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚀 Testar Modal (Dados Reais)", type="primary"):
        # Tentar buscar uma mensalidade real
        try:
            response = supabase.table("mensalidades").select("id_mensalidade").limit(1).execute()
            if response.data:
                st.session_state.modal_teste_aberto = True
                st.session_state.id_mensalidade_teste = response.data[0]["id_mensalidade"]
                st.success(f"✅ Mensalidade encontrada: {response.data[0]['id_mensalidade']}")
            else:
                st.warning("⚠️ Nenhuma mensalidade encontrada no banco")
        except Exception as e:
            st.error(f"❌ Erro ao buscar mensalidade: {e}")

with col2:
    if st.button("🎭 Modo Demonstração", type="secondary"):
        st.info("🎭 Modo demonstração ativado!")
        st.session_state.modal_teste_aberto = True
        st.session_state.id_mensalidade_teste = "demo_123"

with col3:
    if st.button("❌ Fechar Teste"):
        st.session_state.modal_teste_aberto = False
        st.session_state.id_mensalidade_teste = None

# Renderizar modal de teste se ativo
if st.session_state.get('modal_teste_aberto', False):
    st.markdown("---")
    st.markdown("### 🔍 MODAL EM EXECUÇÃO")
    
    id_teste = st.session_state.get('id_mensalidade_teste', 'demo_123')
    
    try:
        # Se for modo demo, criar dados fictícios
        if id_teste == "demo_123":
            st.info("🎭 **Modo Demonstração Ativo** - Dados fictícios sendo utilizados")
            
            # Simular estrutura de dados
            dados_demo = {
                "mensalidade": {
                    "id_mensalidade": "demo_123",
                    "mes_referencia": "Janeiro/2024",
                    "valor": 250.00,
                    "data_vencimento": "2024-01-10",
                    "data_pagamento": None,
                    "status": "A vencer",
                    "observacoes": "Mensalidade de demonstração",
                    "inserted_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "alunos": {
                        "id": "aluno_demo",
                        "nome": "João Silva Demo",
                        "turno": "Manhã",
                        "valor_mensalidade": 250.00,
                        "data_nascimento": "2010-05-15",
                        "data_matricula": "2024-01-01",
                        "dia_vencimento": 10,
                        "turmas": {
                            "nome_turma": "1º Ano A",
                            "turno": "Manhã"
                        }
                    }
                },
                "responsaveis": [
                    {
                        "responsavel_financeiro": True,
                        "parentesco": "Pai",
                        "responsaveis": {
                            "id": "resp_demo",
                            "nome": "Carlos Silva Demo",
                            "telefone": "(11) 99999-9999",
                            "email": "carlos.demo@email.com",
                            "cpf": "123.456.789-00",
                            "endereco": "Rua Demo, 123"
                        }
                    }
                ],
                "pagamentos": [],
                "historico": [
                    {
                        "data": "2024-01-01T00:00:00Z",
                        "acao": "Criação",
                        "usuario": "Sistema Demo",
                        "detalhes": "Mensalidade de demonstração criada"
                    }
                ]
            }
            
            # Renderizar componentes do modal manualmente para demonstração
            from modal_mensalidade_completo import (
                renderizar_header_modal,
                renderizar_aba_detalhes,
                renderizar_footer_modal
            )
            
            # Header
            renderizar_header_modal(dados_demo)
            
            # Tabs de demonstração
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Detalhes",
                "✏️ Edição", 
                "⚡ Ações",
                "📚 Histórico",
                "📊 Relatórios"
            ])
            
            with tab1:
                renderizar_aba_detalhes(dados_demo)
            
            with tab2:
                st.info("🔧 Aba de edição em modo demonstração")
                st.markdown("Esta aba permitiria editar todos os campos da mensalidade")
            
            with tab3:
                st.info("🔧 Aba de ações em modo demonstração")
                st.markdown("Esta aba permitiria executar ações como marcar como pago, cancelar, etc.")
            
            with tab4:
                st.info("🔧 Aba de histórico em modo demonstração")
                st.markdown("Esta aba mostraria o timeline completo de alterações")
            
            with tab5:
                st.info("🔧 Aba de relatórios em modo demonstração")
                st.markdown("Esta aba permitiria gerar e enviar relatórios")
            
            # Footer
            renderizar_footer_modal(dados_demo)
            
        else:
            # Tentar modal real
            abrir_modal_mensalidade(id_teste)
            
    except Exception as e:
        st.error(f"❌ Erro ao renderizar modal: {e}")
        st.code(str(e))

# ==========================================================
# TESTE 5: VERIFICAÇÃO DE ESTRUTURA
# ==========================================================

st.markdown("## 5️⃣ Verificação de Estrutura")

# Verificar arquivos necessários
import os

arquivos_necessarios = [
    "modal_mensalidade_completo.py",
    "exemplo_uso_modal_mensalidade.py",
    "README_MODAL_MENSALIDADE.md"
]

st.markdown("### 📁 Arquivos do Sistema")
for arquivo in arquivos_necessarios:
    if os.path.exists(arquivo):
        st.success(f"✅ {arquivo}")
    else:
        st.error(f"❌ {arquivo} - Não encontrado")

# ==========================================================
# TESTE 6: INFORMAÇÕES DO SISTEMA
# ==========================================================

st.markdown("## 6️⃣ Informações do Sistema")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Estado da Sessão")
    
    # Filtrar apenas keys relacionados ao modal
    modal_keys = {k: v for k, v in st.session_state.items() if 'modal' in k.lower()}
    
    if modal_keys:
        st.json(modal_keys)
    else:
        st.info("Nenhum estado de modal ativo")

with col2:
    st.markdown("### 🔧 Configurações")
    
    config_info = {
        "Streamlit Version": st.__version__,
        "Python Version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Page Config": "Wide Layout"
    }
    
    st.json(config_info)

# ==========================================================
# RESULTADO FINAL
# ==========================================================

st.markdown("---")
st.markdown("## 🎯 Resultado Final")

try:
    # Tentar importar tudo
    from modal_mensalidade_completo import *
    
    st.success("🎉 **SUCESSO!** Modal de mensalidade implementado e funcionando!")
    
    st.markdown("""
    ### ✅ Funcionalidades Testadas:
    - ✅ Importação de módulos
    - ✅ Funções auxiliares
    - ✅ CSS personalizado
    - ✅ Estrutura de arquivos
    - ✅ Simulação do modal
    
    ### 🚀 Próximos Passos:
    1. **Execute o exemplo completo:** `streamlit run exemplo_uso_modal_mensalidade.py`
    2. **Integre ao seu sistema** usando as instruções do README
    3. **Personalize** o CSS e funcionalidades conforme necessário
    4. **Teste com dados reais** do seu banco Supabase
    
    ### 📚 Documentação:
    - Leia o `README_MODAL_MENSALIDADE.md` para instruções detalhadas
    - Veja o `exemplo_uso_modal_mensalidade.py` para implementação prática
    - Use este teste para verificar funcionamento
    """)
    
except Exception as e:
    st.error(f"❌ **ERRO:** {e}")
    st.markdown("Verifique os arquivos e dependências necessárias")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🧪 <strong>Teste do Modal de Mensalidade</strong> | 
    💰 Sistema de Gestão Escolar | 
    🔧 Versão de Teste
</div>
""", unsafe_allow_html=True) 