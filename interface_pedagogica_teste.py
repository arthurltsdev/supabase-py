#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 INTERFACE DE TESTE - MODELO PEDAGÓGICO
=========================================

Interface Streamlit para testar todas as funcionalidades do modelo pedagógico:
- Filtros por turma e campos vazios
- Cadastro e edição de alunos
- Gestão de responsáveis e vínculos
- Validações estratégicas
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import os

# Importar funções do modelo pedagógico
from models.pedagogico import (
    # Gestão de turmas
    listar_turmas_disponiveis,
    obter_mapeamento_turmas,
    
    # Gestão de alunos
    buscar_alunos_para_dropdown,
    buscar_alunos_por_turmas,
    buscar_informacoes_completas_aluno,
    atualizar_aluno_campos,
    cadastrar_aluno_e_vincular,
    filtrar_alunos_por_campos_vazios,
    listar_mensalidades_para_cancelamento,
    trancar_matricula_aluno,
    
    # Gestão de responsáveis
    buscar_responsaveis_para_dropdown,
    listar_responsaveis_aluno,
    listar_alunos_vinculados_responsavel,
    cadastrar_responsavel_e_vincular,
    verificar_responsavel_existe,
    atualizar_responsavel_campos,
    
    # Gestão de vínculos
    vincular_aluno_responsavel,
    atualizar_vinculo_responsavel,
    remover_vinculo_responsavel,
    buscar_dados_completos_alunos_responsavel,
    
    # Gestão de cobranças
    listar_cobrancas_aluno,
    cadastrar_cobranca_individual,
    cadastrar_cobranca_parcelada,
    atualizar_cobranca,
    marcar_cobranca_como_paga,
    cancelar_cobranca,
    listar_cobrancas_por_grupo
)

# Importar constantes e funções utilitárias do models.base
from models.base import (
    formatar_data_br,
    formatar_valor_br,
    TIPOS_COBRANCA_DISPLAY,
    PRIORIDADES_COBRANCA,
    supabase
)

# Configuração da página
st.set_page_config(
    page_title="🎓 Interface Pedagógica - Teste",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stDataFrame {font-size: 12px;}
    .success-card {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .error-card {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .info-card {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .warning-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 🔧 FUNÇÕES AUXILIARES
# ==========================================================

def init_session_state():
    """Inicializa o estado da sessão"""
    if 'aluno_selecionado' not in st.session_state:
        st.session_state.aluno_selecionado = None
    if 'responsavel_selecionado' not in st.session_state:
        st.session_state.responsavel_selecionado = None
    if 'historico_operacoes' not in st.session_state:
        st.session_state.historico_operacoes = []

def adicionar_historico(operacao: str, detalhes: Dict):
    """Adiciona operação ao histórico"""
    entrada = {
        'timestamp': datetime.now(),
        'operacao': operacao,
        'detalhes': detalhes
    }
    st.session_state.historico_operacoes.append(entrada)

def mostrar_resultado(resultado: Dict, operacao: str = "Operação"):
    """Mostra resultado de uma operação"""
    if resultado.get("success"):
        st.success(f"✅ {operacao} realizada com sucesso!")
        
        # Mostrar detalhes se houver
        if resultado.get("message"):
            st.info(resultado["message"])
        
        # Adicionar ao histórico
        adicionar_historico(operacao, resultado)
        
        return True
    else:
        st.error(f"❌ Erro na {operacao.lower()}: {resultado.get('error', 'Erro desconhecido')}")
        return False

def formatar_campo_vazio(valor, campo_nome: str) -> str:
    """Formata exibição de campos vazios"""
    if valor is None or valor == "" or valor == "Não informado":
        return f"❌ {campo_nome} vazio"
    else:
        return f"✅ {campo_nome}: {valor}"

# ==========================================================
# 🎨 INTERFACE PRINCIPAL
# ==========================================================

def main():
    """Função principal da interface"""
    
    # Inicializar estado
    init_session_state()
    
    # Header
    st.title("🎓 Interface de Teste - Modelo Pedagógico")
    st.markdown("Interface completa para testar todas as funcionalidades do modelo pedagógico")
    
    # Sidebar com informações
    with st.sidebar:
        st.header("📊 Estatísticas Rápidas")
        
        # Carregar estatísticas básicas
        turmas_resultado = listar_turmas_disponiveis()
        if turmas_resultado.get("success"):
            st.metric("🎓 Total de Turmas", turmas_resultado["count"])
        
        st.markdown("---")
        st.header("📋 Histórico de Operações")
        
        if st.session_state.historico_operacoes:
            st.write(f"📊 **Total:** {len(st.session_state.historico_operacoes)} operações")
            
            # Mostrar últimas 5 operações
            for i, op in enumerate(st.session_state.historico_operacoes[-5:], 1):
                timestamp = op['timestamp'].strftime("%H:%M:%S")
                st.write(f"**{i}.** [{timestamp}] {op['operacao']}")
            
            if st.button("🗑️ Limpar Histórico"):
                st.session_state.historico_operacoes = []
                st.rerun()
        else:
            st.info("Nenhuma operação realizada ainda")
    
    # Tabs principais
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🔍 Filtros e Consultas",
        "👨‍🎓 Gestão de Alunos", 
        "👨‍👩‍👧‍👦 Gestão de Responsáveis",
        "🔗 Gestão de Vínculos",
        "📝 Cadastros",
        "💰 Gestão de Cobranças",
        "📊 Relatórios"
    ])
    
    # ==========================================================
    # TAB 1: FILTROS E CONSULTAS
    # ==========================================================
    with tab1:
        st.header("🔍 Filtros e Consultas Estratégicas")
        
        # Seção 1: Filtro por Turmas
        st.subheader("🎓 Filtro por Turmas")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Carregar turmas disponíveis
            turmas_resultado = listar_turmas_disponiveis()
            if turmas_resultado.get("success"):
                turmas_selecionadas = st.multiselect(
                    "Selecione as turmas:",
                    options=turmas_resultado["turmas"],
                    help="Selecione uma ou mais turmas para filtrar alunos"
                )
            else:
                st.error(f"Erro ao carregar turmas: {turmas_resultado.get('error')}")
                turmas_selecionadas = []
        
        with col2:
            st.write(" ")  # Espaço
            if st.button("🔍 Buscar por Turmas", type="primary"):
                if turmas_selecionadas:
                    # Obter IDs das turmas
                    mapeamento_resultado = obter_mapeamento_turmas()
                    if mapeamento_resultado.get("success"):
                        ids_turmas = [mapeamento_resultado["mapeamento"][nome] for nome in turmas_selecionadas]
                        
                        with st.spinner("Buscando alunos..."):
                            resultado = buscar_alunos_por_turmas(ids_turmas)
                        
                        if mostrar_resultado(resultado, "Busca por turmas"):
                            st.session_state.resultado_busca_turmas = resultado
                    else:
                        st.error("Erro ao obter mapeamento de turmas")
                else:
                    st.warning("Selecione pelo menos uma turma")
        
        # Mostrar resultados da busca por turmas
        if hasattr(st.session_state, 'resultado_busca_turmas'):
            resultado = st.session_state.resultado_busca_turmas
            
            if resultado.get("success") and resultado.get("total_alunos", 0) > 0:
                st.markdown("### 📋 Resultados da Busca por Turmas")
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👨‍🎓 Total de Alunos", resultado["total_alunos"])
                with col2:
                    st.metric("🎓 Turmas", resultado["total_turmas"])
                with col3:
                    if st.button("🔄 Limpar Resultados"):
                        del st.session_state.resultado_busca_turmas
                        st.rerun()
                
                # Exibir alunos por turma
                for turma_nome, dados_turma in resultado["alunos_por_turma"].items():
                    with st.expander(f"🎓 {turma_nome} ({len(dados_turma['alunos'])} alunos)", expanded=True):
                        
                        for aluno in dados_turma["alunos"]:
                            col1, col2, col3 = st.columns([3, 2, 1])
                            
                            with col1:
                                st.write(f"**👨‍🎓 {aluno['nome']}**")
                                st.write(f"🕐 Turno: {aluno['turno']}")
                                st.write(f"💰 Mensalidade: R$ {aluno['valor_mensalidade']:.2f}")
                            
                            with col2:
                                st.write(f"**👥 Responsáveis ({aluno['total_responsaveis']}):**")
                                if aluno['responsaveis']:
                                    for resp in aluno['responsaveis']:
                                        emoji = "💰" if resp['responsavel_financeiro'] else "👤"
                                        st.write(f"{emoji} {resp['nome']} ({resp['tipo_relacao']})")
                                else:
                                    st.write("❌ Nenhum responsável")
                            
                            with col3:
                                if st.button(f"👁️ Detalhes", key=f"det_{aluno['id']}"):
                                    st.session_state.aluno_selecionado = aluno['id']
                                    st.rerun()
        
        # Seção 2: Filtro por Campos Vazios
        st.markdown("---")
        st.subheader("❓ Filtro por Campos Vazios")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            campos_disponiveis = {
                "turno": "Turno",
                "data_nascimento": "Data de Nascimento", 
                "dia_vencimento": "Dia de Vencimento",
                "data_matricula": "Data de Matrícula",
                "valor_mensalidade": "Valor da Mensalidade"
            }
            
            campos_selecionados = st.multiselect(
                "Selecione os campos para verificar se estão vazios:",
                options=list(campos_disponiveis.keys()),
                format_func=lambda x: campos_disponiveis[x],
                help="Alunos que possuem estes campos vazios serão listados"
            )
            
            # Filtro adicional por turma
            filtro_turma_vazios = st.multiselect(
                "Filtrar também por turmas (opcional):",
                options=turmas_resultado["turmas"] if turmas_resultado.get("success") else [],
                help="Deixe vazio para buscar em todas as turmas"
            )
        
        with col2:
            st.write(" ")  # Espaço
            if st.button("🔍 Buscar Campos Vazios", type="primary"):
                if campos_selecionados:
                    # Obter IDs das turmas se selecionadas
                    ids_turmas_filtro = None
                    if filtro_turma_vazios:
                        mapeamento_resultado = obter_mapeamento_turmas()
                        if mapeamento_resultado.get("success"):
                            ids_turmas_filtro = [mapeamento_resultado["mapeamento"][nome] for nome in filtro_turma_vazios]
                    
                    with st.spinner("Buscando alunos com campos vazios..."):
                        resultado = filtrar_alunos_por_campos_vazios(campos_selecionados, ids_turmas_filtro)
                    
                    if mostrar_resultado(resultado, "Busca por campos vazios"):
                        st.session_state.resultado_campos_vazios = resultado
                else:
                    st.warning("Selecione pelo menos um campo")
        
        # Mostrar resultados da busca por campos vazios
        if hasattr(st.session_state, 'resultado_campos_vazios'):
            resultado = st.session_state.resultado_campos_vazios
            
            if resultado.get("success") and resultado.get("count", 0) > 0:
                st.markdown("### ❓ Resultados - Alunos com Campos Vazios")
                
                # Métricas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👨‍🎓 Alunos Encontrados", resultado["count"])
                with col2:
                    campos_nomes = [campos_disponiveis[c] for c in resultado["campos_filtrados"]]
                    st.metric("🔍 Campos Filtrados", len(campos_nomes))
                with col3:
                    if st.button("🔄 Limpar Resultados", key="limpar_vazios"):
                        del st.session_state.resultado_campos_vazios
                        st.rerun()
                
                st.info(f"**Campos verificados:** {', '.join(campos_nomes)}")
                
                # Lista de alunos com problemas
                for aluno in resultado["alunos"]:
                    with st.expander(f"❓ {aluno['nome']} - {aluno['turma_nome']} ({len(aluno['campos_vazios_aluno'])} campos vazios)", expanded=False):
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📋 Dados do Aluno:**")
                            st.write(formatar_campo_vazio(aluno.get('turno'), "Turno"))
                            st.write(formatar_campo_vazio(aluno.get('data_nascimento'), "Data Nascimento"))
                            st.write(formatar_campo_vazio(aluno.get('dia_vencimento'), "Dia Vencimento"))
                            st.write(formatar_campo_vazio(aluno.get('data_matricula'), "Data Matrícula"))
                            st.write(formatar_campo_vazio(aluno.get('valor_mensalidade'), "Valor Mensalidade"))
                        
                        with col2:
                            st.markdown(f"**👥 Responsáveis ({aluno['total_responsaveis']}):**")
                            if aluno['responsaveis']:
                                for resp in aluno['responsaveis']:
                                    st.write(f"**{resp['nome']}** ({resp['tipo_relacao']})")
                                    
                                    # Mostrar campos vazios do responsável
                                    if resp.get('campos_vazios'):
                                        for campo_vazio in resp['campos_vazios']:
                                            st.write(f"   ❌ {campo_vazio.title()} vazio")
                            else:
                                st.write("❌ Nenhum responsável cadastrado")
                        
                        # Botão para editar
                        if st.button(f"✏️ Editar {aluno['nome']}", key=f"edit_{aluno['id']}"):
                            st.session_state.aluno_selecionado = aluno['id']
                            st.rerun()
            
            elif resultado.get("success"):
                st.success("✅ Nenhum aluno encontrado com os campos vazios especificados!")
    
    # ==========================================================
    # TAB 2: GESTÃO DE ALUNOS
    # ==========================================================
    with tab2:
        st.header("👨‍🎓 Gestão de Alunos")
        
        # Seção de busca
        st.subheader("🔍 Buscar Aluno")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            termo_busca = st.text_input(
                "Digite o nome do aluno:",
                placeholder="Digite pelo menos 2 caracteres...",
                key="busca_aluno"
            )
        
        with col2:
            st.write(" ")  # Espaço
            if st.button("🔍 Buscar"):
                if len(termo_busca) >= 2:
                    resultado = buscar_alunos_para_dropdown(termo_busca)
                    if resultado.get("success"):
                        st.session_state.alunos_encontrados = resultado["opcoes"]
                    else:
                        st.error(f"Erro na busca: {resultado.get('error')}")
                else:
                    st.warning("Digite pelo menos 2 caracteres")
        
        # Mostrar resultados da busca
        if hasattr(st.session_state, 'alunos_encontrados') and st.session_state.alunos_encontrados:
            st.markdown("### 📋 Alunos Encontrados")
            
            for aluno in st.session_state.alunos_encontrados:
                col1, col2, col3 = st.columns([4, 2, 2])
                
                with col1:
                    st.write(f"**👨‍🎓 {aluno['nome']}**")
                    st.write(f"🎓 {aluno['turma']}")
                
                with col2:
                    if st.button(f"👁️ Ver Detalhes", key=f"ver_{aluno['id']}"):
                        st.session_state.aluno_selecionado = aluno['id']
                        st.rerun()
                
                with col3:
                    if st.button(f"✏️ Editar", key=f"editar_{aluno['id']}"):
                        st.session_state.aluno_selecionado = aluno['id']
                        st.session_state.modo_edicao = True
                        st.rerun()
        
        # Mostrar detalhes do aluno selecionado
        if st.session_state.aluno_selecionado:
            st.markdown("---")
            mostrar_detalhes_aluno(st.session_state.aluno_selecionado)
    
    # ==========================================================
    # TAB 3: GESTÃO DE RESPONSÁVEIS
    # ==========================================================
    with tab3:
        st.header("👨‍👩‍👧‍👦 Gestão de Responsáveis")
        
        # Seção de busca de responsáveis
        st.subheader("🔍 Buscar Responsável")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            termo_busca_resp = st.text_input(
                "Digite o nome do responsável:",
                placeholder="Digite para buscar...",
                key="busca_responsavel"
            )
        
        with col2:
            st.write(" ")  # Espaço
            if st.button("🔍 Buscar", key="buscar_resp"):
                if termo_busca_resp:
                    resultado = buscar_responsaveis_para_dropdown(termo_busca_resp)
                    if resultado.get("success"):
                        st.session_state.responsaveis_encontrados = resultado["opcoes"]
                    else:
                        st.error(f"Erro na busca: {resultado.get('error')}")
                else:
                    st.warning("Digite o nome do responsável")
        
        # Mostrar resultados da busca de responsáveis
        if hasattr(st.session_state, 'responsaveis_encontrados') and st.session_state.responsaveis_encontrados:
            st.markdown("### 📋 Responsáveis Encontrados")
            
            for resp in st.session_state.responsaveis_encontrados:
                col1, col2, col3 = st.columns([4, 2, 2])
                
                with col1:
                    st.write(f"**👤 {resp['nome']}**")
                    if resp.get('telefone'):
                        st.write(f"📱 {resp['telefone']}")
                    if resp.get('email'):
                        st.write(f"📧 {resp['email']}")
                
                with col2:
                    if st.button(f"👁️ Ver Alunos", key=f"ver_alunos_{resp['id']}"):
                        st.session_state.responsavel_selecionado = resp['id']
                        st.rerun()
                
                with col3:
                    if st.button(f"✏️ Editar", key=f"editar_resp_{resp['id']}"):
                        st.session_state.responsavel_selecionado = resp['id']
                        st.session_state.modo_edicao_resp = True
                        st.rerun()
        
        # Mostrar detalhes do responsável selecionado
        if st.session_state.responsavel_selecionado:
            st.markdown("---")
            mostrar_detalhes_responsavel(st.session_state.responsavel_selecionado)
    
    # ==========================================================
    # TAB 4: GESTÃO DE VÍNCULOS
    # ==========================================================
    with tab4:
        st.header("🔗 Gestão de Vínculos")
        
        st.subheader("➕ Criar Novo Vínculo")
        
        with st.form("form_vinculo"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👨‍🎓 Selecionar Aluno:**")
                busca_aluno_vinculo = st.text_input("Nome do aluno:", key="busca_aluno_vinculo")
                
                aluno_selecionado_vinculo = None
                if busca_aluno_vinculo and len(busca_aluno_vinculo) >= 2:
                    resultado_alunos = buscar_alunos_para_dropdown(busca_aluno_vinculo)
                    if resultado_alunos.get("success") and resultado_alunos["opcoes"]:
                        opcoes_alunos = {op["label"]: op for op in resultado_alunos["opcoes"]}
                        aluno_escolhido = st.selectbox("Aluno:", list(opcoes_alunos.keys()), key="select_aluno_vinculo")
                        aluno_selecionado_vinculo = opcoes_alunos[aluno_escolhido]
            
            with col2:
                st.markdown("**👤 Selecionar Responsável:**")
                busca_resp_vinculo = st.text_input("Nome do responsável:", key="busca_resp_vinculo")
                
                resp_selecionado_vinculo = None
                if busca_resp_vinculo:
                    resultado_resps = buscar_responsaveis_para_dropdown(busca_resp_vinculo)
                    if resultado_resps.get("success") and resultado_resps["opcoes"]:
                        opcoes_resps = {op["label"]: op for op in resultado_resps["opcoes"]}
                        resp_escolhido = st.selectbox("Responsável:", list(opcoes_resps.keys()), key="select_resp_vinculo")
                        resp_selecionado_vinculo = opcoes_resps[resp_escolhido]
            
            # Configurações do vínculo
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_relacao = st.selectbox(
                    "Tipo de Relação:",
                    ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"],
                    key="tipo_relacao_vinculo"
                )
            
            with col2:
                responsavel_financeiro = st.checkbox("É responsável financeiro", key="resp_financeiro_vinculo")
            
            if st.form_submit_button("🔗 Criar Vínculo", type="primary"):
                if aluno_selecionado_vinculo and resp_selecionado_vinculo:
                    resultado = vincular_aluno_responsavel(
                        aluno_selecionado_vinculo["id"],
                        resp_selecionado_vinculo["id"],
                        tipo_relacao,
                        responsavel_financeiro
                    )
                    
                    mostrar_resultado(resultado, "Criação de vínculo")
                else:
                    st.error("Selecione um aluno e um responsável")
    
    # ==========================================================
    # TAB 5: CADASTROS
    # ==========================================================
    with tab5:
        st.header("📝 Cadastros")
        
        sub_tab1, sub_tab2 = st.tabs(["👨‍🎓 Cadastrar Aluno", "👤 Cadastrar Responsável"])
        
        # Cadastro de Aluno
        with sub_tab1:
            st.subheader("👨‍🎓 Cadastrar Novo Aluno")
            
            mostrar_formulario_cadastro_aluno()
        
        # Cadastro de Responsável
        with sub_tab2:
            st.subheader("👤 Cadastrar Novo Responsável")
            
            mostrar_formulario_cadastro_responsavel()
    
    # ==========================================================
    # TAB 6: GESTÃO DE COBRANÇAS
    # ==========================================================
    with tab6:
        st.header("💰 Gestão de Cobranças")
        
        # Sub-tabs para organizar funcionalidades
        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
            "➕ Criar Cobranças",
            "📋 Gerenciar Cobranças",
            "👨‍🎓 Vincular Alunos",
            "📊 Relatórios de Cobranças"
        ])
        
        # SUB-TAB 1: CRIAR COBRANÇAS
        with sub_tab1:
            mostrar_interface_criar_cobrancas()
        
        # SUB-TAB 2: GERENCIAR COBRANÇAS  
        with sub_tab2:
            mostrar_interface_gerenciar_cobrancas()
        
        # SUB-TAB 3: VINCULAR ALUNOS
        with sub_tab3:
            mostrar_interface_vincular_alunos_cobrancas()
        
        # SUB-TAB 4: RELATÓRIOS
        with sub_tab4:
            mostrar_interface_relatorios_cobrancas()
    
    # ==========================================================
    # TAB 7: RELATÓRIOS
    # ==========================================================
    with tab7:
        st.header("📊 Relatórios e Geração de Documentos")
        
        # Importar funções de relatórios
        try:
            from funcoes_relatorios import (
                gerar_relatorio_interface,
                obter_campos_disponiveis,
                limpar_arquivos_temporarios,
                DOCX_AVAILABLE,
                OPENAI_AVAILABLE
            )
            relatorios_disponivel = True
        except ImportError as e:
            st.error(f"❌ Erro ao importar módulo de relatórios: {e}")
            relatorios_disponivel = False
        
        if not relatorios_disponivel:
            st.warning("⚠️ Módulo de relatórios não disponível")
            st.info("💡 Certifique-se de que o arquivo funcoes_relatorios.py está presente")
            return
        
        # Verificar dependências
        if not DOCX_AVAILABLE:
            st.error("❌ python-docx não instalado")
            st.info("💡 Execute: pip install python-docx")
            return
        
        # Status das dependências
        col_dep1, col_dep2, col_dep3 = st.columns(3)
        
        with col_dep1:
            if DOCX_AVAILABLE:
                st.success("✅ python-docx disponível")
            else:
                st.error("❌ python-docx não disponível")
        
        with col_dep2:
            if OPENAI_AVAILABLE:
                st.success("✅ OpenAI disponível")
            else:
                st.warning("⚠️ OpenAI não disponível")
        
        with col_dep3:
            if os.getenv("OPENAI_API_KEY"):
                st.success("✅ API Key configurada")
            else:
                st.warning("⚠️ API Key não configurada")
        
        # Tabs de tipos de relatórios
        tab_pedagogico, tab_financeiro, tab_historico = st.tabs([
            "🎓 Relatório Pedagógico",
            "💰 Relatório Financeiro", 
            "📋 Histórico de Relatórios"
        ])
        
        # ==========================================================
        # RELATÓRIO PEDAGÓGICO
        # ==========================================================
        with tab_pedagogico:
            st.subheader("🎓 Relatório Pedagógico")
            st.info("Gera relatório com dados dos alunos e responsáveis das turmas selecionadas")
            
            # Seleção de turmas
            st.markdown("### 🎓 Seleção de Turmas")
            turmas_resultado = listar_turmas_disponiveis()
            
            if turmas_resultado.get("success"):
                turmas_selecionadas_ped = st.multiselect(
                    "Selecione as turmas para o relatório:",
                    options=turmas_resultado["turmas"],
                    help="Selecione uma ou mais turmas"
                )
            else:
                st.error("Erro ao carregar turmas")
                turmas_selecionadas_ped = []
            
            # Seleção de campos
            st.markdown("### 📋 Seleção de Campos")
            
            campos_disponiveis = obter_campos_disponiveis()
            
            col_aluno, col_responsavel = st.columns(2)
            
            with col_aluno:
                st.markdown("**👨‍🎓 Campos do Aluno:**")
                campos_aluno_selecionados = []
                
                for campo, descricao in campos_disponiveis["aluno"].items():
                    if st.checkbox(descricao, key=f"ped_aluno_{campo}", value=(campo == 'nome')):
                        campos_aluno_selecionados.append(campo)
            
            with col_responsavel:
                st.markdown("**👥 Campos do Responsável:**")
                campos_responsavel_selecionados = []
                
                for campo, descricao in campos_disponiveis["responsavel"].items():
                    if st.checkbox(descricao, key=f"ped_resp_{campo}"):
                        campos_responsavel_selecionados.append(campo)
            
            # Visualizar seleção
            if campos_aluno_selecionados or campos_responsavel_selecionados:
                st.markdown("### 👀 Campos Selecionados")
                
                col_preview1, col_preview2 = st.columns(2)
                
                with col_preview1:
                    if campos_aluno_selecionados:
                        st.success(f"**👨‍🎓 Aluno:** {len(campos_aluno_selecionados)} campos")
                        for campo in campos_aluno_selecionados:
                            st.write(f"   ✅ {campos_disponiveis['aluno'][campo]}")
                
                with col_preview2:
                    if campos_responsavel_selecionados:
                        st.success(f"**👥 Responsável:** {len(campos_responsavel_selecionados)} campos")
                        for campo in campos_responsavel_selecionados:
                            st.write(f"   ✅ {campos_disponiveis['responsavel'][campo]}")
            
            # Botão de geração
            st.markdown("---")
            
            if st.button("📊 Gerar Relatório Pedagógico", type="primary", use_container_width=True):
                if not turmas_selecionadas_ped:
                    st.error("❌ Selecione pelo menos uma turma")
                elif not (campos_aluno_selecionados or campos_responsavel_selecionados):
                    st.error("❌ Selecione pelo menos um campo")
                else:
                    # Combinar campos selecionados
                    todos_campos = campos_aluno_selecionados + campos_responsavel_selecionados
                    
                    # Configuração do relatório
                    configuracao = {
                        'turmas_selecionadas': turmas_selecionadas_ped,
                        'campos_selecionados': todos_campos
                    }
                    
                    # Gerar relatório
                    with st.spinner("🤖 Gerando relatório pedagógico..."):
                        resultado = gerar_relatorio_interface('pedagogico', configuracao)
                    
                    if resultado.get("success"):
                        st.success("✅ Relatório gerado com sucesso!")
                        
                        # Informações do relatório
                        col_info1, col_info2, col_info3 = st.columns(3)
                        
                        with col_info1:
                            st.metric("👨‍🎓 Total de Alunos", resultado["total_alunos"])
                        
                        with col_info2:
                            st.metric("🎓 Turmas", len(resultado["turmas_incluidas"]))
                        
                        with col_info3:
                            st.metric("📋 Campos", len(resultado["campos_selecionados"]))
                        
                        # Botão de download
                        if os.path.exists(resultado["arquivo"]):
                            with open(resultado["arquivo"], "rb") as file:
                                st.download_button(
                                    label="📥 Baixar Relatório (.docx)",
                                    data=file.read(),
                                    file_name=resultado["nome_arquivo"],
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    type="primary",
                                    use_container_width=True
                                )
                        
                        # Salvar no histórico
                        adicionar_historico("Geração de Relatório Pedagógico", resultado)
                    
                    else:
                        st.error(f"❌ Erro na geração: {resultado.get('error')}")
        
        # ==========================================================
        # RELATÓRIO FINANCEIRO
        # ==========================================================
        with tab_financeiro:
            st.subheader("💰 Relatório Financeiro")
            st.info("Gera relatório financeiro com dados de alunos, mensalidades, pagamentos e extrato PIX")
            
            # Seleção de turmas
            st.markdown("### 🎓 Seleção de Turmas")
            if turmas_resultado.get("success"):
                turmas_selecionadas_fin = st.multiselect(
                    "Selecione as turmas para o relatório financeiro:",
                    options=turmas_resultado["turmas"],
                    help="Selecione uma ou mais turmas",
                    key="turmas_fin"
                )
            else:
                st.error("Erro ao carregar turmas")
                turmas_selecionadas_fin = []
            
            # Seleção de campos por categoria
            st.markdown("### 📋 Seleção de Dados")
            
            # Campos básicos (aluno + responsável)
            col_basic1, col_basic2 = st.columns(2)
            
            with col_basic1:
                st.markdown("**👨‍🎓 Dados do Aluno:**")
                incluir_aluno = st.checkbox("Incluir dados do aluno", value=True, key="fin_aluno")
                
                if incluir_aluno:
                    campos_aluno_fin = []
                    for campo, descricao in campos_disponiveis["aluno"].items():
                        if st.checkbox(descricao, key=f"fin_aluno_{campo}", value=(campo == 'nome')):
                            campos_aluno_fin.append(campo)
                else:
                    campos_aluno_fin = []
            
            with col_basic2:
                st.markdown("**👥 Dados do Responsável:**")
                incluir_responsavel = st.checkbox("Incluir dados do responsável", key="fin_responsavel")
                
                if incluir_responsavel:
                    campos_responsavel_fin = []
                    for campo, descricao in campos_disponiveis["responsavel"].items():
                        if st.checkbox(descricao, key=f"fin_resp_{campo}"):
                            campos_responsavel_fin.append(campo)
                else:
                    campos_responsavel_fin = []
            
            # Dados financeiros específicos
            st.markdown("---")
            col_fin1, col_fin2, col_fin3 = st.columns(3)
            
            with col_fin1:
                st.markdown("**📅 Mensalidades:**")
                incluir_mensalidades = st.checkbox("Incluir mensalidades", key="fin_mensalidades")
                
                if incluir_mensalidades:
                    st.markdown("**Status das Mensalidades:**")
                    status_mensalidades = []
                    
                    for status in ['A vencer', 'Pago', 'Atrasado', 'Cancelado', 'Baixado']:
                        if st.checkbox(status, key=f"status_mens_{status}"):
                            status_mensalidades.append(status)
                    
                    campos_mensalidade_fin = []
                    for campo, descricao in campos_disponiveis["mensalidade"].items():
                        if st.checkbox(descricao, key=f"fin_mens_{campo}"):
                            campos_mensalidade_fin.append(campo)
                else:
                    status_mensalidades = []
                    campos_mensalidade_fin = []
            
            with col_fin2:
                st.markdown("**💳 Pagamentos:**")
                incluir_pagamentos = st.checkbox("Incluir pagamentos", key="fin_pagamentos")
                
                if incluir_pagamentos:
                    campos_pagamento_fin = []
                    for campo, descricao in campos_disponiveis["pagamento"].items():
                        if st.checkbox(descricao, key=f"fin_pag_{campo}"):
                            campos_pagamento_fin.append(campo)
                else:
                    campos_pagamento_fin = []
            
            with col_fin3:
                st.markdown("**📊 Extrato PIX:**")
                incluir_extrato = st.checkbox("Incluir extrato PIX", key="fin_extrato")
                
                if incluir_extrato:
                    st.markdown("**Status do Extrato:**")
                    incluir_processados = st.checkbox("Processados", key="extrato_processados")
                    incluir_nao_processados = st.checkbox("Não Processados", key="extrato_nao_processados")
                    
                    campos_extrato_fin = []
                    for campo, descricao in campos_disponiveis["extrato_pix"].items():
                        if st.checkbox(descricao, key=f"fin_ext_{campo}"):
                            campos_extrato_fin.append(campo)
                else:
                    incluir_processados = False
                    incluir_nao_processados = False
                    campos_extrato_fin = []
            
            # Filtro de período
            st.markdown("---")
            st.markdown("### 📅 Filtro de Período")
            
            usar_filtro_periodo = st.checkbox("Aplicar filtro de período", key="usar_periodo")
            
            if usar_filtro_periodo:
                col_data1, col_data2 = st.columns(2)
                
                with col_data1:
                    data_inicio = st.date_input("Data de Início:", key="data_inicio_fin")
                
                with col_data2:
                    data_fim = st.date_input("Data de Fim:", key="data_fim_fin")
            else:
                data_inicio = None
                data_fim = None
            
            # Visualizar seleção
            st.markdown("### 👀 Resumo da Seleção")
            
            total_campos = len(campos_aluno_fin) + len(campos_responsavel_fin) + len(campos_mensalidade_fin) + len(campos_pagamento_fin) + len(campos_extrato_fin)
            
            col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
            
            with col_resumo1:
                st.metric("📋 Total de Campos", total_campos)
            
            with col_resumo2:
                categorias_incluidas = sum([
                    1 if campos_aluno_fin else 0,
                    1 if campos_responsavel_fin else 0,
                    1 if campos_mensalidade_fin else 0,
                    1 if campos_pagamento_fin else 0,
                    1 if campos_extrato_fin else 0
                ])
                st.metric("📊 Categorias", categorias_incluidas)
            
            with col_resumo3:
                st.metric("🎓 Turmas", len(turmas_selecionadas_fin))
            
            # Botão de geração
            st.markdown("---")
            
            if st.button("💰 Gerar Relatório Financeiro", type="primary", use_container_width=True):
                if not turmas_selecionadas_fin:
                    st.error("❌ Selecione pelo menos uma turma")
                elif total_campos == 0:
                    st.error("❌ Selecione pelo menos um campo")
                else:
                    # Combinar todos os campos
                    todos_campos_fin = campos_aluno_fin + campos_responsavel_fin + campos_mensalidade_fin + campos_pagamento_fin + campos_extrato_fin
                    
                    # Configurar filtros
                    filtros = {}
                    
                    if usar_filtro_periodo:
                        if data_inicio:
                            filtros['periodo_inicio'] = data_inicio.isoformat()
                        if data_fim:
                            filtros['periodo_fim'] = data_fim.isoformat()
                    
                    if incluir_mensalidades and status_mensalidades:
                        filtros['status_mensalidades'] = status_mensalidades
                    
                    if incluir_extrato:
                        filtros['extrato_pix_processados'] = incluir_processados
                        filtros['extrato_pix_nao_processados'] = incluir_nao_processados
                    
                    # Configuração do relatório
                    configuracao = {
                        'turmas_selecionadas': turmas_selecionadas_fin,
                        'campos_selecionados': todos_campos_fin,
                        'filtros': filtros
                    }
                    
                    # Gerar relatório
                    with st.spinner("🤖 Gerando relatório financeiro..."):
                        resultado = gerar_relatorio_interface('financeiro', configuracao)
                    
                    if resultado.get("success"):
                        st.success("✅ Relatório financeiro gerado com sucesso!")
                        
                        # Informações do relatório
                        col_info1, col_info2, col_info3 = st.columns(3)
                        
                        with col_info1:
                            st.metric("👨‍🎓 Total de Alunos", resultado["total_alunos"])
                        
                        with col_info2:
                            st.metric("🎓 Turmas", len(resultado["turmas_incluidas"]))
                        
                        with col_info3:
                            st.metric("📋 Campos", len(resultado["campos_selecionados"]))
                        
                        # Mostrar filtros aplicados
                        if resultado.get("filtros_aplicados"):
                            st.info(f"🔍 Filtros aplicados: {len(resultado['filtros_aplicados'])}")
                        
                        # Botão de download
                        if os.path.exists(resultado["arquivo"]):
                            with open(resultado["arquivo"], "rb") as file:
                                st.download_button(
                                    label="📥 Baixar Relatório Financeiro (.docx)",
                                    data=file.read(),
                                    file_name=resultado["nome_arquivo"],
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    type="primary",
                                    use_container_width=True
                                )
                        
                        # Salvar no histórico
                        adicionar_historico("Geração de Relatório Financeiro", resultado)
                    
                    else:
                        st.error(f"❌ Erro na geração: {resultado.get('error')}")
        
        # ==========================================================
        # HISTÓRICO DE RELATÓRIOS
        # ==========================================================
        with tab_historico:
            st.subheader("📋 Histórico de Relatórios Gerados")
            
            # Filtrar apenas operações de relatórios
            relatorios_historico = [
                op for op in st.session_state.historico_operacoes 
                if 'relatório' in op['operacao'].lower()
            ]
            
            if relatorios_historico:
                st.success(f"📊 **{len(relatorios_historico)} relatórios** gerados nesta sessão")
                
                # Botão para limpar arquivos antigos
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("🧹 Limpar Arquivos Temporários", help="Remove relatórios com mais de 24h"):
                        limpar_arquivos_temporarios()
                        st.success("✅ Limpeza executada")
                
                with col_btn2:
                    if st.button("🔄 Atualizar Lista"):
                        st.rerun()
                
                # Lista de relatórios
                st.markdown("### 📄 Relatórios Gerados")
                
                for i, relatorio in enumerate(reversed(relatorios_historico), 1):
                    timestamp = relatorio['timestamp'].strftime("%d/%m/%Y %H:%M:%S")
                    detalhes = relatorio.get('detalhes', {})
                    
                    with st.expander(f"📊 {i}. {relatorio['operacao']} - {timestamp}", expanded=False):
                        col_det1, col_det2 = st.columns(2)
                        
                        with col_det1:
                            if detalhes.get('titulo'):
                                st.write(f"**📋 Título:** {detalhes['titulo']}")
                            if detalhes.get('total_alunos'):
                                st.write(f"**👨‍🎓 Alunos:** {detalhes['total_alunos']}")
                            if detalhes.get('turmas_incluidas'):
                                st.write(f"**🎓 Turmas:** {', '.join(detalhes['turmas_incluidas'])}")
                        
                        with col_det2:
                            if detalhes.get('campos_selecionados'):
                                st.write(f"**📋 Campos:** {len(detalhes['campos_selecionados'])}")
                            if detalhes.get('arquivo'):
                                st.write(f"**📁 Arquivo:** {detalhes.get('nome_arquivo', 'N/A')}")
                                
                                # Verificar se arquivo ainda existe
                                if os.path.exists(detalhes['arquivo']):
                                    with open(detalhes['arquivo'], "rb") as file:
                                        st.download_button(
                                            label="📥 Baixar Novamente",
                                            data=file.read(),
                                            file_name=detalhes.get('nome_arquivo', 'relatorio.docx'),
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                            key=f"download_hist_{i}"
                                        )
                                else:
                                    st.warning("⚠️ Arquivo não encontrado (pode ter sido removido)")
            else:
                st.info("ℹ️ Nenhum relatório gerado ainda nesta sessão")
                st.info("💡 Use as abas acima para gerar relatórios pedagógicos ou financeiros")
        
        # Estatísticas gerais (mantidas da versão anterior)
        st.markdown("---")
        st.markdown("### 📊 Estatísticas Gerais")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if turmas_resultado.get("success"):
                st.metric("🎓 Turmas Disponíveis", turmas_resultado["count"])
            else:
                st.metric("🎓 Turmas", "Erro")
        
        with col2:
            # Contar relatórios gerados
            total_relatorios = len([op for op in st.session_state.historico_operacoes if 'relatório' in op['operacao'].lower()])
            st.metric("📊 Relatórios Gerados", total_relatorios)
        
        with col3:
            # Status do sistema
            if DOCX_AVAILABLE and relatorios_disponivel:
                st.metric("✅ Sistema", "Operacional")
            else:
                st.metric("⚠️ Sistema", "Dependências")

# ==========================================================
# 🔧 FUNÇÕES DE INTERFACE
# ==========================================================

def mostrar_detalhes_aluno(id_aluno: str):
    """Mostra detalhes completos e editáveis do aluno com TODAS as funcionalidades"""
    st.markdown("## 👨‍🎓 Informações Completas do Aluno")
    
    with st.spinner("Carregando informações completas..."):
        resultado = buscar_informacoes_completas_aluno(id_aluno)
    
    if not resultado.get("success"):
        st.error(f"❌ Erro ao carregar informações: {resultado.get('error')}")
        return
    
    aluno = resultado["aluno"]
    responsaveis = resultado["responsaveis"]
    pagamentos = resultado["pagamentos"]
    mensalidades = resultado["mensalidades"]
    estatisticas = resultado["estatisticas"]
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Responsáveis", estatisticas["total_responsaveis"])
    
    with col2:
        st.metric("💳 Pagamentos", estatisticas["total_pagamentos"], 
                 delta=f"R$ {estatisticas['total_pago']:,.2f}")
    
    with col3:
        st.metric("📅 Mensalidades", estatisticas["total_mensalidades"],
                 delta=f"{estatisticas['mensalidades_pagas']} pagas")
    
    with col4:
        if estatisticas["mensalidades_vencidas"] > 0:
            st.metric("⚠️ Vencidas", estatisticas["mensalidades_vencidas"], 
                     delta="Atenção", delta_color="inverse")
        else:
            st.metric("✅ Situação", "Em dia", delta="OK")
    
    # Tabs para organizar informações
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Dados do Aluno", 
        "👥 Responsáveis", 
        "💰 Pagamentos", 
        "📊 Extrato PIX",
        "📅 Mensalidades",
        "💰 Cobranças"
    ])
    
    # TAB 1: Dados do Aluno (EDITÁVEIS)
    with tab1:
        mostrar_dados_editaveis_aluno(aluno)
    
    # TAB 2: Responsáveis (EDITÁVEIS + CADASTRO + VINCULAÇÃO)
    with tab2:
        mostrar_gestao_responsaveis_completa(id_aluno, responsaveis)
    
    # TAB 3: Pagamentos Registrados
    with tab3:
        mostrar_pagamentos_aluno(pagamentos, estatisticas)
    
    # TAB 4: Extrato PIX (PROCESSÁVEL)
    with tab4:
        mostrar_extrato_pix_aluno(id_aluno, responsaveis)
    
    # TAB 5: Mensalidades
    with tab5:
        mostrar_mensalidades_aluno(mensalidades, estatisticas, id_aluno)
    
    # TAB 6: Cobranças
    with tab6:
        mostrar_cobrancas_aluno(id_aluno, responsaveis)
    
    # Botões de ação globais
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("❌ Fechar", use_container_width=True):
            st.session_state.aluno_selecionado = None
            if 'modo_edicao' in st.session_state:
                del st.session_state.modo_edicao
            if 'modo_gestao_responsaveis' in st.session_state:
                del st.session_state.modo_gestao_responsaveis
            st.rerun()

def mostrar_detalhes_responsavel(id_responsavel: str):
    """Mostra detalhes completos e editáveis do responsável"""
    st.markdown("## 👤 Informações Completas do Responsável")
    
    with st.spinner("Carregando informações do responsável..."):
        # Buscar dados do responsável
        from models.pedagogico import supabase
        resp_response = supabase.table("responsaveis").select("*").eq("id", id_responsavel).execute()
        
        if not resp_response.data:
            st.error("❌ Responsável não encontrado")
            return
        
        responsavel = resp_response.data[0]
        
        # Buscar alunos vinculados
        resultado_alunos = listar_alunos_vinculados_responsavel(id_responsavel)
    
    if resultado_alunos.get("success"):
        alunos = resultado_alunos["alunos"]
        
        # Métricas principais
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👨‍🎓 Alunos Vinculados", len(alunos))
        
        with col2:
            responsavel_financeiro_count = sum(1 for a in alunos if a['responsavel_financeiro'])
            st.metric("💰 Resp. Financeiro", responsavel_financeiro_count)
        
        with col3:
            valor_total_mensalidades = sum(float(a.get('valor_mensalidade', 0)) for a in alunos)
            st.metric("💵 Total Mensalidades", f"R$ {valor_total_mensalidades:,.2f}")
        
        # Tabs para organizar informações
        tab1, tab2, tab3 = st.tabs([
            "📋 Dados do Responsável",
            "👨‍🎓 Alunos Vinculados", 
            "💰 Informações Financeiras"
        ])
        
        # TAB 1: Dados do Responsável (EDITÁVEIS)
        with tab1:
            st.markdown("### 👤 Informações Pessoais")
            
            # Exibir dados atuais
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**🆔 ID:** {responsavel['id']}")
                st.info(f"**📖 Nome:** {responsavel['nome']}")
                st.info(f"**📱 Telefone:** {responsavel.get('telefone', 'Não informado')}")
                st.info(f"**📧 Email:** {responsavel.get('email', 'Não informado')}")
            
            with col2:
                st.info(f"**📄 CPF:** {responsavel.get('cpf', 'Não informado')}")
                st.info(f"**📍 Endereço:** {responsavel.get('endereco', 'Não informado')}")
                st.info(f"**📅 Cadastrado:** {responsavel.get('inserted_at', 'N/A')}")
                st.info(f"**🔄 Atualizado:** {responsavel.get('updated_at', 'N/A')}")
            
            # Formulário de edição
            st.markdown("---")
            st.markdown("### ✏️ Editar Informações")
            
            with st.form("form_edicao_responsavel"):
                col1, col2 = st.columns(2)
                
                with col1:
                    novo_telefone = st.text_input("📱 Telefone:", value=responsavel.get('telefone', ''))
                    novo_email = st.text_input("📧 Email:", value=responsavel.get('email', ''))
                
                with col2:
                    novo_cpf = st.text_input("📄 CPF:", value=responsavel.get('cpf', ''))
                    novo_endereco = st.text_area("📍 Endereço:", value=responsavel.get('endereco', ''))
                
                if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                    campos_update = {
                        "telefone": novo_telefone if novo_telefone else None,
                        "email": novo_email if novo_email else None,
                        "cpf": novo_cpf if novo_cpf else None,
                        "endereco": novo_endereco if novo_endereco else None
                    }
                    
                    resultado_update = atualizar_responsavel_campos(responsavel['id'], campos_update)
                    
                    if resultado_update.get("success"):
                        st.success("✅ Dados do responsável atualizados com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"❌ Erro ao atualizar: {resultado_update.get('error')}")
        
        # TAB 2: Alunos Vinculados
        with tab2:
            if alunos:
                st.markdown(f"### 👨‍🎓 {len(alunos)} Alunos Vinculados")
                
                for i, aluno in enumerate(alunos, 1):
                    with st.expander(f"👨‍🎓 {i}. {aluno['nome']} - {aluno['turmas']['nome_turma']}", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**🆔 ID:** {aluno['id']}")
                            st.write(f"**🎓 Turma:** {aluno['turmas']['nome_turma']}")
                            st.write(f"**🕐 Turno:** {aluno.get('turno', 'Não informado')}")
                            st.write(f"**📅 Nascimento:** {aluno.get('data_nascimento', 'Não informado')}")
                        
                        with col2:
                            st.write(f"**💰 Mensalidade:** R$ {float(aluno.get('valor_mensalidade', 0)):,.2f}")
                            st.write(f"**📆 Vencimento:** Dia {aluno.get('dia_vencimento', 'N/A')}")
                            st.write(f"**🎯 Matrícula:** {aluno.get('data_matricula', 'Não informado')}")
                        
                        with col3:
                            st.write(f"**👨‍👩‍👧‍👦 Relação:** {aluno['tipo_relacao']}")
                            
                            if aluno['responsavel_financeiro']:
                                st.success("💰 Responsável Financeiro")
                            else:
                                st.info("👥 Responsável Geral")
                            
                            # Botão para ver detalhes do aluno
                            if st.button(f"👁️ Ver Detalhes do Aluno", key=f"ver_aluno_{aluno['id']}"):
                                st.session_state.aluno_selecionado = aluno['id']
                                st.session_state.responsavel_selecionado = None
                                st.rerun()
            else:
                st.warning("⚠️ Nenhum aluno vinculado a este responsável")
                st.info("💡 Use a gestão de vínculos para associar alunos a este responsável")
        
        # TAB 3: Informações Financeiras
        with tab3:
            if alunos:
                st.markdown("### 💰 Resumo Financeiro")
                
                # Calcular totais
                total_mensalidades = sum(float(a.get('valor_mensalidade', 0)) for a in alunos)
                alunos_responsavel_financeiro = [a for a in alunos if a['responsavel_financeiro']]
                total_responsabilidade_financeira = sum(float(a.get('valor_mensalidade', 0)) for a in alunos_responsavel_financeiro)
                
                # Métricas financeiras
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💵 Total Mensalidades", f"R$ {total_mensalidades:,.2f}")
                
                with col2:
                    st.metric("💰 Responsabilidade Financeira", f"R$ {total_responsabilidade_financeira:,.2f}")
                
                with col3:
                    percentual_responsabilidade = (total_responsabilidade_financeira / total_mensalidades * 100) if total_mensalidades > 0 else 0
                    st.metric("📊 % Responsabilidade", f"{percentual_responsabilidade:.1f}%")
                
                # Lista detalhada por aluno
                st.markdown("#### 📋 Detalhamento por Aluno")
                
                dados_financeiros = []
                for aluno in alunos:
                    dados_financeiros.append({
                        "Aluno": aluno['nome'],
                        "Turma": aluno['turmas']['nome_turma'],
                        "Mensalidade": f"R$ {float(aluno.get('valor_mensalidade', 0)):,.2f}",
                        "Vencimento": f"Dia {aluno.get('dia_vencimento', 'N/A')}",
                        "Resp. Financeiro": "✅ Sim" if aluno['responsavel_financeiro'] else "❌ Não",
                        "Tipo Relação": aluno['tipo_relacao']
                    })
                
                df_financeiro = pd.DataFrame(dados_financeiros)
                st.dataframe(df_financeiro, use_container_width=True, height=300)
            else:
                st.info("ℹ️ Nenhuma informação financeira disponível - nenhum aluno vinculado")
        
        # Botões de ação globais
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🔄 Atualizar Dados", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("❌ Fechar", use_container_width=True):
                st.session_state.responsavel_selecionado = None
                if 'modo_edicao_resp' in st.session_state:
                    del st.session_state.modo_edicao_resp
                st.rerun()
    
    else:
        st.error(f"❌ Erro ao carregar alunos vinculados: {resultado_alunos.get('error')}")

def mostrar_formulario_cadastro_aluno():
    """Formulário para cadastrar novo aluno"""
    with st.form("form_cadastro_aluno"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo*", key="nome_aluno")
            
            # Carregar turmas
            turmas_resultado = listar_turmas_disponiveis()
            if turmas_resultado.get("success"):
                turma_selecionada = st.selectbox(
                    "Turma*",
                    options=["Selecionar..."] + turmas_resultado["turmas"],
                    key="turma_aluno"
                )
            
            turno = st.selectbox("Turno*", ["Manhã", "Tarde", "Integral", "Horário Extendido"], key="turno_aluno")
            data_nascimento = st.date_input("Data de Nascimento", key="data_nasc_aluno")
        
        with col2:
            dia_vencimento = st.selectbox("Dia de Vencimento", list(range(1, 32)), index=4, key="dia_venc_aluno")
            valor_mensalidade = st.number_input("Valor da Mensalidade (R$)", min_value=0.0, step=10.0, key="valor_mens_aluno")
            
            st.markdown("**👤 Vincular Responsável (Opcional):**")
            busca_resp_aluno = st.text_input("Nome do responsável:", key="busca_resp_aluno")
            
            responsavel_selecionado = None
            if busca_resp_aluno:
                resultado_busca = buscar_responsaveis_para_dropdown(busca_resp_aluno)
                if resultado_busca.get("success") and resultado_busca["opcoes"]:
                    opcoes_resp = {op["label"]: op for op in resultado_busca["opcoes"]}
                    resp_escolhido = st.selectbox("Responsável:", ["Não vincular"] + list(opcoes_resp.keys()), key="select_resp_aluno")
                    if resp_escolhido != "Não vincular":
                        responsavel_selecionado = opcoes_resp[resp_escolhido]
            
            if responsavel_selecionado:
                tipo_relacao = st.selectbox("Tipo de Relação:", ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"], key="tipo_rel_aluno")
                responsavel_financeiro = st.checkbox("É responsável financeiro", value=True, key="resp_fin_aluno")
        
        if st.form_submit_button("👨‍🎓 Cadastrar Aluno", type="primary"):
            if not nome:
                st.error("Nome é obrigatório!")
                return
            
            if turma_selecionada == "Selecionar...":
                st.error("Selecione uma turma!")
                return
            
            # Obter ID da turma
            mapeamento_resultado = obter_mapeamento_turmas()
            if not mapeamento_resultado.get("success"):
                st.error("Erro ao obter mapeamento de turmas")
                return
            
            id_turma = mapeamento_resultado["mapeamento"].get(turma_selecionada)
            if not id_turma:
                st.error("Turma não encontrada")
                return
            
            # Preparar dados do aluno
            dados_aluno = {
                "nome": nome,
                "id_turma": id_turma,
                "turno": turno,
                "data_nascimento": data_nascimento.isoformat() if data_nascimento else None,
                "dia_vencimento": str(dia_vencimento),
                "valor_mensalidade": valor_mensalidade if valor_mensalidade > 0 else None
            }
            
            # Cadastrar aluno
            resultado = cadastrar_aluno_e_vincular(
                dados_aluno=dados_aluno,
                id_responsavel=responsavel_selecionado["id"] if responsavel_selecionado else None,
                tipo_relacao=tipo_relacao if responsavel_selecionado else "responsavel",
                responsavel_financeiro=responsavel_financeiro if responsavel_selecionado else True
            )
            
            if mostrar_resultado(resultado, "Cadastro de aluno"):
                st.rerun()

def mostrar_formulario_cadastro_responsavel():
    """Formulário para cadastrar novo responsável"""
    with st.form("form_cadastro_responsavel"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo*", key="nome_resp")
            cpf = st.text_input("CPF", key="cpf_resp")
            telefone = st.text_input("Telefone", key="telefone_resp")
        
        with col2:
            email = st.text_input("Email", key="email_resp")
            endereco = st.text_area("Endereço", key="endereco_resp")
            
            st.markdown("**👨‍🎓 Vincular a Aluno (Opcional):**")
            busca_aluno_resp = st.text_input("Nome do aluno:", key="busca_aluno_resp")
            
            aluno_selecionado = None
            if busca_aluno_resp and len(busca_aluno_resp) >= 2:
                resultado_busca = buscar_alunos_para_dropdown(busca_aluno_resp)
                if resultado_busca.get("success") and resultado_busca["opcoes"]:
                    opcoes_aluno = {op["label"]: op for op in resultado_busca["opcoes"]}
                    aluno_escolhido = st.selectbox("Aluno:", ["Não vincular"] + list(opcoes_aluno.keys()), key="select_aluno_resp")
                    if aluno_escolhido != "Não vincular":
                        aluno_selecionado = opcoes_aluno[aluno_escolhido]
            
            if aluno_selecionado:
                tipo_relacao = st.selectbox("Tipo de Relação:", ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"], key="tipo_rel_resp")
                responsavel_financeiro = st.checkbox("É responsável financeiro", value=True, key="resp_fin_resp")
        
        if st.form_submit_button("👤 Cadastrar Responsável", type="primary"):
            if not nome:
                st.error("Nome é obrigatório!")
                return
            
            if aluno_selecionado:
                # Cadastrar responsável e vincular
                dados_responsavel = {
                    "nome": nome,
                    "cpf": cpf if cpf else None,
                    "telefone": telefone if telefone else None,
                    "email": email if email else None,
                    "endereco": endereco if endereco else None
                }
                
                resultado = cadastrar_responsavel_e_vincular(
                    dados_responsavel=dados_responsavel,
                    id_aluno=aluno_selecionado["id"],
                    tipo_relacao=tipo_relacao,
                    responsavel_financeiro=responsavel_financeiro
                )
                
                if mostrar_resultado(resultado, "Cadastro de responsável com vínculo"):
                    st.rerun()
            else:
                st.warning("Implementar cadastro de responsável sem vínculo")

def mostrar_dados_editaveis_aluno(aluno: Dict):
    """Exibe e permite edição de todos os dados do aluno"""
    st.markdown("### 📚 Informações Acadêmicas e Financeiras")
    
    # Verificar situação do aluno
    situacao_atual = aluno.get('situacao', 'ativo')
    is_trancado = situacao_atual == 'trancado'
    
    # Exibição atual
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 Dados Básicos:**")
        st.info(f"**🆔 ID:** {aluno['id']}")
        st.info(f"**📖 Nome:** {aluno['nome']}")
        st.info(f"**🎓 Turma:** {aluno['turma_nome']}")
        st.info(f"**🕐 Turno:** {aluno.get('turno', 'Não informado')}")
        st.info(f"**📅 Data Nascimento:** {aluno.get('data_nascimento', 'Não informado')}")
        st.info(f"**🎯 Data Matrícula:** {aluno.get('data_matricula', 'Não informado')}")
    
    with col2:
        st.markdown("**💰 Dados Financeiros:**")
        st.info(f"**💵 Valor Mensalidade:** R$ {aluno['valor_mensalidade']:.2f}")
        st.info(f"**📆 Dia Vencimento:** {aluno.get('dia_vencimento', 'Não definido')}")
        st.info(f"**📊 Mensalidades Geradas:** {'Sim' if aluno.get('mensalidades_geradas') else 'Não'}")
        
        # Mostrar situação da matrícula
        if is_trancado:
            st.error(f"🔒 **MATRÍCULA TRANCADA**")
            if aluno.get('data_saida'):
                st.error(f"📅 Data de Saída: {formatar_data_br(aluno['data_saida'])}")
            if aluno.get('motivo_saida'):
                st.error(f"📝 Motivo: {aluno['motivo_saida']}")
        else:
            st.success("✅ **MATRÍCULA ATIVA**")
    
    # Seção de trancamento de matrícula
    if not is_trancado:
        st.markdown("---")
        st.markdown("### 🔒 Trancamento de Matrícula")
        
        # Botão para iniciar processo de trancamento
        if st.button("❌ TRANCAR MATRÍCULA", type="secondary", use_container_width=True):
            st.session_state[f'trancar_matricula_{aluno["id"]}'] = True
        
        # Interface de trancamento
        if st.session_state.get(f'trancar_matricula_{aluno["id"]}', False):
            st.warning("⚠️ **ATENÇÃO**: O trancamento de matrícula cancelará todas as mensalidades futuras!")
            
            with st.form(f"form_trancamento_{aluno['id']}"):
                col_tranc1, col_tranc2 = st.columns(2)
                
                with col_tranc1:
                    data_saida = st.date_input(
                        "📅 Data de Saída:",
                        help="Data em que o aluno deixará a escola",
                        key=f"data_saida_{aluno['id']}"
                    )
                    
                    motivo_saida = st.selectbox(
                        "📝 Motivo do Trancamento:",
                        ["trancamento", "transferido", "desistente", "outro"],
                        key=f"motivo_{aluno['id']}"
                    )
                
                with col_tranc2:
                    # Mostrar preview das mensalidades que serão canceladas
                    if data_saida:
                        data_saida_str = data_saida.isoformat()
                        
                        with st.spinner("Calculando mensalidades que serão canceladas..."):
                            preview_resultado = listar_mensalidades_para_cancelamento(aluno['id'], data_saida_str)
                        
                        if preview_resultado.get("success"):
                            mensalidades_preview = preview_resultado["mensalidades"]
                            
                            if mensalidades_preview:
                                st.info(f"📊 **{len(mensalidades_preview)} mensalidades serão canceladas:**")
                                for mens in mensalidades_preview[:5]:  # Mostrar apenas as primeiras 5
                                    st.write(f"   • {mens['mes_referencia']} - R$ {mens['valor']:.2f}")
                                if len(mensalidades_preview) > 5:
                                    st.write(f"   • ... e mais {len(mensalidades_preview) - 5}")
                                
                                valor_total = sum(m['valor'] for m in mensalidades_preview)
                                st.info(f"💰 **Valor total cancelado:** R$ {valor_total:,.2f}")
                            else:
                                st.success("✅ Nenhuma mensalidade futura para cancelar")
                        else:
                            st.error(f"❌ Erro ao calcular mensalidades: {preview_resultado.get('error')}")
                
                # Botões de confirmação
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.form_submit_button("🔒 CONFIRMAR TRANCAMENTO", type="primary"):
                        if not data_saida:
                            st.error("❌ Selecione a data de saída!")
                        else:
                            with st.spinner("Processando trancamento..."):
                                resultado_trancamento = trancar_matricula_aluno(
                                    aluno['id'], 
                                    data_saida.isoformat(), 
                                    motivo_saida
                                )
                            
                            if resultado_trancamento.get("success"):
                                st.success("✅ Matrícula trancada com sucesso!")
                                st.info(f"📊 {resultado_trancamento['mensalidades_canceladas']} mensalidades canceladas")
                                
                                if resultado_trancamento.get('erros_cancelamento'):
                                    st.warning(f"⚠️ {resultado_trancamento.get('aviso')}")
                                
                                # Limpar estado e recarregar
                                if f'trancar_matricula_{aluno["id"]}' in st.session_state:
                                    del st.session_state[f'trancar_matricula_{aluno["id"]}']
                                st.rerun()
                            else:
                                st.error(f"❌ Erro no trancamento: {resultado_trancamento.get('error')}")
                
                with col_btn2:
                    if st.form_submit_button("❌ CANCELAR", type="secondary"):
                        if f'trancar_matricula_{aluno["id"]}' in st.session_state:
                            del st.session_state[f'trancar_matricula_{aluno["id"]}']
                        st.rerun()
                
                with col_btn3:
                    st.write("")  # Espaço
    
    else:
        # Se está trancado, mostrar informações e opção de reativar (opcional)
        st.markdown("---")
        st.markdown("### 🔓 Matrícula Trancada")
        st.warning("ℹ️ Esta matrícula está trancada. As mensalidades futuras foram canceladas.")
        
        # Aqui poderia ser implementada uma função de reativação futuramente
        st.info("💡 Para reativar a matrícula, entre em contato com a administração.")
    
    # Formulário de edição (só aparece se não estiver trancado)
    if not is_trancado:
        st.markdown("---")
        st.markdown("### ✏️ Editar Informações")
        
        with st.form("form_edicao_aluno"):
            col1, col2 = st.columns(2)
            
            with col1:
                novo_turno = st.selectbox(
                    "🕐 Turno:",
                    ["Manhã", "Tarde", "Integral", "Horário Extendido"],
                    index=["Manhã", "Tarde", "Integral", "Horário Extendido"].index(aluno.get('turno', 'Manhã')) if aluno.get('turno') in ["Manhã", "Tarde", "Integral", "Horário Extendido"] else 0
                )
                
                nova_data_nascimento = st.date_input(
                    "📅 Data de Nascimento:",
                    value=pd.to_datetime(aluno.get('data_nascimento')).date() if aluno.get('data_nascimento') else None
                )
                
                nova_data_matricula = st.date_input(
                    "🎯 Data de Matrícula:",
                    value=pd.to_datetime(aluno.get('data_matricula')).date() if aluno.get('data_matricula') else None
                )
            
            with col2:
                novo_dia_vencimento = st.selectbox(
                    "📆 Dia de Vencimento:",
                    list(range(1, 32)),
                    index=int(aluno.get('dia_vencimento', 5)) - 1 if aluno.get('dia_vencimento') else 4
                )
                
                novo_valor_mensalidade = st.number_input(
                    "💵 Valor da Mensalidade (R$):",
                    min_value=0.0,
                    step=10.0,
                    value=float(aluno.get('valor_mensalidade', 0))
                )
                
                mensalidades_geradas = st.checkbox(
                    "📊 Mensalidades Geradas",
                    value=aluno.get('mensalidades_geradas', False)
                )
            
            if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                campos_update = {
                    "turno": novo_turno,
                    "data_nascimento": nova_data_nascimento.isoformat() if nova_data_nascimento else None,
                    "data_matricula": nova_data_matricula.isoformat() if nova_data_matricula else None,
                    "dia_vencimento": str(novo_dia_vencimento),
                    "valor_mensalidade": novo_valor_mensalidade,
                    "mensalidades_geradas": mensalidades_geradas
                }
                
                resultado = atualizar_aluno_campos(aluno["id"], campos_update)
                
                if resultado.get("success"):
                    st.success("✅ Dados do aluno atualizados com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ Erro ao atualizar: {resultado.get('error')}")
    else:
        st.info("ℹ️ Edição de dados não disponível para matrículas trancadas.")

def mostrar_gestao_responsaveis_completa(id_aluno: str, responsaveis: List[Dict]):
    """Gestão completa de responsáveis: visualizar, editar, cadastrar e vincular"""
    st.markdown("### 👥 Gestão de Responsáveis")
    
    # Seção 1: Responsáveis Atuais
    if responsaveis:
        st.markdown(f"#### 📋 Responsáveis Vinculados ({len(responsaveis)})")
        
        for i, resp in enumerate(responsaveis, 1):
            with st.expander(f"👤 {i}. {resp['nome']} ({resp['tipo_relacao']})", expanded=True):
                # Exibir dados atuais
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**🆔 ID:** {resp['id']}")
                    st.write(f"**📱 Telefone:** {resp.get('telefone', 'Não informado')}")
                    st.write(f"**📧 Email:** {resp.get('email', 'Não informado')}")
                    st.write(f"**📄 CPF:** {resp.get('cpf', 'Não informado')}")
                
                with col2:
                    st.write(f"**👨‍👩‍👧‍👦 Tipo Relação:** {resp['tipo_relacao']}")
                    st.write(f"**💰 Resp. Financeiro:** {'Sim' if resp['responsavel_financeiro'] else 'Não'}")
                    st.write(f"**📍 Endereço:** {resp.get('endereco', 'Não informado')}")
                    
                    # Indicador visual
                    if resp['responsavel_financeiro']:
                        st.success("💰 Responsável Financeiro")
                    else:
                        st.info("👥 Responsável Geral")
                
                # Formulário de edição inline
                st.markdown("**✏️ Editar Dados:**")
                
                with st.form(f"edit_resp_{resp['id']}"):
                    col_edit1, col_edit2 = st.columns(2)
                    
                    with col_edit1:
                        novo_telefone = st.text_input("📱 Telefone:", value=resp.get('telefone', ''), key=f"tel_{resp['id']}")
                        novo_email = st.text_input("📧 Email:", value=resp.get('email', ''), key=f"email_{resp['id']}")
                        novo_cpf = st.text_input("📄 CPF:", value=resp.get('cpf', ''), key=f"cpf_{resp['id']}")
                    
                    with col_edit2:
                        novo_tipo_relacao = st.selectbox(
                            "👨‍👩‍👧‍👦 Tipo de Relação:",
                            ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"],
                            index=["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"].index(resp['tipo_relacao']) if resp['tipo_relacao'] in ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"] else 0,
                            key=f"tipo_{resp['id']}"
                        )
                        
                        novo_resp_financeiro = st.checkbox(
                            "💰 É responsável financeiro",
                            value=resp['responsavel_financeiro'],
                            key=f"fin_{resp['id']}"
                        )
                        
                        novo_endereco = st.text_area("📍 Endereço:", value=resp.get('endereco', ''), key=f"end_{resp['id']}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                            # Atualizar dados do responsável
                            campos_resp = {
                                "telefone": novo_telefone if novo_telefone else None,
                                "email": novo_email if novo_email else None,
                                "cpf": novo_cpf if novo_cpf else None,
                                "endereco": novo_endereco if novo_endereco else None
                            }
                            
                            resultado_resp = atualizar_responsavel_campos(resp['id'], campos_resp)
                            
                            # Atualizar vínculo
                            resultado_vinculo = atualizar_vinculo_responsavel(
                                resp['id_vinculo'],
                                novo_tipo_relacao,
                                novo_resp_financeiro
                            )
                            
                            if resultado_resp.get("success") and resultado_vinculo.get("success"):
                                st.success("✅ Responsável atualizado!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao atualizar responsável")
                    
                    with col_btn2:
                        if st.form_submit_button("🗑️ Remover Vínculo", type="secondary"):
                            resultado_remocao = remover_vinculo_responsavel(resp['id_vinculo'])
                            if resultado_remocao.get("success"):
                                st.success("✅ Vínculo removido!")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao remover vínculo")
    else:
        st.warning("⚠️ Nenhum responsável vinculado a este aluno")
    
    # Seção 2: Cadastrar Novo Responsável
    st.markdown("---")
    st.markdown("#### ➕ Cadastrar Novo Responsável")
    
    with st.form("novo_responsavel"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("📖 Nome Completo*")
            cpf = st.text_input("📄 CPF")
            telefone = st.text_input("📱 Telefone")
        
        with col2:
            email = st.text_input("📧 Email")
            endereco = st.text_area("📍 Endereço")
            tipo_relacao = st.selectbox(
                "👨‍👩‍👧‍👦 Tipo de Relação*",
                ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"]
            )
        
        responsavel_financeiro = st.checkbox("💰 É responsável financeiro", value=True)
        
        if st.form_submit_button("➕ Cadastrar e Vincular", type="primary"):
            if not nome:
                st.error("Nome é obrigatório!")
            else:
                dados_responsavel = {
                    "nome": nome,
                    "cpf": cpf if cpf else None,
                    "telefone": telefone if telefone else None,
                    "email": email if email else None,
                    "endereco": endereco if endereco else None
                }
                
                resultado = cadastrar_responsavel_e_vincular(
                    dados_responsavel=dados_responsavel,
                    id_aluno=id_aluno,
                    tipo_relacao=tipo_relacao,
                    responsavel_financeiro=responsavel_financeiro
                )
                
                if resultado.get("success"):
                    st.success(f"✅ Responsável {nome} cadastrado e vinculado!")
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {resultado.get('error')}")
    
    # Seção 3: Vincular Responsável Existente
    st.markdown("---")
    st.markdown("#### 🔗 Vincular Responsável Existente")
    
    with st.form("vincular_existente"):
        busca_resp = st.text_input("🔍 Digite o nome do responsável:", placeholder="Digite para buscar...")
        
        responsavel_selecionado = None
        if busca_resp and len(busca_resp.strip()) >= 2:
            resultado_busca = buscar_responsaveis_para_dropdown(busca_resp.strip())
            if resultado_busca.get("success") and resultado_busca.get("opcoes"):
                opcoes_resp = {op["label"]: op for op in resultado_busca["opcoes"]}
                
                if opcoes_resp:
                    resp_escolhido = st.selectbox(
                        f"Responsáveis encontrados ({len(opcoes_resp)}):",
                        ["Selecione..."] + list(opcoes_resp.keys())
                    )
                    
                    if resp_escolhido != "Selecione...":
                        responsavel_selecionado = opcoes_resp[resp_escolhido]
                        st.info(f"📋 Selecionado: {responsavel_selecionado['nome']}")
                else:
                    st.info("Nenhum responsável encontrado")
        
        if responsavel_selecionado:
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_relacao_vinc = st.selectbox(
                    "👨‍👩‍👧‍👦 Tipo de Relação:",
                    ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"],
                    key="tipo_vinc"
                )
            
            with col2:
                resp_financeiro_vinc = st.checkbox("💰 É responsável financeiro", key="fin_vinc")
        
        if st.form_submit_button("🔗 Vincular", type="primary"):
            if responsavel_selecionado:
                resultado = vincular_aluno_responsavel(
                    id_aluno,
                    responsavel_selecionado["id"],
                    tipo_relacao_vinc,
                    resp_financeiro_vinc
                )
                
                if resultado.get("success"):
                    st.success(f"✅ Responsável {responsavel_selecionado['nome']} vinculado!")
                    st.rerun()
                else:
                    st.error(f"❌ Erro: {resultado.get('error')}")
            else:
                st.warning("Selecione um responsável para vincular")

def mostrar_pagamentos_aluno(pagamentos: List[Dict], estatisticas: Dict):
    """Exibe pagamentos registrados do aluno"""
    if pagamentos:
        st.markdown(f"### 💳 {len(pagamentos)} Pagamentos Registrados")
        
        # Resumo por tipo
        tipos_pagamento = {}
        for pag in pagamentos:
            tipo = pag["tipo_pagamento"]
            if tipo not in tipos_pagamento:
                tipos_pagamento[tipo] = {"count": 0, "valor": 0}
            tipos_pagamento[tipo]["count"] += 1
            tipos_pagamento[tipo]["valor"] += pag["valor"]
        
        # Mostrar resumo
        if tipos_pagamento:
            st.markdown("#### 📊 Resumo por Tipo de Pagamento")
            cols = st.columns(len(tipos_pagamento))
            
            for i, (tipo, info) in enumerate(tipos_pagamento.items()):
                with cols[i]:
                    st.metric(
                        f"💳 {tipo.title()}", 
                        f"{info['count']} pag.", 
                        delta=f"R$ {info['valor']:,.2f}"
                    )
        
        # Lista detalhada
        st.markdown("#### 📋 Lista Detalhada")
        df_pagamentos = pd.DataFrame(pagamentos)
        
        # Configurar colunas
        df_display = df_pagamentos[['data_pagamento', 'tipo_pagamento', 'valor', 'forma_pagamento', 'nome_responsavel', 'origem_extrato']].copy()
        df_display.columns = ['Data', 'Tipo', 'Valor', 'Forma', 'Responsável', 'Origem Extrato']
        
        st.dataframe(
            df_display,
            column_config={
                "Data": st.column_config.DateColumn("Data"),
                "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Origem Extrato": st.column_config.CheckboxColumn("Do Extrato PIX")
            },
            use_container_width=True,
            height=300
        )
        
    else:
        st.info("ℹ️ Nenhum pagamento registrado para este aluno")
        st.info("💡 Pagamentos aparecerão aqui após serem processados no extrato PIX")

def mostrar_mensalidades_aluno(mensalidades: List[Dict], estatisticas: Dict, id_aluno: str = None):
    """Exibe mensalidades do aluno"""
    
    # Verificar se pode gerar mensalidades (se não há mensalidades ou se o aluno pode gerar)
    pode_gerar_mensalidades = False
    if id_aluno:
        from funcoes_extrato_otimizadas import verificar_pode_gerar_mensalidades
        verificacao = verificar_pode_gerar_mensalidades(id_aluno)
        pode_gerar_mensalidades = verificacao.get("pode_gerar", False)
        
        # Mostrar botão de gerar mensalidades se aplicável
        if pode_gerar_mensalidades:
            st.markdown("### 🎯 Gerar Mensalidades")
            
            with st.expander("➕ Gerar Mensalidades para este Aluno", expanded=False):
                st.info("✅ Este aluno atende aos requisitos para gerar mensalidades!")
                
                # Mostrar condições atendidas
                if verificacao.get("success"):
                    condicoes = verificacao.get("condicoes", {})
                    st.success("**📋 Condições Atendidas:**")
                    if condicoes.get("tem_data_matricula"):
                        st.write("✅ Possui data de matrícula")
                    if condicoes.get("tem_dia_vencimento"):
                        st.write("✅ Possui dia de vencimento configurado")
                    if condicoes.get("tem_valor_mensalidade"):
                        st.write("✅ Possui valor de mensalidade configurado")
                    if condicoes.get("tem_pagamento_matricula"):
                        st.write("✅ Possui pagamento de matrícula registrado")
                
                # Formulário para gerar mensalidades
                with st.form(f"gerar_mensalidades_{id_aluno}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        automatico = st.checkbox(
                            "🤖 Gerar automaticamente",
                            value=True,
                            help="Gera mensalidades do mês seguinte à matrícula até dezembro. Se matrícula foi em dezembro, inicia em fevereiro."
                        )
                    
                    with col2:
                        st.write(" ")  # Espaço
                    
                    # Campos para modo manual
                    numero_parcelas = None
                    data_primeira_parcela = None
                    
                    if not automatico:
                        st.markdown("**⚙️ Configuração Manual:**")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            numero_parcelas = st.number_input(
                                "📊 Número de parcelas:",
                                min_value=1,
                                max_value=24,
                                value=10,
                                help="Quantidade de mensalidades a gerar"
                            )
                        
                        with col2:
                            data_primeira_parcela = st.date_input(
                                "📅 Vencimento da primeira parcela:",
                                help="Data de vencimento da primeira mensalidade"
                            )
                    
                    if st.form_submit_button("🎯 Gerar Mensalidades", type="primary"):
                        with st.spinner("Gerando mensalidades..."):
                            from funcoes_extrato_otimizadas import gerar_mensalidades_aluno
                            
                            # Preparar parâmetros
                            params = {
                                "id_aluno": id_aluno,
                                "automatico": automatico
                            }
                            
                            if not automatico:
                                params["numero_parcelas"] = numero_parcelas
                                params["data_primeira_parcela"] = data_primeira_parcela.isoformat() if data_primeira_parcela else None
                            
                            # Gerar mensalidades
                            resultado = gerar_mensalidades_aluno(**params)
                            
                            if resultado.get("success"):
                                st.success(f"✅ {resultado.get('mensalidades_criadas', 0)} mensalidades geradas com sucesso!")
                                st.info(f"📋 Modo: {resultado.get('modo', 'N/A')}")
                                st.info(f"👨‍🎓 Aluno: {resultado.get('aluno_nome', 'N/A')}")
                                
                                # Recarregar página para mostrar as novas mensalidades
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao gerar mensalidades: {resultado.get('error')}")
        
        elif not mensalidades:
            # Se não tem mensalidades e não pode gerar, mostrar motivos
            if verificacao.get("success"):
                problemas = verificacao.get("problemas", [])
                if problemas:
                    st.warning("⚠️ Este aluno não pode gerar mensalidades ainda:")
                    for problema in problemas:
                        st.write(f"   {problema}")
                    
                    st.info("💡 **Dica:** Complete os dados necessários e registre o pagamento da matrícula para poder gerar mensalidades.")
    
    if mensalidades:
        st.markdown(f"### 📅 {len(mensalidades)} Mensalidades")
        
        # Resumo por status
        status_counts = {}
        for mens in mensalidades:
            status = mens["status_real"]
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
        
        # Mostrar métricas de status
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            pagas = status_counts.get("Pago", 0) + status_counts.get("Pago parcial", 0)
            st.metric("✅ Pagas", pagas)
        
        with col2:
            a_vencer = status_counts.get("A vencer", 0)
            st.metric("📅 A Vencer", a_vencer)
        
        with col3:
            vencidas = status_counts.get("Vencida", 0)
            if vencidas > 0:
                st.metric("⚠️ Vencidas", vencidas, delta="Atenção", delta_color="inverse")
            else:
                st.metric("⚠️ Vencidas", 0)
        
        with col4:
            canceladas = status_counts.get("Cancelado", 0)
            if canceladas > 0:
                st.metric("❌ Canceladas", canceladas, delta="Trancamento", delta_color="off")
            else:
                st.metric("❌ Canceladas", 0)
        
        with col5:
            # Calcular valor total apenas das mensalidades não canceladas
            valor_total_mensalidades = sum(m["valor"] for m in mensalidades if m["status_real"] != "Cancelado")
            st.metric("💰 Valor Total", f"R$ {valor_total_mensalidades:,.2f}")
        
        # Lista detalhada de mensalidades
        st.markdown("#### 📋 Lista de Mensalidades")
        
        # Criar DataFrame
        df_mensalidades = []
        for mens in mensalidades:
            status_emoji = {
                "Pago": "✅",
                "Pago parcial": "🔶", 
                "A vencer": "📅",
                "Vencida": "⚠️",
                "Cancelado": "❌"
            }.get(mens["status_real"], "❓")
            
            df_mensalidades.append({
                "Status": f"{status_emoji} {mens['status_real']}",
                "Mês": mens["mes_referencia"],
                "Valor": mens["valor"],
                "Vencimento": mens["data_vencimento"],
                "Data Pagamento": mens.get("data_pagamento", "—"),
                "Observações": mens.get("observacoes", "")
            })
        
        df_display = pd.DataFrame(df_mensalidades)
        
        st.dataframe(
            df_display,
            column_config={
                "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                "Vencimento": st.column_config.DateColumn("Vencimento"),
                "Data Pagamento": st.column_config.TextColumn("Pago em")
            },
            use_container_width=True,
            height=400
        )
        
    else:
        st.info("ℹ️ Nenhuma mensalidade gerada para este aluno")
        if not pode_gerar_mensalidades:
            st.info("💡 Mensalidades devem ser geradas primeiro no sistema de gestão")

def mostrar_extrato_pix_aluno(id_aluno: str, responsaveis: List[Dict]):
    """Mostra registros do extrato PIX relacionados ao aluno e permite processamento em lote"""
    st.markdown("### 📊 Extrato PIX - Registros Relacionados")
    
    if not responsaveis:
        st.warning("⚠️ Nenhum responsável vinculado. Não é possível buscar registros no extrato PIX.")
        return
    
    # Buscar registros do extrato PIX
    with st.spinner("Buscando registros no extrato PIX..."):
        registros_encontrados = []
        
        try:
            # Buscar registros por responsável cadastrado
            for resp in responsaveis:
                id_responsavel = resp.get('id')
                if id_responsavel:
                    # Buscar registros diretamente por ID do responsável
                    from models.pedagogico import supabase
                    
                    # Buscar registros onde o responsável já foi identificado
                    response = supabase.table("extrato_pix").select("*").eq("id_responsavel", id_responsavel).execute()
                    
                    if response.data:
                        for registro in response.data:
                            # Adicionar informações do responsável
                            registro['responsavel_info'] = resp
                            registros_encontrados.append(registro)
                    
                    # Buscar também por nome (para registros ainda não processados)
                    nome_responsavel = resp.get('nome')
                    if nome_responsavel:
                        response_nome = supabase.table("extrato_pix").select("*").ilike("nome_remetente", f"%{nome_responsavel}%").execute()
                        
                        if response_nome.data:
                            # Evitar duplicatas
                            ids_existentes = [r.get('id') for r in registros_encontrados]
                            for registro in response_nome.data:
                                if registro.get('id') not in ids_existentes:
                                    registro['responsavel_info'] = resp
                                    registros_encontrados.append(registro)
                    
                    # Buscar por CPF se disponível
                    cpf_responsavel = resp.get('cpf')
                    if cpf_responsavel:
                        # Buscar registros que contenham o CPF nas observações ou chave PIX
                        response_cpf = supabase.table("extrato_pix").select("*").or_(
                            f"observacoes.ilike.%{cpf_responsavel}%,chave_pix.ilike.%{cpf_responsavel}%"
                        ).execute()
                        
                        if response_cpf.data:
                            # Evitar duplicatas
                            ids_existentes = [r.get('id') for r in registros_encontrados]
                            for registro in response_cpf.data:
                                if registro.get('id') not in ids_existentes:
                                    registro['responsavel_info'] = resp
                                    registros_encontrados.append(registro)
        
        except Exception as e:
            st.error(f"❌ Erro ao buscar registros: {e}")
            return
    
    if registros_encontrados:
        st.success(f"✅ {len(registros_encontrados)} registros encontrados no extrato PIX")
        
        # Separar registros por status
        registros_nao_processados = [r for r in registros_encontrados if r.get('status') != 'registrado']
        registros_processados = [r for r in registros_encontrados if r.get('status') == 'registrado']
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total", len(registros_encontrados))
        
        with col2:
            valor_nao_processado = sum(float(r.get('valor', 0)) for r in registros_nao_processados)
            st.metric("⏳ Não Processados", len(registros_nao_processados), 
                     delta=f"R$ {valor_nao_processado:,.2f}")
        
        with col3:
            valor_processado = sum(float(r.get('valor', 0)) for r in registros_processados)
            st.metric("✅ Processados", len(registros_processados), 
                     delta=f"R$ {valor_processado:,.2f}")
        
        # Tabs para separar processados e não processados
        tab_nao_proc, tab_proc = st.tabs([
            f"⏳ Não Processados ({len(registros_nao_processados)})",
            f"✅ Processados ({len(registros_processados)})"
        ])
        
        # TAB: Registros NÃO PROCESSADOS (podem ser convertidos em pagamentos)
        with tab_nao_proc:
            if registros_nao_processados:
                # Sistema de marcação em lote
                session_key = f"pagamentos_marcados_{id_aluno}"
                if session_key not in st.session_state:
                    st.session_state[session_key] = []
                
                pagamentos_marcados = st.session_state[session_key]
                
                # Painel de controle dos pagamentos marcados
                if pagamentos_marcados:
                    with st.container():
                        st.markdown("### 📋 Pagamentos Marcados para Processamento")
                        
                        col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
                        
                        with col_resumo1:
                            st.metric("📌 Marcados", len(pagamentos_marcados))
                        
                        with col_resumo2:
                            valor_total_marcado = sum(p.get('valor_pagamento', 0) for p in pagamentos_marcados)
                            st.metric("💰 Valor Total", f"R$ {valor_total_marcado:,.2f}")
                        
                        with col_resumo3:
                            mensalidades_marcadas = sum(1 for p in pagamentos_marcados if p.get('tipo_pagamento') == 'mensalidade')
                            st.metric("📅 Mensalidades", mensalidades_marcadas)
                        
                        # Lista dos pagamentos marcados
                        with st.expander("👁️ Ver Pagamentos Marcados", expanded=False):
                            for i, pag in enumerate(pagamentos_marcados, 1):
                                col_pag1, col_pag2, col_pag3 = st.columns([3, 2, 1])
                                
                                with col_pag1:
                                    st.write(f"**{i}. {pag['nome_remetente']}**")
                                    st.write(f"👨‍🎓 {pag['nome_aluno']}")
                                    
                                with col_pag2:
                                    st.write(f"💳 {pag['tipo_pagamento'].title()}")
                                    st.write(f"💰 R$ {pag['valor_pagamento']:,.2f}")
                                    if pag.get('mes_referencia'):
                                        st.write(f"📅 {pag['mes_referencia']}")
                                
                                with col_pag3:
                                    if st.button("🗑️", key=f"remove_marcado_{i}", help="Remover"):
                                        pagamentos_marcados.remove(pag)
                                        st.rerun()
                        
                        # Botões de ação em lote
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            if st.button("✅ PROCESSAR TODOS OS PAGAMENTOS", type="primary", use_container_width=True):
                                if pagamentos_marcados:
                                    try:
                                        sucessos = 0
                                        erros = []
                                        
                                        with st.spinner(f"Processando {len(pagamentos_marcados)} pagamentos..."):
                                            for pag in pagamentos_marcados:
                                                try:
                                                    from funcoes_extrato_otimizadas import registrar_pagamento_do_extrato
                                                    
                                                    resultado = registrar_pagamento_do_extrato(
                                                        id_extrato=pag['id_registro'],
                                                        id_responsavel=pag['id_responsavel'],
                                                        id_aluno=pag['id_aluno'],
                                                        tipo_pagamento=pag['tipo_pagamento'],
                                                        descricao=pag.get('observacoes'),
                                                        id_mensalidade=pag.get('id_mensalidade')
                                                    )
                                                    
                                                    if resultado.get("success"):
                                                        sucessos += 1
                                                    else:
                                                        erros.append(f"{pag['nome_remetente']}: {resultado.get('error')}")
                                                
                                                except Exception as e:
                                                    erros.append(f"{pag['nome_remetente']}: {str(e)}")
                                        
                                        # Mostrar resultados
                                        if sucessos > 0:
                                            st.success(f"✅ {sucessos} pagamentos processados com sucesso!")
                                        
                                        if erros:
                                            st.error(f"❌ {len(erros)} erros encontrados:")
                                            for erro in erros:
                                                st.write(f"   - {erro}")
                                        
                                        # Limpar lista
                                        st.session_state[session_key] = []
                                        st.rerun()
                                    
                                    except Exception as e:
                                        st.error(f"❌ Erro geral no processamento: {e}")
                        
                        with col_btn2:
                            if st.button("🗑️ Limpar Marcados", use_container_width=True):
                                st.session_state[session_key] = []
                                st.rerun()
                        
                        with col_btn3:
                            if st.button("🔄 Atualizar Lista", use_container_width=True):
                                st.rerun()
                        
                        st.markdown("---")
                
                st.markdown("#### 💳 Registros Disponíveis para Marcação")
                st.info("💡 Configure cada pagamento e clique em 'Marcar' para adicionar à lista de processamento")
                
                # Ordenar registros por data (mais antigo primeiro)
                registros_ordenados = sorted(registros_nao_processados, key=lambda x: x.get('data_pagamento', ''))
                
                for i, registro in enumerate(registros_ordenados, 1):
                    # Formatação melhorada da exibição
                    nome_remetente = registro.get('nome_remetente', 'Nome não informado')
                    valor = float(registro.get('valor', 0))
                    data_pagamento = registro.get('data_pagamento', 'N/A')
                    
                    # Converter data para formato brasileiro se possível
                    try:
                        from datetime import datetime
                        data_obj = datetime.strptime(data_pagamento, '%Y-%m-%d')
                        data_formatada = data_obj.strftime('%d/%m/%Y')
                    except:
                        data_formatada = data_pagamento
                    
                    titulo_expander = f"{i}. {nome_remetente} - R$ {valor:,.2f} - {data_formatada}"
                    
                    # Verificar se já está marcado
                    ja_marcado = any(p["id_registro"] == registro.get('id') for p in pagamentos_marcados)
                    
                    with st.expander(titulo_expander, expanded=False):
                        # Mostrar detalhes do registro
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**📅 Data:** {registro.get('data_pagamento', 'N/A')}")
                            st.write(f"**💰 Valor:** R$ {float(registro.get('valor', 0)):,.2f}")
                            st.write(f"**👤 Remetente:** {registro.get('nome_remetente', 'N/A')}")
                            st.write(f"**📄 Status:** {registro.get('status', 'N/A')}")
                        
                        with col2:
                            st.write(f"**📝 Descrição:** {registro.get('descricao', 'N/A')}")
                            st.write(f"**💬 Observações:** {registro.get('observacoes', 'N/A')}")
                            st.write(f"**🆔 ID Registro:** {registro.get('id', 'N/A')}")
                            
                            # Mostrar responsável relacionado
                            if registro.get('responsavel_info'):
                                resp_info = registro['responsavel_info']
                                st.write(f"**👤 Responsável:** {resp_info['nome']}")
                        
                        if ja_marcado:
                            st.success("✅ Este registro já está marcado para processamento")
                        else:
                            # Configuração do pagamento
                            st.markdown("---")
                            st.markdown("**🔄 Configurar Pagamento:**")
                            
                            # Verificar se responsável tem múltiplos alunos
                            resp_info = registro.get('responsavel_info', {})
                            id_responsavel = resp_info.get('id')
                            
                            # Buscar alunos vinculados ao responsável
                            from models.pedagogico import listar_alunos_vinculados_responsavel
                            alunos_resultado = listar_alunos_vinculados_responsavel(id_responsavel) if id_responsavel else {"success": False}
                            
                            tem_multiplos_alunos = False
                            alunos_vinculados = []
                            
                            if alunos_resultado.get("success") and alunos_resultado.get("alunos"):
                                alunos_vinculados = alunos_resultado["alunos"]
                                tem_multiplos_alunos = len(alunos_vinculados) > 1
                            
                            col_config1, col_config2 = st.columns(2)
                            
                            with col_config1:
                                # Seleção do aluno (se múltiplos)
                                if tem_multiplos_alunos:
                                    opcoes_alunos = {f"{aluno['nome']} - {aluno.get('turmas', {}).get('nome_turma', 'N/A')}": aluno for aluno in alunos_vinculados}
                                    aluno_selecionado_nome = st.selectbox(
                                        "👨‍🎓 Selecionar Aluno:",
                                        list(opcoes_alunos.keys()),
                                        key=f"aluno_config_{registro.get('id')}"
                                    )
                                    aluno_selecionado = opcoes_alunos[aluno_selecionado_nome]
                                    id_aluno_processamento = aluno_selecionado["id"]
                                else:
                                    aluno_selecionado = alunos_vinculados[0] if alunos_vinculados else None
                                    id_aluno_processamento = aluno_selecionado["id"] if aluno_selecionado else id_aluno
                                    st.info(f"👨‍🎓 Aluno: {aluno_selecionado['nome'] if aluno_selecionado else 'N/A'}")
                                
                                # Tipo de pagamento (SEM mensalidade)
                                tipo_pagamento = st.selectbox(
                                    "💳 Tipo de Pagamento:",
                                    ["matricula", "material", "uniforme", "transporte", "outro"],
                                    key=f"tipo_config_{registro.get('id')}"
                                )
                                
                                # Valor (pré-preenchido, mas editável)
                                valor_pagamento = st.number_input(
                                    "💰 Valor do Pagamento:",
                                    min_value=0.01,
                                    value=float(registro.get('valor', 0)),
                                    step=0.01,
                                    key=f"valor_config_{registro.get('id')}"
                                )
                            
                            with col_config2:
                                # Campo separado para mensalidades
                                mensalidade_selecionada = None
                                if id_aluno_processamento:
                                    from funcoes_extrato_otimizadas import listar_mensalidades_disponiveis_aluno
                                    mensalidades_resultado = listar_mensalidades_disponiveis_aluno(id_aluno_processamento)
                                    
                                    if mensalidades_resultado.get("success") and mensalidades_resultado.get("mensalidades"):
                                        mensalidades_disponiveis = mensalidades_resultado["mensalidades"]
                                        opcoes_mensalidades = ["Não é pagamento de mensalidade"] + [m["label"] for m in mensalidades_disponiveis]
                                        
                                        mensalidade_escolhida = st.selectbox(
                                            f"📅 Mensalidades para {aluno_selecionado['nome'] if aluno_selecionado else 'aluno'}:",
                                            options=opcoes_mensalidades,
                                            key=f"mens_config_{registro.get('id')}",
                                            help="Selecione uma mensalidade se este pagamento for referente a mensalidade"
                                        )
                                        
                                        if mensalidade_escolhida != "Não é pagamento de mensalidade":
                                            mensalidade_selecionada = next(
                                                (m for m in mensalidades_disponiveis if m["label"] == mensalidade_escolhida), 
                                                None
                                            )
                                            
                                            if mensalidade_selecionada:
                                                st.success(f"📅 Selecionado: {mensalidade_selecionada['mes_referencia']} - {mensalidade_selecionada['status_texto']}")
                                    else:
                                        st.info(f"ℹ️ Nenhuma mensalidade pendente para {aluno_selecionado['nome'] if aluno_selecionado else 'este aluno'}")
                                
                                observacoes = st.text_area(
                                    "📝 Observações:",
                                    placeholder="Observações sobre o pagamento...",
                                    key=f"obs_config_{registro.get('id')}"
                                )
                            
                            # Botões de ação
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                if st.button("📌 Marcar para Processamento", key=f"marcar_{registro.get('id')}", type="primary"):
                                    # Criar configuração do pagamento
                                    config_pagamento = {
                                        "id_registro": registro.get('id'),
                                        "nome_remetente": nome_remetente,
                                        "valor_original": float(registro.get('valor', 0)),
                                        "data_pagamento": registro.get('data_pagamento'),
                                        "id_aluno": id_aluno_processamento,
                                        "nome_aluno": aluno_selecionado['nome'] if aluno_selecionado else 'N/A',
                                        "tipo_pagamento": "mensalidade" if mensalidade_selecionada else tipo_pagamento,
                                        "valor_pagamento": valor_pagamento,
                                        "observacoes": observacoes,
                                        "id_responsavel": resp_info.get('id'),
                                        "responsavel_info": resp_info
                                    }
                                    
                                    # Adicionar dados da mensalidade se selecionada
                                    if mensalidade_selecionada:
                                        config_pagamento.update({
                                            "id_mensalidade": mensalidade_selecionada["id_mensalidade"],
                                            "mes_referencia": mensalidade_selecionada["mes_referencia"],
                                            "data_vencimento": mensalidade_selecionada["data_vencimento"],
                                            "tipo_pagamento": "mensalidade"
                                        })
                                    
                                    pagamentos_marcados.append(config_pagamento)
                                    st.success(f"✅ Pagamento marcado! Total: {len(pagamentos_marcados)}")
                                    st.rerun()
                            
                            with col_btn2:
                                if st.button("🔄 Processar Individual", key=f"proc_individual_{registro.get('id')}", type="secondary"):
                                    # Processar apenas este pagamento
                                    try:
                                        from funcoes_extrato_otimizadas import registrar_pagamento_do_extrato
                                        
                                        # Determinar tipo e ID da mensalidade
                                        tipo_final = "mensalidade" if mensalidade_selecionada else tipo_pagamento
                                        id_mensalidade = mensalidade_selecionada["id_mensalidade"] if mensalidade_selecionada else None
                                        
                                        resultado_processamento = registrar_pagamento_do_extrato(
                                            id_extrato=registro.get('id'),
                                            id_responsavel=resp_info.get('id'),
                                            id_aluno=id_aluno_processamento,
                                            tipo_pagamento=tipo_final,
                                            descricao=observacoes if observacoes else None,
                                            id_mensalidade=id_mensalidade
                                        )
                                        
                                        if resultado_processamento.get("success"):
                                            st.success("✅ Registro processado como pagamento com sucesso!")
                                            if resultado_processamento.get('id_pagamento'):
                                                st.info(f"📋 ID do Pagamento: {resultado_processamento.get('id_pagamento')}")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Erro ao processar: {resultado_processamento.get('error')}")
                                    
                                    except Exception as e:
                                        st.error(f"❌ Erro ao processar pagamento: {e}")
                        
            else:
                st.info("✅ Todos os registros relacionados já foram processados como pagamentos")
        
        # TAB: Registros PROCESSADOS (já convertidos em pagamentos)
        with tab_proc:
            if registros_processados:
                st.markdown("#### ✅ Registros Já Processados")
                st.info("ℹ️ Estes registros já foram convertidos em pagamentos oficiais")
                
                # Criar DataFrame para exibição
                df_processados = []
                for registro in registros_processados:
                    df_processados.append({
                        "Data": registro.get('data_pagamento', 'N/A'),
                        "Valor": f"R$ {float(registro.get('valor', 0)):,.2f}",
                        "Remetente": registro.get('nome_remetente', 'N/A'),
                        "Descrição": registro.get('descricao', 'N/A'),
                        "Status": registro.get('status', 'N/A'),
                        "ID Registro": registro.get('id', 'N/A')
                    })
                
                if df_processados:
                    df_display = pd.DataFrame(df_processados)
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        height=300
                    )
                else:
                    st.info("Nenhum registro processado encontrado")
            else:
                st.info("ℹ️ Nenhum registro foi processado ainda")
    
    else:
        st.info("ℹ️ Nenhum registro encontrado no extrato PIX para os responsáveis deste aluno")
        st.info("💡 Registros aparecerão aqui quando transações PIX forem identificadas com os dados dos responsáveis")
        
        # Mostrar informações dos responsáveis para debug
        with st.expander("🔍 Informações dos Responsáveis (Debug)", expanded=False):
            for i, resp in enumerate(responsaveis, 1):
                st.write(f"**👤 {i}. {resp.get('nome', 'N/A')}**")
                st.write(f"   - ID: {resp.get('id', 'N/A')}")
                st.write(f"   - CPF: {resp.get('cpf', 'N/A')}")
                st.write(f"   - Telefone: {resp.get('telefone', 'N/A')}")
                st.write("---")

# ==========================================================
# 💰 FUNÇÕES DE INTERFACE PARA COBRANÇAS
# ==========================================================

def mostrar_interface_criar_cobrancas():
    """Interface para criar novas cobranças"""
    st.markdown("### ➕ Criar Novas Cobranças")
    
    # Tipos de cobrança
    tipo_cobranca_tabs = st.tabs(["📦 Cobrança Parcelada", "📝 Cobrança Individual"])
    
    # TAB: Cobrança Parcelada (ex: Formatura)
    with tipo_cobranca_tabs[0]:
        st.markdown("#### 📦 Cadastrar Cobrança Parcelada")
        st.info("💡 Use para cobranças como formatura, eventos com múltiplas parcelas, etc.")
        
        with st.form("form_cobranca_parcelada"):
            col1, col2 = st.columns(2)
            
            with col1:
                titulo_base = st.text_input("📝 Título da Cobrança*", 
                                          placeholder="Ex: Formatura 2025")
                descricao = st.text_area("📋 Descrição", 
                                       placeholder="Ex: Formatura da turma Infantil III")
                valor_parcela = st.number_input("💰 Valor por Parcela (R$)*", 
                                              min_value=0.01, step=0.01, value=376.00)
                numero_parcelas = st.number_input("🔢 Número de Parcelas*", 
                                                min_value=2, max_value=24, value=6)
            
            with col2:
                data_primeira = st.date_input("📅 Data da Primeira Parcela*", 
                                            value=date(2025, 6, 30))
                
                tipo_opcoes = list(TIPOS_COBRANCA_DISPLAY.keys())
                tipo_selecionado = st.selectbox("🎯 Tipo de Cobrança*", 
                                              tipo_opcoes,
                                              format_func=lambda x: TIPOS_COBRANCA_DISPLAY[x])
                
                prioridade = st.selectbox("⚡ Prioridade", 
                                        list(PRIORIDADES_COBRANCA.keys()),
                                        index=1,  # Normal como padrão
                                        format_func=lambda x: PRIORIDADES_COBRANCA[x])
                
                observacoes = st.text_area("📝 Observações", 
                                         placeholder="Observações adicionais...")
            
            # Preview das parcelas
            if titulo_base and valor_parcela > 0 and numero_parcelas > 0:
                st.markdown("#### 👁️ Preview das Parcelas")
                
                from datetime import datetime, timedelta
                data_base = data_primeira
                valor_total = valor_parcela * numero_parcelas
                
                st.info(f"📊 **Total:** {numero_parcelas} parcelas de {valor_parcela:,.2f} = R$ {valor_total:,.2f}")
                
                # Mostrar algumas parcelas como exemplo
                for i in range(min(3, numero_parcelas)):
                    data_parcela = data_base + timedelta(days=30 * i)
                    st.write(f"• **Parcela {i+1}:** {titulo_base} - Parcela {i+1}/{numero_parcelas} - R$ {valor_parcela:,.2f} - {data_parcela.strftime('%d/%m/%Y')}")
                
                if numero_parcelas > 3:
                    st.write(f"... e mais {numero_parcelas - 3} parcelas")
            
            # Botão de criação
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                criar_cobranca = st.form_submit_button("🎯 Criar Cobrança Parcelada", type="primary")
            
            with col_btn2:
                if st.form_submit_button("👥 Criar e Vincular a Alunos"):
                    st.session_state['criar_e_vincular_parcelada'] = True
                    criar_cobranca = True
            
            if criar_cobranca:
                if not titulo_base or valor_parcela <= 0 or numero_parcelas <= 0:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                else:
                    # Salvar dados na sessão para usar na vinculação
                    dados_cobranca = {
                        "titulo": titulo_base,
                        "descricao": descricao,
                        "valor_parcela": valor_parcela,
                        "numero_parcelas": numero_parcelas,
                        "data_primeira_parcela": data_primeira.isoformat(),
                        "tipo_cobranca": tipo_selecionado,
                        "prioridade": prioridade,
                        "observacoes": observacoes
                    }
                    
                    st.session_state['ultima_cobranca_parcelada'] = dados_cobranca
                    st.success("✅ Cobrança parcelada configurada!")
                    
                    if st.session_state.get('criar_e_vincular_parcelada'):
                        st.info("👥 Vá para a aba 'Vincular Alunos' para adicionar alunos a esta cobrança")
                        del st.session_state['criar_e_vincular_parcelada']
    
    # TAB: Cobrança Individual
    with tipo_cobranca_tabs[1]:
        st.markdown("#### 📝 Cadastrar Cobrança Individual")
        st.info("💡 Use para cobranças únicas como taxas, materiais, etc.")
        
        with st.form("form_cobranca_individual"):
            col1, col2 = st.columns(2)
            
            with col1:
                titulo_individual = st.text_input("📝 Título da Cobrança*", 
                                                placeholder="Ex: Taxa de Material")
                descricao_individual = st.text_area("📋 Descrição", 
                                                  placeholder="Ex: Kit de material escolar")
                valor_individual = st.number_input("💰 Valor (R$)*", 
                                                 min_value=0.01, step=0.01, value=120.00)
            
            with col2:
                data_vencimento = st.date_input("📅 Data de Vencimento*")
                
                tipo_individual = st.selectbox("🎯 Tipo de Cobrança*", 
                                             tipo_opcoes,
                                             format_func=lambda x: TIPOS_COBRANCA_DISPLAY[x],
                                             key="tipo_individual")
                
                prioridade_individual = st.selectbox("⚡ Prioridade", 
                                                   list(PRIORIDADES_COBRANCA.keys()),
                                                   index=1,
                                                   format_func=lambda x: PRIORIDADES_COBRANCA[x],
                                                   key="prioridade_individual")
                
                observacoes_individual = st.text_area("📝 Observações", 
                                                    placeholder="Observações adicionais...",
                                                    key="obs_individual")
            
            # Botões de criação
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                criar_individual = st.form_submit_button("📝 Criar Cobrança Individual", type="primary")
            
            with col_btn2:
                if st.form_submit_button("👥 Criar e Vincular a Alunos"):
                    st.session_state['criar_e_vincular_individual'] = True
                    criar_individual = True
            
            if criar_individual:
                if not titulo_individual or valor_individual <= 0:
                    st.error("❌ Preencha todos os campos obrigatórios!")
                else:
                    # Salvar dados na sessão
                    dados_individual = {
                        "titulo": titulo_individual,
                        "descricao": descricao_individual,
                        "valor": valor_individual,
                        "data_vencimento": data_vencimento.isoformat(),
                        "tipo_cobranca": tipo_individual,
                        "prioridade": prioridade_individual,
                        "observacoes": observacoes_individual
                    }
                    
                    st.session_state['ultima_cobranca_individual'] = dados_individual
                    st.success("✅ Cobrança individual configurada!")
                    
                    if st.session_state.get('criar_e_vincular_individual'):
                        st.info("👥 Vá para a aba 'Vincular Alunos' para adicionar alunos a esta cobrança")
                        del st.session_state['criar_e_vincular_individual']

def mostrar_cobrancas_aluno(id_aluno: str, responsaveis: List[Dict]):
    """Mostra interface completa de cobranças do aluno"""
    st.markdown("### 💰 Cobranças do Aluno")
    
    # Buscar cobranças do aluno
    with st.spinner("Carregando cobranças..."):
        resultado_cobrancas = listar_cobrancas_aluno(id_aluno)
    
    if not resultado_cobrancas.get("success"):
        st.error(f"❌ Erro ao carregar cobranças: {resultado_cobrancas.get('error')}")
        return
    
    cobrancas = resultado_cobrancas.get("cobrancas", [])
    estatisticas = resultado_cobrancas.get("estatisticas", {})
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏳ Pendentes", estatisticas.get("total_pendente", 0), 
                 delta=f"R$ {estatisticas.get('valor_pendente', 0):,.2f}")
    
    with col2:
        st.metric("⚠️ Vencidas", estatisticas.get("total_vencido", 0),
                 delta=f"R$ {estatisticas.get('valor_vencido', 0):,.2f}")
    
    with col3:
        st.metric("✅ Pagas", estatisticas.get("total_pago", 0),
                 delta=f"R$ {estatisticas.get('valor_pago', 0):,.2f}")
    
    with col4:
        valor_total = (estatisticas.get('valor_pendente', 0) + 
                      estatisticas.get('valor_vencido', 0) + 
                      estatisticas.get('valor_pago', 0))
        st.metric("💰 Total", f"R$ {valor_total:,.2f}")
    
    if cobrancas:
        st.markdown("#### 📋 Lista de Cobranças")
        
        # Agrupar por grupo_cobranca para mostrar parcelas relacionadas
        grupos = {}
        individuais = []
        
        for cobranca in cobrancas:
            if cobranca.get("grupo_cobranca"):
                grupo = cobranca["grupo_cobranca"]
                if grupo not in grupos:
                    grupos[grupo] = []
                grupos[grupo].append(cobranca)
            else:
                individuais.append(cobranca)
        
        # Mostrar grupos de parcelas
        for grupo, parcelas in grupos.items():
            primeiro = parcelas[0]
            total_grupo = sum(p["valor"] for p in parcelas)
            pagas_grupo = len([p for p in parcelas if p["status_real"] == "Pago"])
            
            with st.expander(f"📦 {primeiro['titulo'].split(' - Parcela')[0]} - {len(parcelas)} parcelas - R$ {total_grupo:,.2f} ({pagas_grupo} pagas)", expanded=False):
                for parcela in sorted(parcelas, key=lambda x: x["parcela_numero"]):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**{parcela['emoji']} {parcela['titulo_completo']}**")
                        st.write(f"📅 Vencimento: {parcela['data_vencimento_br']}")
                    
                    with col2:
                        st.write(f"💰 {parcela['valor_br']}")
                        st.write(f"🔢 {parcela['status_real']}")
                    
                    with col3:
                        if parcela['status_real'] == 'Pendente':
                            if st.button("✅ Pagar", key=f"pagar_{parcela['id_cobranca']}"):
                                data_hoje = date.today().isoformat()
                                resultado = marcar_cobranca_como_paga(parcela['id_cobranca'], data_hoje)
                                if resultado.get("success"):
                                    st.success("✅ Cobrança marcada como paga!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro: {resultado.get('error')}")
        
        # Mostrar cobranças individuais
        if individuais:
            st.markdown("#### 📝 Cobranças Individuais")
            for cobranca in individuais:
                with st.expander(f"{cobranca['emoji']} {cobranca['titulo']} - {cobranca['valor_br']}", expanded=False):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**📋 Tipo:** {cobranca['tipo_display']}")
                        st.write(f"**📅 Vencimento:** {cobranca['data_vencimento_br']}")
                        if cobranca.get('descricao'):
                            st.write(f"**📝 Descrição:** {cobranca['descricao']}")
                    
                    with col2:
                        st.write(f"**💰 Valor:** {cobranca['valor_br']}")
                        st.write(f"**🔢 Status:** {cobranca['status_real']}")
                        st.write(f"**⚡ Prioridade:** {cobranca['prioridade_display']}")
                    
                    with col3:
                        if cobranca['status_real'] == 'Pendente':
                            if st.button("✅ Pagar", key=f"pagar_individual_{cobranca['id_cobranca']}"):
                                data_hoje = date.today().isoformat()
                                resultado = marcar_cobranca_como_paga(cobranca['id_cobranca'], data_hoje)
                                if resultado.get("success"):
                                    st.success("✅ Cobrança marcada como paga!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro: {resultado.get('error')}")
                        elif cobranca['status_real'] == 'Pago':
                            st.success(f"Pago em: {cobranca['data_pagamento_br']}")
    else:
        st.info("ℹ️ Nenhuma cobrança cadastrada para este aluno")
        st.info("💡 Use a aba 'Gestão de Cobranças' para criar e vincular cobranças")

def mostrar_interface_vincular_alunos_cobrancas():
    """Interface para vincular alunos às cobranças criadas"""
    st.markdown("### 👨‍🎓 Vincular Alunos às Cobranças")
    
    # Verificar se há cobranças configuradas na sessão
    cobranca_parcelada = st.session_state.get('ultima_cobranca_parcelada')
    cobranca_individual = st.session_state.get('ultima_cobranca_individual')
    
    if not cobranca_parcelada and not cobranca_individual:
        st.warning("⚠️ Nenhuma cobrança configurada na sessão")
        st.info("💡 Vá para a aba 'Criar Cobranças' primeiro para configurar uma cobrança")
        return
    
    # Tabs para tipos de cobrança
    vincular_tabs = []
    tab_labels = []
    
    if cobranca_parcelada:
        tab_labels.append("📦 Cobrança Parcelada")
    if cobranca_individual:
        tab_labels.append("📝 Cobrança Individual")
    
    if len(tab_labels) > 1:
        vincular_tabs = st.tabs(tab_labels)
    else:
        vincular_tabs = [st.container()]
    
    tab_index = 0
    
    # TAB: Vincular Cobrança Parcelada
    if cobranca_parcelada:
        with vincular_tabs[tab_index]:
            st.markdown("#### 📦 Vincular Cobrança Parcelada")
            
            # Mostrar resumo da cobrança
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.info(f"**📝 Título:** {cobranca_parcelada['titulo']}")
                st.info(f"**💰 Valor por Parcela:** R$ {cobranca_parcelada['valor_parcela']:,.2f}")
                st.info(f"**🔢 Número de Parcelas:** {cobranca_parcelada['numero_parcelas']}")
            
            with col_info2:
                valor_total = cobranca_parcelada['valor_parcela'] * cobranca_parcelada['numero_parcelas']
                st.info(f"**💰 Valor Total:** R$ {valor_total:,.2f}")
                st.info(f"**📅 Primeira Parcela:** {formatar_data_br(cobranca_parcelada['data_primeira_parcela'])}")
                st.info(f"**🎯 Tipo:** {TIPOS_COBRANCA_DISPLAY.get(cobranca_parcelada['tipo_cobranca'], 'N/A')}")
            
            # Interface para selecionar alunos
            st.markdown("#### 🔍 Selecionar Alunos")
            
            # Busca por turmas
            turmas_resultado = listar_turmas_disponiveis()
            if turmas_resultado.get("success"):
                turmas_selecionadas = st.multiselect(
                    "🎓 Filtrar por Turmas (opcional):",
                    options=turmas_resultado["turmas"],
                    help="Deixe vazio para buscar em todas as turmas"
                )
                
                # Buscar alunos das turmas
                if turmas_selecionadas:
                    mapeamento = obter_mapeamento_turmas()
                    if mapeamento.get("success"):
                        ids_turmas = [mapeamento["mapeamento"][nome] for nome in turmas_selecionadas]
                        
                        resultado_alunos = buscar_alunos_por_turmas(ids_turmas)
                        if resultado_alunos.get("success"):
                            # Mostrar alunos agrupados por turma
                            st.markdown("#### 👨‍🎓 Alunos Disponíveis")
                            
                            alunos_selecionados = []
                            
                            for turma_nome, dados_turma in resultado_alunos["alunos_por_turma"].items():
                                with st.expander(f"🎓 {turma_nome} ({len(dados_turma['alunos'])} alunos)", expanded=True):
                                    
                                    # Checkbox para selecionar todos da turma
                                    selecionar_todos = st.checkbox(f"Selecionar todos de {turma_nome}", key=f"todos_{turma_nome}_parcelada")
                                    
                                    cols = st.columns(3)
                                    for i, aluno in enumerate(dados_turma["alunos"]):
                                        col_idx = i % 3
                                        with cols[col_idx]:
                                            selecionado = st.checkbox(
                                                f"👨‍🎓 {aluno['nome']}",
                                                value=selecionar_todos,
                                                key=f"aluno_{aluno['id']}_parcelada"
                                            )
                                            if selecionado:
                                                alunos_selecionados.append({
                                                    "id": aluno["id"],
                                                    "nome": aluno["nome"],
                                                    "turma": turma_nome
                                                })
                            
                            # Mostrar resumo dos selecionados
                            if alunos_selecionados:
                                st.markdown("#### 📋 Resumo dos Alunos Selecionados")
                                
                                col_resumo1, col_resumo2 = st.columns(2)
                                
                                with col_resumo1:
                                    st.metric("👨‍🎓 Total de Alunos", len(alunos_selecionados))
                                    valor_total_geral = valor_total * len(alunos_selecionados)
                                    st.metric("💰 Valor Total Geral", f"R$ {valor_total_geral:,.2f}")
                                
                                with col_resumo2:
                                    # Agrupar por turma para resumo
                                    turmas_resumo = {}
                                    for aluno in alunos_selecionados:
                                        turma = aluno["turma"]
                                        if turma not in turmas_resumo:
                                            turmas_resumo[turma] = 0
                                        turmas_resumo[turma] += 1
                                    
                                    st.write("**📊 Por Turma:**")
                                    for turma, quantidade in turmas_resumo.items():
                                        st.write(f"• {turma}: {quantidade} alunos")
                                
                                # Botão para criar as cobranças
                                if st.button("🎯 Criar Cobranças para Alunos Selecionados", type="primary", key="criar_parcelada"):
                                    with st.spinner(f"Criando cobranças para {len(alunos_selecionados)} alunos..."):
                                        sucessos = 0
                                        erros = []
                                        
                                        for aluno in alunos_selecionados:
                                            try:
                                                # Buscar responsável financeiro do aluno
                                                responsaveis_aluno = listar_responsaveis_aluno(aluno["id"])
                                                
                                                id_responsavel = None
                                                if responsaveis_aluno.get("success") and responsaveis_aluno.get("responsaveis"):
                                                    # Procurar responsável financeiro
                                                    for resp in responsaveis_aluno["responsaveis"]:
                                                        if resp.get("responsavel_financeiro"):
                                                            id_responsavel = resp["id"]
                                                            break
                                                    
                                                    # Se não tem financeiro, usar o primeiro
                                                    if not id_responsavel:
                                                        id_responsavel = responsaveis_aluno["responsaveis"][0]["id"]
                                                
                                                if id_responsavel:
                                                    resultado = cadastrar_cobranca_parcelada(
                                                        aluno["id"], 
                                                        id_responsavel, 
                                                        cobranca_parcelada
                                                    )
                                                    
                                                    if resultado.get("success"):
                                                        sucessos += 1
                                                    else:
                                                        erros.append(f"{aluno['nome']}: {resultado.get('error')}")
                                                else:
                                                    erros.append(f"{aluno['nome']}: Nenhum responsável encontrado")
                                            
                                            except Exception as e:
                                                erros.append(f"{aluno['nome']}: {str(e)}")
                                        
                                        # Mostrar resultados
                                        if sucessos > 0:
                                            st.success(f"✅ Cobranças criadas para {sucessos} alunos!")
                                        
                                        if erros:
                                            st.error(f"❌ {len(erros)} erros encontrados:")
                                            for erro in erros[:5]:  # Mostrar apenas os primeiros 5 erros
                                                st.write(f"   - {erro}")
                                            if len(erros) > 5:
                                                st.write(f"   ... e mais {len(erros) - 5} erros")
                                        
                                        # Limpar sessão após criação
                                        if sucessos > 0:
                                            del st.session_state['ultima_cobranca_parcelada']
                                            st.rerun()
                else:
                    st.info("ℹ️ Selecione pelo menos uma turma para visualizar os alunos")
            
        tab_index += 1
    
    # TAB: Vincular Cobrança Individual
    if cobranca_individual:
        with vincular_tabs[tab_index]:
            st.markdown("#### 📝 Vincular Cobrança Individual")
            
            # Mostrar resumo da cobrança
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.info(f"**📝 Título:** {cobranca_individual['titulo']}")
                st.info(f"**💰 Valor:** R$ {cobranca_individual['valor']:,.2f}")
                st.info(f"**📅 Vencimento:** {formatar_data_br(cobranca_individual['data_vencimento'])}")
            
            with col_info2:
                st.info(f"**🎯 Tipo:** {TIPOS_COBRANCA_DISPLAY.get(cobranca_individual['tipo_cobranca'], 'N/A')}")
                st.info(f"**⚡ Prioridade:** {PRIORIDADES_COBRANCA.get(cobranca_individual['prioridade'], 'N/A')}")
                if cobranca_individual.get('descricao'):
                    st.info(f"**📋 Descrição:** {cobranca_individual['descricao']}")
            
            # Interface para selecionar alunos (similar à parcelada)
            st.markdown("#### 🔍 Selecionar Alunos")
            
            turmas_resultado = listar_turmas_disponiveis()
            if turmas_resultado.get("success"):
                turmas_selecionadas_individual = st.multiselect(
                    "🎓 Filtrar por Turmas (opcional):",
                    options=turmas_resultado["turmas"],
                    help="Deixe vazio para buscar em todas as turmas",
                    key="turmas_individual"
                )
                
                if turmas_selecionadas_individual:
                    mapeamento = obter_mapeamento_turmas()
                    if mapeamento.get("success"):
                        ids_turmas = [mapeamento["mapeamento"][nome] for nome in turmas_selecionadas_individual]
                        
                        resultado_alunos = buscar_alunos_por_turmas(ids_turmas)
                        if resultado_alunos.get("success"):
                            st.markdown("#### 👨‍🎓 Alunos Disponíveis")
                            
                            alunos_selecionados_individual = []
                            
                            for turma_nome, dados_turma in resultado_alunos["alunos_por_turma"].items():
                                with st.expander(f"🎓 {turma_nome} ({len(dados_turma['alunos'])} alunos)", expanded=True):
                                    
                                    selecionar_todos = st.checkbox(f"Selecionar todos de {turma_nome}", key=f"todos_{turma_nome}_individual")
                                    
                                    cols = st.columns(3)
                                    for i, aluno in enumerate(dados_turma["alunos"]):
                                        col_idx = i % 3
                                        with cols[col_idx]:
                                            selecionado = st.checkbox(
                                                f"👨‍🎓 {aluno['nome']}",
                                                value=selecionar_todos,
                                                key=f"aluno_{aluno['id']}_individual"
                                            )
                                            if selecionado:
                                                alunos_selecionados_individual.append({
                                                    "id": aluno["id"],
                                                    "nome": aluno["nome"],
                                                    "turma": turma_nome
                                                })
                            
                            # Resumo e criação
                            if alunos_selecionados_individual:
                                st.markdown("#### 📋 Resumo dos Alunos Selecionados")
                                
                                col_resumo1, col_resumo2 = st.columns(2)
                                
                                with col_resumo1:
                                    st.metric("👨‍🎓 Total de Alunos", len(alunos_selecionados_individual))
                                    valor_total_individual = cobranca_individual['valor'] * len(alunos_selecionados_individual)
                                    st.metric("💰 Valor Total", f"R$ {valor_total_individual:,.2f}")
                                
                                with col_resumo2:
                                    turmas_resumo = {}
                                    for aluno in alunos_selecionados_individual:
                                        turma = aluno["turma"]
                                        if turma not in turmas_resumo:
                                            turmas_resumo[turma] = 0
                                        turmas_resumo[turma] += 1
                                    
                                    st.write("**📊 Por Turma:**")
                                    for turma, quantidade in turmas_resumo.items():
                                        st.write(f"• {turma}: {quantidade} alunos")
                                
                                # Botão para criar
                                if st.button("📝 Criar Cobranças para Alunos Selecionados", type="primary", key="criar_individual"):
                                    with st.spinner(f"Criando cobranças para {len(alunos_selecionados_individual)} alunos..."):
                                        sucessos = 0
                                        erros = []
                                        
                                        for aluno in alunos_selecionados_individual:
                                            try:
                                                responsaveis_aluno = listar_responsaveis_aluno(aluno["id"])
                                                
                                                id_responsavel = None
                                                if responsaveis_aluno.get("success") and responsaveis_aluno.get("responsaveis"):
                                                    for resp in responsaveis_aluno["responsaveis"]:
                                                        if resp.get("responsavel_financeiro"):
                                                            id_responsavel = resp["id"]
                                                            break
                                                    
                                                    if not id_responsavel:
                                                        id_responsavel = responsaveis_aluno["responsaveis"][0]["id"]
                                                
                                                if id_responsavel:
                                                    resultado = cadastrar_cobranca_individual(
                                                        aluno["id"], 
                                                        id_responsavel, 
                                                        cobranca_individual
                                                    )
                                                    
                                                    if resultado.get("success"):
                                                        sucessos += 1
                                                    else:
                                                        erros.append(f"{aluno['nome']}: {resultado.get('error')}")
                                                else:
                                                    erros.append(f"{aluno['nome']}: Nenhum responsável encontrado")
                                            
                                            except Exception as e:
                                                erros.append(f"{aluno['nome']}: {str(e)}")
                                        
                                        # Mostrar resultados
                                        if sucessos > 0:
                                            st.success(f"✅ Cobranças criadas para {sucessos} alunos!")
                                        
                                        if erros:
                                            st.error(f"❌ {len(erros)} erros encontrados:")
                                            for erro in erros[:5]:
                                                st.write(f"   - {erro}")
                                            if len(erros) > 5:
                                                st.write(f"   ... e mais {len(erros) - 5} erros")
                                        
                                        # Limpar sessão
                                        if sucessos > 0:
                                            del st.session_state['ultima_cobranca_individual']
                                            st.rerun()
                else:
                    st.info("ℹ️ Selecione pelo menos uma turma para visualizar os alunos")

def mostrar_interface_gerenciar_cobrancas():
    """Interface para gerenciar cobranças existentes"""
    st.markdown("### 📋 Gerenciar Cobranças Existentes")
    
    # Buscar todas as cobranças criadas
    with st.spinner("Carregando cobranças do sistema..."):
        try:
            # Buscar todas as cobranças do banco de dados
            response = supabase.table("cobrancas").select("""
                id_cobranca, titulo, valor, data_vencimento, status, tipo_cobranca,
                grupo_cobranca, parcela_numero, parcela_total, prioridade,
                alunos!inner(id, nome, turmas!inner(nome_turma)),
                responsaveis!inner(id, nome)
            """).order("data_vencimento").execute()
            
            if not response.data:
                st.info("ℹ️ Nenhuma cobrança encontrada no sistema")
                st.info("💡 Use a aba 'Criar Cobranças' para criar novas cobranças")
                return
            
            cobranças_sistema = response.data
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar cobranças: {str(e)}")
            return
    
    # Filtros
    st.markdown("#### 🔍 Filtros")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        # Filtro por tipo
        tipos_unicos = list(set(c["tipo_cobranca"] for c in cobranças_sistema))
        tipo_filtro = st.multiselect(
            "🎯 Tipo de Cobrança:",
            options=tipos_unicos,
            format_func=lambda x: TIPOS_COBRANCA_DISPLAY.get(x, x)
        )
    
    with col_filtro2:
        # Filtro por status
        status_unicos = list(set(c["status"] for c in cobranças_sistema))
        status_filtro = st.multiselect(
            "📊 Status:",
            options=status_unicos
        )
    
    with col_filtro3:
        # Filtro por turma
        turmas_unicas = list(set(c["alunos"]["turmas"]["nome_turma"] for c in cobranças_sistema))
        turma_filtro = st.multiselect(
            "🎓 Turma:",
            options=turmas_unicas
        )
    
    # Aplicar filtros
    cobranças_filtradas = cobranças_sistema
    
    if tipo_filtro:
        cobranças_filtradas = [c for c in cobranças_filtradas if c["tipo_cobranca"] in tipo_filtro]
    
    if status_filtro:
        cobranças_filtradas = [c for c in cobranças_filtradas if c["status"] in status_filtro]
    
    if turma_filtro:
        cobranças_filtradas = [c for c in cobranças_filtradas if c["alunos"]["turmas"]["nome_turma"] in turma_filtro]
    
    # Estatísticas das cobranças
    if cobranças_filtradas:
        st.markdown("#### 📊 Estatísticas")
        
        total_cobrancas = len(cobranças_filtradas)
        valor_total = sum(float(c["valor"]) for c in cobranças_filtradas)
        pendentes = len([c for c in cobranças_filtradas if c["status"] == "Pendente"])
        pagas = len([c for c in cobranças_filtradas if c["status"] == "Pago"])
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("📋 Total de Cobranças", total_cobrancas)
        
        with col_stat2:
            st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
        
        with col_stat3:
            st.metric("⏳ Pendentes", pendentes)
        
        with col_stat4:
            st.metric("✅ Pagas", pagas)
        
        # Agrupar por grupo_cobranca (parcelas relacionadas)
        grupos = {}
        individuais = []
        
        for cobranca in cobranças_filtradas:
            if cobranca.get("grupo_cobranca"):
                grupo = cobranca["grupo_cobranca"]
                if grupo not in grupos:
                    grupos[grupo] = []
                grupos[grupo].append(cobranca)
            else:
                individuais.append(cobranca)
        
        # Mostrar grupos de parcelas
        if grupos:
            st.markdown("#### 📦 Cobranças Parceladas")
            
            for grupo, parcelas in grupos.items():
                primeiro = parcelas[0]
                total_grupo = sum(float(p["valor"]) for p in parcelas)
                pagas_grupo = len([p for p in parcelas if p["status"] == "Pago"])
                pendentes_grupo = len([p for p in parcelas if p["status"] == "Pendente"])
                
                # Título do grupo baseado na primeira parcela
                titulo_grupo = primeiro['titulo'].split(' - Parcela')[0] if ' - Parcela' in primeiro['titulo'] else primeiro['titulo']
                tipo_display = TIPOS_COBRANCA_DISPLAY.get(primeiro['tipo_cobranca'], primeiro['tipo_cobranca'])
                
                with st.expander(f"📦 {tipo_display} - {titulo_grupo} ({len(parcelas)} parcelas) - R$ {total_grupo:,.2f} ({pagas_grupo}/{len(parcelas)} pagas)", expanded=False):
                    
                    # Resumo do grupo
                    col_grupo1, col_grupo2 = st.columns(2)
                    
                    with col_grupo1:
                        st.info(f"**👨‍🎓 Aluno:** {primeiro['alunos']['nome']}")
                        st.info(f"**🎓 Turma:** {primeiro['alunos']['turmas']['nome_turma']}")
                        st.info(f"**👤 Responsável:** {primeiro['responsaveis']['nome']}")
                    
                    with col_grupo2:
                        st.info(f"**📦 Total de Parcelas:** {len(parcelas)}")
                        st.info(f"**💰 Valor Total:** R$ {total_grupo:,.2f}")
                        st.info(f"**📊 Status:** {pagas_grupo} pagas, {pendentes_grupo} pendentes")
                    
                    # Lista das parcelas
                    parcelas_ordenadas = sorted(parcelas, key=lambda x: x["parcela_numero"])
                    
                    for parcela in parcelas_ordenadas:
                        col_parcela1, col_parcela2, col_parcela3, col_parcela4 = st.columns([3, 2, 2, 1])
                        
                        # Status emoji
                        if parcela["status"] == "Pago":
                            emoji = "✅"
                            cor = "success"
                        elif parcela["status"] == "Pendente":
                            emoji = "⏳"
                            cor = "warning"
                        elif parcela["status"] == "Cancelado":
                            emoji = "❌"
                            cor = "secondary"
                        else:
                            emoji = "❓"
                            cor = "info"
                        
                        with col_parcela1:
                            st.write(f"{emoji} **Parcela {parcela['parcela_numero']}/{parcela['parcela_total']}**")
                        
                        with col_parcela2:
                            st.write(f"💰 R$ {float(parcela['valor']):,.2f}")
                        
                        with col_parcela3:
                            st.write(f"📅 {formatar_data_br(parcela['data_vencimento'])}")
                        
                        with col_parcela4:
                            if parcela["status"] == "Pendente":
                                if st.button("✅", key=f"pagar_grupo_{parcela['id_cobranca']}", help="Marcar como pago"):
                                    data_hoje = date.today().isoformat()
                                    resultado = marcar_cobranca_como_paga(parcela['id_cobranca'], data_hoje)
                                    if resultado.get("success"):
                                        st.success("✅ Parcela marcada como paga!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro: {resultado.get('error')}")
        
        # Mostrar cobranças individuais
        if individuais:
            st.markdown("#### 📝 Cobranças Individuais")
            
            for cobranca in individuais:
                tipo_display = TIPOS_COBRANCA_DISPLAY.get(cobranca['tipo_cobranca'], cobranca['tipo_cobranca'])
                
                # Status emoji
                if cobranca["status"] == "Pago":
                    emoji = "✅"
                    cor = "success"
                elif cobranca["status"] == "Pendente":
                    emoji = "⏳"
                    cor = "warning"
                elif cobranca["status"] == "Cancelado":
                    emoji = "❌"
                    cor = "secondary"
                else:
                    emoji = "❓"
                    cor = "info"
                
                with st.expander(f"{emoji} {tipo_display} - {cobranca['titulo']} - R$ {float(cobranca['valor']):,.2f}", expanded=False):
                    
                    col_ind1, col_ind2, col_ind3 = st.columns([2, 2, 1])
                    
                    with col_ind1:
                        st.write(f"**👨‍🎓 Aluno:** {cobranca['alunos']['nome']}")
                        st.write(f"**🎓 Turma:** {cobranca['alunos']['turmas']['nome_turma']}")
                        st.write(f"**👤 Responsável:** {cobranca['responsaveis']['nome']}")
                    
                    with col_ind2:
                        st.write(f"**💰 Valor:** R$ {float(cobranca['valor']):,.2f}")
                        st.write(f"**📅 Vencimento:** {formatar_data_br(cobranca['data_vencimento'])}")
                        st.write(f"**📊 Status:** {cobranca['status']}")
                    
                    with col_ind3:
                        if cobranca["status"] == "Pendente":
                            if st.button("✅ Pagar", key=f"pagar_individual_{cobranca['id_cobranca']}", type="primary"):
                                data_hoje = date.today().isoformat()
                                resultado = marcar_cobranca_como_paga(cobranca['id_cobranca'], data_hoje)
                                if resultado.get("success"):
                                    st.success("✅ Cobrança marcada como paga!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro: {resultado.get('error')}")
                        
                        if st.button("🗑️ Cancelar", key=f"cancelar_individual_{cobranca['id_cobranca']}", help="Cancelar cobrança"):
                            resultado = cancelar_cobranca(cobranca['id_cobranca'], "Cancelado via interface")
                            if resultado.get("success"):
                                st.success("✅ Cobrança cancelada!")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro: {resultado.get('error')}")
        
        # Ações em lote
        st.markdown("---")
        st.markdown("#### ⚡ Ações em Lote")
        
        col_lote1, col_lote2 = st.columns(2)
        
        with col_lote1:
            if st.button("✅ Marcar Todas Pendentes como Pagas", help="Marca todas as cobranças pendentes como pagas"):
                pendentes_ids = [c["id_cobranca"] for c in cobranças_filtradas if c["status"] == "Pendente"]
                
                if pendentes_ids:
                    with st.spinner(f"Marcando {len(pendentes_ids)} cobranças como pagas..."):
                        sucessos = 0
                        erros = []
                        data_hoje = date.today().isoformat()
                        
                        for id_cobranca in pendentes_ids:
                            resultado = marcar_cobranca_como_paga(id_cobranca, data_hoje)
                            if resultado.get("success"):
                                sucessos += 1
                            else:
                                erros.append(f"ID {id_cobranca}: {resultado.get('error')}")
                        
                        if sucessos > 0:
                            st.success(f"✅ {sucessos} cobranças marcadas como pagas!")
                        
                        if erros:
                            st.error(f"❌ {len(erros)} erros encontrados")
                        
                        st.rerun()
                else:
                    st.info("ℹ️ Nenhuma cobrança pendente encontrada")
        
        with col_lote2:
            if st.button("📊 Exportar Relatório", help="Exporta relatório das cobranças filtradas"):
                # Preparar dados para exportação
                dados_exportacao = []
                
                for cobranca in cobranças_filtradas:
                    dados_exportacao.append({
                        "ID": cobranca["id_cobranca"],
                        "Título": cobranca["titulo"],
                        "Aluno": cobranca["alunos"]["nome"],
                        "Turma": cobranca["alunos"]["turmas"]["nome_turma"],
                        "Responsável": cobranca["responsaveis"]["nome"],
                        "Tipo": TIPOS_COBRANCA_DISPLAY.get(cobranca["tipo_cobranca"], cobranca["tipo_cobranca"]),
                        "Valor": f"R$ {float(cobranca['valor']):,.2f}",
                        "Vencimento": formatar_data_br(cobranca["data_vencimento"]),
                        "Status": cobranca["status"],
                        "Grupo": cobranca.get("grupo_cobranca", "Individual"),
                        "Parcela": f"{cobranca.get('parcela_numero', 1)}/{cobranca.get('parcela_total', 1)}" if cobranca.get("grupo_cobranca") else "N/A"
                    })
                
                df = pd.DataFrame(dados_exportacao)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name=f"relatorio_cobrancas_{date.today().isoformat()}.csv",
                    mime="text/csv"
                )
    
    else:
        st.info("ℹ️ Nenhuma cobrança encontrada com os filtros aplicados")

def mostrar_interface_relatorios_cobrancas():
    """Interface para relatórios de cobranças"""
    st.markdown("### 📊 Relatórios de Cobranças")
    
    # Carregar dados para relatórios
    with st.spinner("Carregando dados para relatórios..."):
        try:
            response = supabase.table("cobrancas").select("""
                id_cobranca, titulo, valor, data_vencimento, status, tipo_cobranca,
                grupo_cobranca, parcela_numero, parcela_total, prioridade, inserted_at,
                alunos!inner(id, nome, turmas!inner(nome_turma)),
                responsaveis!inner(id, nome)
            """).execute()
            
            if not response.data:
                st.info("ℹ️ Nenhuma cobrança encontrada no sistema")
                return
            
            cobranças_dados = response.data
            
        except Exception as e:
            st.error(f"❌ Erro ao carregar dados: {str(e)}")
            return
    
    # Relatórios disponíveis
    relatorio_tabs = st.tabs([
        "📊 Visão Geral",
        "🎯 Por Tipo de Cobrança", 
        "🎓 Por Turma",
        "⏰ Por Status",
        "📅 Por Período"
    ])
    
    # TAB: Visão Geral
    with relatorio_tabs[0]:
        st.markdown("#### 📊 Visão Geral do Sistema")
        
        # Métricas gerais
        total_cobrancas = len(cobranças_dados)
        valor_total_sistema = sum(float(c["valor"]) for c in cobranças_dados)
        cobrancas_pendentes = len([c for c in cobranças_dados if c["status"] == "Pendente"])
        cobrancas_pagas = len([c for c in cobranças_dados if c["status"] == "Pago"])
        
        col_geral1, col_geral2, col_geral3, col_geral4 = st.columns(4)
        
        with col_geral1:
            st.metric("📋 Total de Cobranças", total_cobrancas)
        
        with col_geral2:
            st.metric("💰 Valor Total", f"R$ {valor_total_sistema:,.2f}")
        
        with col_geral3:
            st.metric("⏳ Pendentes", cobrancas_pendentes, delta=f"{(cobrancas_pendentes/total_cobrancas*100):.1f}%")
        
        with col_geral4:
            st.metric("✅ Pagas", cobrancas_pagas, delta=f"{(cobrancas_pagas/total_cobrancas*100):.1f}%")
        
        # Gráficos
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            # Gráfico de status
            status_counts = {}
            for cobranca in cobranças_dados:
                status = cobranca["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
            
            st.markdown("**📊 Distribuição por Status**")
            for status, count in status_counts.items():
                percentage = (count / total_cobrancas) * 100
                st.write(f"• {status}: {count} ({percentage:.1f}%)")
        
        with col_graf2:
            # Gráfico de tipos
            tipo_counts = {}
            for cobranca in cobranças_dados:
                tipo = cobranca["tipo_cobranca"]
                if tipo not in tipo_counts:
                    tipo_counts[tipo] = 0
                tipo_counts[tipo] += 1
            
            st.markdown("**🎯 Distribuição por Tipo**")
            for tipo, count in tipo_counts.items():
                tipo_display = TIPOS_COBRANCA_DISPLAY.get(tipo, tipo)
                percentage = (count / total_cobrancas) * 100
                st.write(f"• {tipo_display}: {count} ({percentage:.1f}%)")
    
    # TAB: Por Tipo
    with relatorio_tabs[1]:
        st.markdown("#### 🎯 Relatório por Tipo de Cobrança")
        
        tipos_stats = {}
        for cobranca in cobranças_dados:
            tipo = cobranca["tipo_cobranca"]
            if tipo not in tipos_stats:
                tipos_stats[tipo] = {
                    "total": 0,
                    "valor_total": 0,
                    "pendentes": 0,
                    "pagas": 0,
                    "valor_pendente": 0,
                    "valor_pago": 0
                }
            
            tipos_stats[tipo]["total"] += 1
            tipos_stats[tipo]["valor_total"] += float(cobranca["valor"])
            
            if cobranca["status"] == "Pendente":
                tipos_stats[tipo]["pendentes"] += 1
                tipos_stats[tipo]["valor_pendente"] += float(cobranca["valor"])
            elif cobranca["status"] == "Pago":
                tipos_stats[tipo]["pagas"] += 1
                tipos_stats[tipo]["valor_pago"] += float(cobranca["valor"])
        
        for tipo, stats in tipos_stats.items():
            tipo_display = TIPOS_COBRANCA_DISPLAY.get(tipo, tipo)
            
            with st.expander(f"{tipo_display} - {stats['total']} cobranças - R$ {stats['valor_total']:,.2f}", expanded=True):
                col_tipo1, col_tipo2, col_tipo3, col_tipo4 = st.columns(4)
                
                with col_tipo1:
                    st.metric("📋 Total", stats["total"])
                
                with col_tipo2:
                    st.metric("💰 Valor Total", f"R$ {stats['valor_total']:,.2f}")
                
                with col_tipo3:
                    st.metric("⏳ Pendentes", stats["pendentes"], delta=f"R$ {stats['valor_pendente']:,.2f}")
                
                with col_tipo4:
                    st.metric("✅ Pagas", stats["pagas"], delta=f"R$ {stats['valor_pago']:,.2f}")
    
    # TAB: Por Turma
    with relatorio_tabs[2]:
        st.markdown("#### 🎓 Relatório por Turma")
        
        turmas_stats = {}
        for cobranca in cobranças_dados:
            turma = cobranca["alunos"]["turmas"]["nome_turma"]
            if turma not in turmas_stats:
                turmas_stats[turma] = {
                    "total": 0,
                    "valor_total": 0,
                    "pendentes": 0,
                    "pagas": 0,
                    "alunos": set()
                }
            
            turmas_stats[turma]["total"] += 1
            turmas_stats[turma]["valor_total"] += float(cobranca["valor"])
            turmas_stats[turma]["alunos"].add(cobranca["alunos"]["id"])
            
            if cobranca["status"] == "Pendente":
                turmas_stats[turma]["pendentes"] += 1
            elif cobranca["status"] == "Pago":
                turmas_stats[turma]["pagas"] += 1
        
        for turma, stats in turmas_stats.items():
            with st.expander(f"🎓 {turma} - {len(stats['alunos'])} alunos - {stats['total']} cobranças", expanded=True):
                col_turma1, col_turma2, col_turma3, col_turma4 = st.columns(4)
                
                with col_turma1:
                    st.metric("👨‍🎓 Alunos", len(stats["alunos"]))
                
                with col_turma2:
                    st.metric("📋 Cobranças", stats["total"])
                
                with col_turma3:
                    st.metric("💰 Valor Total", f"R$ {stats['valor_total']:,.2f}")
                
                with col_turma4:
                    taxa_pagamento = (stats["pagas"] / stats["total"] * 100) if stats["total"] > 0 else 0
                    st.metric("📊 Taxa Pagamento", f"{taxa_pagamento:.1f}%")
    
    # TAB: Por Status
    with relatorio_tabs[3]:
        st.markdown("#### ⏰ Relatório por Status")
        
        status_stats = {}
        for cobranca in cobranças_dados:
            status = cobranca["status"]
            if status not in status_stats:
                status_stats[status] = {
                    "total": 0,
                    "valor_total": 0,
                    "alunos": set()
                }
            
            status_stats[status]["total"] += 1
            status_stats[status]["valor_total"] += float(cobranca["valor"])
            status_stats[status]["alunos"].add(cobranca["alunos"]["id"])
        
        for status, stats in status_stats.items():
            emoji = "✅" if status == "Pago" else "⏳" if status == "Pendente" else "❌"
            
            with st.expander(f"{emoji} {status} - {stats['total']} cobranças - R$ {stats['valor_total']:,.2f}", expanded=True):
                col_status1, col_status2, col_status3 = st.columns(3)
                
                with col_status1:
                    st.metric("📋 Cobranças", stats["total"])
                
                with col_status2:
                    st.metric("💰 Valor Total", f"R$ {stats['valor_total']:,.2f}")
                
                with col_status3:
                    st.metric("👨‍🎓 Alunos Únicos", len(stats["alunos"]))
    
    # TAB: Por Período
    with relatorio_tabs[4]:
        st.markdown("#### 📅 Relatório por Período")
        
        # Filtros de período
        col_periodo1, col_periodo2 = st.columns(2)
        
        with col_periodo1:
            data_inicio = st.date_input(
                "📅 Data Início:",
                value=date.today() - timedelta(days=30),
                help="Data de início do período para análise"
            )
        
        with col_periodo2:
            data_fim = st.date_input(
                "📅 Data Fim:",
                value=date.today(),
                help="Data de fim do período para análise"
            )
        
        # Filtrar cobranças por período
        cobranças_periodo = []
        for cobranca in cobranças_dados:
            data_vencimento = datetime.strptime(cobranca["data_vencimento"], "%Y-%m-%d").date()
            if data_inicio <= data_vencimento <= data_fim:
                cobranças_periodo.append(cobranca)
        
        if cobranças_periodo:
            st.markdown(f"#### 📊 Análise do Período: {formatar_data_br(data_inicio.isoformat())} a {formatar_data_br(data_fim.isoformat())}")
            
            # Métricas do período
            total_periodo = len(cobranças_periodo)
            valor_total_periodo = sum(float(c["valor"]) for c in cobranças_periodo)
            pendentes_periodo = len([c for c in cobranças_periodo if c["status"] == "Pendente"])
            pagas_periodo = len([c for c in cobranças_periodo if c["status"] == "Pago"])
            
            col_periodo_stats1, col_periodo_stats2, col_periodo_stats3, col_periodo_stats4 = st.columns(4)
            
            with col_periodo_stats1:
                st.metric("📋 Total no Período", total_periodo)
            
            with col_periodo_stats2:
                st.metric("💰 Valor Total", f"R$ {valor_total_periodo:,.2f}")
            
            with col_periodo_stats3:
                st.metric("⏳ Pendentes", pendentes_periodo, delta=f"{(pendentes_periodo/total_periodo*100):.1f}%")
            
            with col_periodo_stats4:
                st.metric("✅ Pagas", pagas_periodo, delta=f"{(pagas_periodo/total_periodo*100):.1f}%")
            
            # Gráfico por data
            st.markdown("**📈 Cobranças por Data de Vencimento**")
            
            # Agrupar por data
            datas_valores = {}
            for cobranca in cobranças_periodo:
                data_venc = cobranca["data_vencimento"]
                if data_venc not in datas_valores:
                    datas_valores[data_venc] = 0
                datas_valores[data_venc] += float(cobranca["valor"])
            
            # Mostrar resumo por data
            for data, valor in sorted(datas_valores.items()):
                cobranças_data = [c for c in cobranças_periodo if c["data_vencimento"] == data]
                st.write(f"📅 {formatar_data_br(data)}: {len(cobranças_data)} cobranças - R$ {valor:,.2f}")
        
        else:
            st.info("ℹ️ Nenhuma cobrança encontrada no período selecionado")

# ==========================================================
# 🚀 EXECUTAR APLICAÇÃO
# ==========================================================

if __name__ == "__main__":
    main() 