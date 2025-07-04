#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 EXEMPLO DE INTERFACE PEDAGÓGICA ESTRATÉGICA
==============================================

Interface demonstrativa das funcionalidades estratégicas implementadas:
1. Filtros por campos vazios
2. Visualização e edição completa de dados
3. Cadastro completo de alunos e responsáveis
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional

# Importar funções dos modelos
from models.pedagogico import (
    listar_turmas_disponiveis,
    obter_mapeamento_turmas,
    buscar_alunos_por_turmas,
    filtrar_alunos_por_campos_vazios,
    buscar_informacoes_completas_aluno,
    atualizar_aluno_campos,
    atualizar_responsavel_campos,
    cadastrar_aluno_e_vincular,
    buscar_responsaveis_para_dropdown,
    buscar_alunos_para_dropdown
)

# Configuração da página
st.set_page_config(
    page_title="Interface Pedagógica Estratégica",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .student-card {
        background-color: #f8f9fa;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .empty-field {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 5px;
        margin: 2px 0;
    }
    .complete-field {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 5px;
        margin: 2px 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Inicializa o estado da sessão"""
    defaults = {
        'selected_student_id': None,
        'edit_mode': False,
        'filter_results': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def mostrar_card_aluno_detalhado(aluno: Dict, mostrar_responsaveis: bool = True):
    """Mostra card detalhado do aluno com informações completas"""
    
    # Identificar campos vazios
    campos_vazios = aluno.get("campos_vazios_aluno", [])
    
    with st.container():
        st.markdown(f"""
        <div class="student-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #2c3e50;">👨‍🎓 {aluno['nome']}</h4>
                <span style="background-color: #3498db; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">
                    {aluno['turma_nome']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Layout em colunas
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown("**📋 Dados Básicos:**")
            
            # Turno
            if "turno" in campos_vazios:
                st.markdown('<div class="empty-field">🕐 <strong>Turno:</strong> ❌ Não informado</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="complete-field">🕐 <strong>Turno:</strong> ✅ {aluno.get("turno", "N/A")}</div>', unsafe_allow_html=True)
            
            # Data de nascimento
            if "data_nascimento" in campos_vazios:
                st.markdown('<div class="empty-field">🎂 <strong>Nascimento:</strong> ❌ Não informado</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="complete-field">🎂 <strong>Nascimento:</strong> ✅ {aluno.get("data_nascimento", "N/A")}</div>', unsafe_allow_html=True)
            
            # Data de matrícula
            if "data_matricula" in campos_vazios:
                st.markdown('<div class="empty-field">🎓 <strong>Matrícula:</strong> ❌ Não informado</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="complete-field">🎓 <strong>Matrícula:</strong> ✅ {aluno.get("data_matricula", "N/A")}</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("**💰 Dados Financeiros:**")
            
            # Valor mensalidade
            if "valor_mensalidade" in campos_vazios:
                st.markdown('<div class="empty-field">💵 <strong>Mensalidade:</strong> ❌ Não informado</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="complete-field">💵 <strong>Mensalidade:</strong> ✅ R$ {aluno.get("valor_mensalidade", 0):.2f}</div>', unsafe_allow_html=True)
            
            # Dia vencimento
            if "dia_vencimento" in campos_vazios:
                st.markdown('<div class="empty-field">📅 <strong>Vencimento:</strong> ❌ Não informado</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="complete-field">📅 <strong>Vencimento:</strong> ✅ Dia {aluno.get("dia_vencimento", "N/A")}</div>', unsafe_allow_html=True)
            
            # Resumo de campos vazios
            total_campos = 5  # turno, data_nascimento, data_matricula, valor_mensalidade, dia_vencimento
            campos_preenchidos = total_campos - len(campos_vazios)
            percentual_completo = (campos_preenchidos / total_campos) * 100
            
            if percentual_completo == 100:
                st.success(f"✅ Dados 100% completos")
            elif percentual_completo >= 80:
                st.warning(f"⚠️ Dados {percentual_completo:.0f}% completos")
            else:
                st.error(f"❌ Dados {percentual_completo:.0f}% completos")
        
        with col3:
            st.markdown("**🎯 Ações:**")
            
            if st.button(f"👁️ Ver Detalhes", key=f"detalhes_{aluno['id']}", use_container_width=True):
                st.session_state.selected_student_id = aluno['id']
                st.rerun()
            
            if st.button(f"✏️ Editar", key=f"editar_{aluno['id']}", use_container_width=True):
                st.session_state.selected_student_id = aluno['id']
                st.session_state.edit_mode = True
                st.rerun()
        
        # Mostrar responsáveis se solicitado
        if mostrar_responsaveis and aluno.get("responsaveis"):
            st.markdown("**👨‍👩‍👧‍👦 Responsáveis:**")
            
            for i, resp in enumerate(aluno["responsaveis"], 1):
                campos_vazios_resp = resp.get("campos_vazios", [])
                total_campos_resp = 4  # telefone, email, cpf, endereco
                campos_preenchidos_resp = total_campos_resp - len(campos_vazios_resp)
                
                financeiro_badge = "💰" if resp.get('responsavel_financeiro') else "👤"
                
                col_resp1, col_resp2 = st.columns([3, 1])
                
                with col_resp1:
                    st.write(f"{financeiro_badge} **{resp['nome']}** - {resp.get('tipo_relacao', 'responsável')}")
                    
                    if campos_vazios_resp:
                        st.write(f"   ⚠️ Campos vazios: {', '.join(campos_vazios_resp)}")
                    else:
                        st.write(f"   ✅ Dados completos")
                
                with col_resp2:
                    if campos_preenchidos_resp == total_campos_resp:
                        st.success("100%")
                    elif campos_preenchidos_resp >= 3:
                        st.warning(f"{(campos_preenchidos_resp/total_campos_resp)*100:.0f}%")
                    else:
                        st.error(f"{(campos_preenchidos_resp/total_campos_resp)*100:.0f}%")

def main():
    """Função principal da interface"""
    
    init_session_state()
    
    # Header
    st.title("🎓 Interface Pedagógica Estratégica")
    st.markdown("Sistema completo de gestão pedagógica com filtros avançados e edição completa")
    
    # Sidebar com filtros
    with st.sidebar:
        st.header("🔍 Filtros Estratégicos")
        
        # Filtro por campos vazios
        st.subheader("📋 Campos Vazios")
        
        campos_para_filtrar = st.multiselect(
            "Selecione campos vazios para filtrar:",
            options=["turno", "data_nascimento", "dia_vencimento", "data_matricula", "valor_mensalidade"],
            default=[]
        )
        
        # Filtro por turmas
        st.subheader("🎓 Turmas")
        
        turmas_resultado = listar_turmas_disponiveis()
        if turmas_resultado.get("success"):
            turmas_selecionadas = st.multiselect(
                "Selecione turmas:",
                options=turmas_resultado["turmas"],
                default=[]
            )
        else:
            st.error("Erro ao carregar turmas")
            turmas_selecionadas = []
        
        # Botão para aplicar filtros
        if st.button("🔍 Aplicar Filtros", type="primary"):
            if campos_para_filtrar:
                # Obter IDs das turmas se selecionadas
                ids_turmas = None
                if turmas_selecionadas:
                    mapeamento = obter_mapeamento_turmas()
                    if mapeamento.get("success"):
                        ids_turmas = [mapeamento["mapeamento"][nome] for nome in turmas_selecionadas if nome in mapeamento["mapeamento"]]
                
                resultado = filtrar_alunos_por_campos_vazios(campos_para_filtrar, ids_turmas)
                st.session_state.filter_results = resultado
                st.rerun()
            else:
                st.warning("Selecione pelo menos um campo vazio para filtrar")
    
    # Interface principal
    st.header("🔍 Alunos com Campos Vazios")
    
    if st.session_state.filter_results:
        resultado = st.session_state.filter_results
        
        if resultado.get("success"):
            if resultado["count"] > 0:
                st.info(f"📊 Encontrados {resultado['count']} alunos com campos vazios: {', '.join(resultado['campos_filtrados'])}")
                
                # Mostrar cards dos alunos
                for aluno in resultado["alunos"]:
                    mostrar_card_aluno_detalhado(aluno, mostrar_responsaveis=True)
            else:
                st.success("✅ Nenhum aluno encontrado com os campos vazios especificados")
        else:
            st.error(f"❌ Erro na busca: {resultado.get('error')}")
    else:
        st.info("👆 Use os filtros na barra lateral para buscar alunos com campos vazios")
        
        # Mostrar exemplo de uso
        st.markdown("""
        ### 💡 Como Usar os Filtros Estratégicos
        
        **1. Filtros por Campos Vazios:**
        - Selecione quais campos você quer verificar se estão vazios
        - Exemplo: "valor_mensalidade" para encontrar alunos sem mensalidade definida
        
        **2. Filtros por Turmas:**
        - Opcionalmente, filtre por turmas específicas
        - Combine com campos vazios para análises mais precisas
        
        **3. Visualização e Edição:**
        - Cada aluno mostra status visual dos campos (✅ completo / ❌ vazio)
        - Botão "Ver Detalhes" para informações completas
        - Botão "Editar" para alterar dados diretamente
        
        **4. Responsáveis:**
        - Visualize informações completas dos responsáveis
        - Identifique campos vazios dos responsáveis
        - Edite dados dos responsáveis
        """)

if __name__ == "__main__":
    main() 