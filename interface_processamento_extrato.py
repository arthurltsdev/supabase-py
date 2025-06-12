#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 INTERFACE DE PROCESSAMENTO DO EXTRATO PIX - VERSÃO OTIMIZADA
==============================================================

Interface eficiente para processar pagamentos do extrato PIX,
cadastrar responsáveis e vincular com alunos.

Versão focada nos requisitos específicos do usuário.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# Importar funções otimizadas
from funcoes_extrato_otimizadas import (
    listar_extrato_com_sem_responsavel,
    buscar_alunos_para_dropdown,
    listar_responsaveis_aluno,
    listar_alunos_vinculados_responsavel,
    cadastrar_responsavel_e_vincular,
    registrar_pagamento_do_extrato,
    registrar_pagamentos_multiplos_do_extrato,
    atualizar_aluno_campos,
    atualizar_vinculo_responsavel,
    obter_estatisticas_extrato,
    verificar_responsavel_existe
)

# Configuração da página
st.set_page_config(
    page_title="Processamento Extrato PIX",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stDataFrame {font-size: 12px;}
    .metric-card {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
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
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 🔧 FUNÇÕES AUXILIARES DA INTERFACE
# ==========================================================

def init_session_state():
    """Inicializa o estado da sessão"""
    defaults = {
        'acoes_selecionadas': {},
        'historico_acoes': [],
        'filtro_data_inicio': datetime.now() - timedelta(days=30),
        'filtro_data_fim': datetime.now(),
        'filtro_status': 'novo',
        'dados_extrato': None,
        'last_update': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def carregar_dados_extrato():
    """Carrega dados do extrato com filtros aplicados"""
    with st.spinner("Carregando dados do extrato..."):
        resultado = listar_extrato_com_sem_responsavel(
            data_inicio=st.session_state.filtro_data_inicio.strftime("%Y-%m-%d"),
            data_fim=st.session_state.filtro_data_fim.strftime("%Y-%m-%d")
        )
        
        if resultado.get("success"):
            st.session_state.dados_extrato = resultado
            st.session_state.last_update = datetime.now()
            return True
        else:
            st.error(f"Erro ao carregar dados: {resultado.get('error')}")
            return False

def mostrar_modal_pagamento_avancado(registro: Dict, id_responsavel: str) -> Optional[Dict]:
    """
    Modal para configurar pagamento avançado (múltiplos tipos/alunos)
    
    Args:
        registro: Dados do registro do extrato
        id_responsavel: ID do responsável
        
    Returns:
        Dict com configuração dos pagamentos ou None se cancelado
    """
    
    # Buscar alunos vinculados ao responsável
    alunos_vinculados = listar_alunos_vinculados_responsavel(id_responsavel)
    
    if not alunos_vinculados.get("success") or not alunos_vinculados.get("alunos"):
        st.error("❌ Nenhum aluno encontrado vinculado a este responsável!")
        return None
    
    alunos = alunos_vinculados["alunos"]
    valor_total = float(registro.get("valor", 0))
    
    # Cabeçalho mais destacado
    st.markdown(f"""
    <div class="info-card">
        <h3>⚙️ Configuração Avançada de Pagamento</h3>
        <p><strong>💰 Valor Total:</strong> R$ {valor_total:.2f}</p>
        <p><strong>👤 Remetente:</strong> {registro.get('nome_remetente')}</p>
        <p><strong>📅 Data:</strong> {registro.get('data_pagamento')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Container para os pagamentos configurados
    if 'pagamentos_config' not in st.session_state:
        st.session_state.pagamentos_config = [{}]  # Começar com 1 pagamento
    
    # Cabeçalho e controles
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 📋 Configure cada pagamento individual:")
    
    with col2:
        if st.button("➕ Adicionar Pagamento", type="secondary"):
            st.session_state.pagamentos_config.append({})
            st.rerun()
    
    with col3:
        if st.button("❌ Cancelar Configuração", type="secondary"):
            if 'pagamentos_config' in st.session_state:
                del st.session_state.pagamentos_config
            return None
    
    # Lista para armazenar as configurações
    pagamentos_detalhados = []
    valor_total_configurado = 0.0
    
    # Criar formulário para cada pagamento
    for i, config in enumerate(st.session_state.pagamentos_config):
        # Usar container com separador visual em vez de expander
        st.markdown(f"### 💰 Pagamento {i+1}")
        
        # Container para este pagamento
        container = st.container()
        
        with container:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Seleção do aluno
                opcoes_alunos = {aluno["label"]: aluno for aluno in alunos}
                aluno_selecionado = st.selectbox(
                    "👨‍🎓 Aluno:",
                    options=list(opcoes_alunos.keys()),
                    key=f"aluno_pag_{i}",
                    index=list(opcoes_alunos.keys()).index(config.get("aluno_label")) if config.get("aluno_label") in opcoes_alunos else 0
                )
                
                aluno_data = opcoes_alunos[aluno_selecionado]
                
            with col2:
                # Tipo de pagamento
                tipo_pagamento = st.selectbox(
                    "💳 Tipo:",
                    ["matricula", "mensalidade", "material", "fardamento", "evento", "outro"],
                    key=f"tipo_pag_{i}",
                    index=["matricula", "mensalidade", "material", "fardamento", "evento", "outro"].index(config.get("tipo_pagamento")) if config.get("tipo_pagamento") else 0
                )
            
            with col3:
                # Botão para remover (só se houver mais de 1)
                if len(st.session_state.pagamentos_config) > 1:
                    if st.button("🗑️ Remover", key=f"remove_pag_{i}"):
                        st.session_state.pagamentos_config.pop(i)
                        st.rerun()
            
            # Valor do pagamento
            col1, col2 = st.columns(2)
            
            with col1:
                # Se é o último pagamento, calcular valor restante automaticamente
                if i == len(st.session_state.pagamentos_config) - 1 and len(st.session_state.pagamentos_config) > 1:
                    valor_restante = valor_total - valor_total_configurado
                    valor_pagamento = st.number_input(
                        "💰 Valor:",
                        min_value=0.01,
                        max_value=valor_restante,
                        value=max(0.01, valor_restante),
                        step=0.01,
                        key=f"valor_pag_{i}",
                        help=f"Valor restante: R$ {valor_restante:.2f}"
                    )
                else:
                    valor_pagamento = st.number_input(
                        "💰 Valor:",
                        min_value=0.01,
                        max_value=valor_total,
                        value=config.get("valor", valor_total if len(st.session_state.pagamentos_config) == 1 else 0.01),
                        step=0.01,
                        key=f"valor_pag_{i}"
                    )
            
            with col2:
                observacoes = st.text_input(
                    "📝 Observações:",
                    value=config.get("observacoes", ""),
                    key=f"obs_pag_{i}"
                )
            
            # Atualizar configuração
            st.session_state.pagamentos_config[i] = {
                "aluno_label": aluno_selecionado,
                "aluno_data": aluno_data,
                "tipo_pagamento": tipo_pagamento,
                "valor": valor_pagamento,
                "observacoes": observacoes
            }
            
            # Adicionar aos pagamentos detalhados
            pagamentos_detalhados.append({
                "id_aluno": aluno_data["id"],
                "nome_aluno": aluno_data["nome"],
                "tipo_pagamento": tipo_pagamento,
                "valor": valor_pagamento,
                "observacoes": observacoes
            })
            
            valor_total_configurado += valor_pagamento
        
        # Separador visual entre pagamentos
        if i < len(st.session_state.pagamentos_config) - 1:
            st.markdown("---")
    
    # Resumo e validação
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Valor Total", f"R$ {valor_total:.2f}")
    
    with col2:
        st.metric("📊 Configurado", f"R$ {valor_total_configurado:.2f}")
        
    with col3:
        diferenca = valor_total - valor_total_configurado
        cor = "normal" if abs(diferenca) < 0.01 else "inverse"
        st.metric("⚖️ Diferença", f"R$ {diferenca:.2f}", delta_color=cor)
    
    # Validações
    valores_ok = abs(diferenca) < 0.01
    
    if not valores_ok:
        st.error(f"❌ Os valores não conferem! Diferença: R$ {diferenca:.2f}")
        return None
    
    # Verificar duplicatas de aluno+tipo
    combinacoes = set()
    for pag in pagamentos_detalhados:
        combinacao = (pag["id_aluno"], pag["tipo_pagamento"])
        if combinacao in combinacoes:
            st.error(f"❌ Combinação duplicada: {pag['nome_aluno']} + {pag['tipo_pagamento']}")
            return None
        combinacoes.add(combinacao)
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ CONFIRMAR PAGAMENTOS", type="primary", disabled=not valores_ok):
            # Limpar estado
            del st.session_state.pagamentos_config
            
            return {
                "configuracao_multipla": True,
                "pagamentos_detalhados": pagamentos_detalhados,
                "valor_total": valor_total_configurado,
                "total_pagamentos": len(pagamentos_detalhados)
            }
    
    with col2:
        if st.button("🔄 RESETAR"):
            st.session_state.pagamentos_config = [{}]
            st.rerun()
    
    with col3:
        if st.button("❌ CANCELAR"):
            if 'pagamentos_config' in st.session_state:
                del st.session_state.pagamentos_config
            return None
    
    return None

def mostrar_formulario_responsavel(nome_sugerido: str = ""):
    """Formulário para cadastrar novo responsável"""
    with st.form("form_novo_responsavel", clear_on_submit=True):
        st.subheader("📝 Cadastrar Novo Responsável")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo*", value=nome_sugerido, key="resp_nome")
            cpf = st.text_input("CPF", key="resp_cpf")
            telefone = st.text_input("Telefone", key="resp_telefone")
        
        with col2:
            email = st.text_input("Email", key="resp_email")
            endereco = st.text_area("Endereço", key="resp_endereco")
            tipo_relacao = st.selectbox(
                "Tipo de Relação*",
                ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"],
                key="resp_tipo"
            )
        
        responsavel_financeiro = st.checkbox("É responsável financeiro", value=True, key="resp_financeiro")
        
        # Busca de alunos
        st.subheader("🎓 Vincular com Aluno")
        busca_aluno = st.text_input("🔍 Digite o nome do aluno", key="busca_aluno")
        
        aluno_selecionado = None
        if busca_aluno and len(busca_aluno) >= 2:
            resultado_busca = buscar_alunos_para_dropdown(busca_aluno)
            if resultado_busca.get("success") and resultado_busca.get("opcoes"):
                opcoes = {op["label"]: op for op in resultado_busca["opcoes"]}
                aluno_escolhido = st.selectbox("Selecione o aluno:", options=list(opcoes.keys()), key="select_aluno")
                aluno_selecionado = opcoes[aluno_escolhido]
        
        submitted = st.form_submit_button("💾 Cadastrar e Vincular", type="primary")
        
        if submitted:
            if not nome:
                st.error("Nome é obrigatório!")
                return None
            
            if not aluno_selecionado:
                st.error("Selecione um aluno para vincular!")
                return None
            
            # Verificar se responsável já existe
            check_resp = verificar_responsavel_existe(nome)
            if check_resp.get("existe"):
                st.warning("⚠️ Já existe responsável com nome similar!")
                for resp in check_resp.get("responsaveis_similares", []):
                    st.write(f"- {resp['nome']} (ID: {resp['id']})")
                
                if st.button("Continuar mesmo assim"):
                    pass
                else:
                    return None
            
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
            
            if resultado.get("success"):
                st.success(f"✅ Responsável {nome} cadastrado e vinculado com {aluno_selecionado['nome']}!")
                return resultado
            else:
                st.error(f"❌ Erro: {resultado.get('error')}")
                return None

def mostrar_informacoes_editaveis_aluno(aluno_data: Dict):
    """Mostra informações editáveis do aluno"""
    st.subheader(f"📚 Informações de {aluno_data['nome']}")
    
    # Buscar dados completos do aluno
    aluno_response = supabase.table("alunos").select("""
        id, nome, turno, data_nascimento, dia_vencimento, 
        data_matricula, valor_mensalidade, mensalidades_geradas,
        turmas!inner(nome_turma)
    """).eq("id", aluno_data['id']).execute()
    
    if not aluno_response.data:
        st.error("❌ Dados do aluno não encontrados")
        return
    
    aluno_completo = aluno_response.data[0]
    
    # Layout em colunas para melhor organização
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 Dados Básicos:**")
        st.write(f"• **Nome:** {aluno_completo['nome']}")
        st.write(f"• **Turma:** {aluno_completo['turmas']['nome_turma']}")
        st.write(f"• **Data Nascimento:** {aluno_completo.get('data_nascimento', 'Não informado')}")
        st.write(f"• **Data Matrícula:** {aluno_completo.get('data_matricula', 'Não informado')}")
    
    with col2:
        st.markdown("**💰 Dados Financeiros:**")
        st.write(f"• **Valor Mensalidade:** R$ {aluno_completo.get('valor_mensalidade', 0):.2f}")
        st.write(f"• **Dia Vencimento:** {aluno_completo.get('dia_vencimento', 'Não definido')}")
        st.write(f"• **Turno:** {aluno_completo.get('turno', 'Não informado')}")
    
    # Formulário de edição
    st.markdown("---")
    st.markdown("### ✏️ Editar Informações")
    
    with st.form(f"edit_aluno_{aluno_data['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            novo_valor_mensalidade = st.number_input(
                "💰 Valor da Mensalidade",
                min_value=0.0,
                step=10.0,
                value=float(aluno_completo.get('valor_mensalidade', 0)),
                key=f"valor_mens_{aluno_data['id']}"
            )
            
            novo_dia_vencimento = st.selectbox(
                "📅 Dia de Vencimento",
                options=list(range(1, 32)),
                index=int(aluno_completo.get('dia_vencimento', 5)) - 1 if aluno_completo.get('dia_vencimento') else 4,
                key=f"dia_venc_{aluno_data['id']}"
            )
        
        with col2:
            novo_turno = st.selectbox(
                "🕐 Turno",
                options=["Matutino", "Vespertino", "Integral"],
                index=["Matutino", "Vespertino", "Integral"].index(aluno_completo.get('turno', 'Matutino')) if aluno_completo.get('turno') in ["Matutino", "Vespertino", "Integral"] else 0,
                key=f"turno_{aluno_data['id']}"
            )
            
            nova_data_nascimento = st.date_input(
                "🎂 Data de Nascimento",
                value=pd.to_datetime(aluno_completo.get('data_nascimento')).date() if aluno_completo.get('data_nascimento') else None,
                key=f"data_nasc_{aluno_data['id']}"
            )
        
        if st.form_submit_button("💾 Salvar Alterações", type="primary"):
            campos_update = {
                "valor_mensalidade": novo_valor_mensalidade,
                "dia_vencimento": str(novo_dia_vencimento),
                "turno": novo_turno,
                "data_nascimento": nova_data_nascimento.isoformat() if nova_data_nascimento else None
            }
            
            resultado = atualizar_aluno_campos(aluno_data["id"], campos_update)
            
            if resultado.get("success"):
                st.success("✅ Informações do aluno atualizadas!")
                st.rerun()
            else:
                st.error(f"❌ Erro: {resultado.get('error')}")

def mostrar_gestao_responsaveis_aluno(id_aluno: str, nome_aluno: str):
    """Interface para gerenciar responsáveis de um aluno"""
    st.subheader(f"👥 Responsáveis de {nome_aluno}")
    
    # Listar responsáveis atuais
    responsaveis = listar_responsaveis_aluno(id_aluno)
    
    if responsaveis.get("success") and responsaveis.get("responsaveis"):
        df_resp = pd.DataFrame(responsaveis["responsaveis"])
        
        # Mostrar em formato editável
        edited_df = st.data_editor(
            df_resp[["nome", "tipo_relacao", "responsavel_financeiro", "telefone", "email"]],
            column_config={
                "tipo_relacao": st.column_config.SelectboxColumn(
                    "Tipo de Relação",
                    options=["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"]
                ),
                "responsavel_financeiro": st.column_config.CheckboxColumn("Resp. Financeiro")
            },
            disabled=["nome", "telefone", "email"],
            use_container_width=True,
            key=f"edit_resp_{id_aluno}"
        )
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Alterações", key=f"save_{id_aluno}"):
                # Processar alterações
                for idx, row in edited_df.iterrows():
                    if idx < len(df_resp):
                        id_vinculo = df_resp.iloc[idx]["id_vinculo"]
                        resultado = atualizar_vinculo_responsavel(
                            id_vinculo=id_vinculo,
                            tipo_relacao=row["tipo_relacao"],
                            responsavel_financeiro=row["responsavel_financeiro"]
                        )
                        if not resultado.get("success"):
                            st.error(f"Erro ao atualizar: {resultado.get('error')}")
                
                st.success("✅ Alterações salvas!")
                st.rerun()
        
        with col2:
            if st.button("➕ Adicionar Responsável", key=f"add_{id_aluno}"):
                st.session_state[f"show_add_resp_{id_aluno}"] = True
    
    else:
        st.info("Nenhum responsável vinculado a este aluno")
        if st.button("➕ Adicionar Primeiro Responsável", key=f"add_first_{id_aluno}"):
            st.session_state[f"show_add_resp_{id_aluno}"] = True
    
    # Formulário para adicionar responsável
    if st.session_state.get(f"show_add_resp_{id_aluno}", False):
        st.markdown("---")
        resultado = mostrar_formulario_responsavel()
        if resultado:
            st.session_state[f"show_add_resp_{id_aluno}"] = False
            st.rerun()

# ==========================================================
# 🎨 INTERFACE PRINCIPAL
# ==========================================================

def main():
    """Função principal da interface"""
    
    # Inicializar estado
    init_session_state()
    
    # Header
    st.title("💰 Processamento do Extrato PIX")
    st.markdown("Interface otimizada para processar pagamentos e gerenciar responsáveis")
    
    # Sidebar com filtros e estatísticas
    with st.sidebar:
        st.header("🔍 Filtros")
        
        # Filtros de data
        data_inicio = st.date_input(
            "Data Início",
            value=st.session_state.filtro_data_inicio,
            key="filtro_inicio"
        )
        
        data_fim = st.date_input(
            "Data Fim",
            value=st.session_state.filtro_data_fim,
            key="filtro_fim"
        )
        
        if st.button("🔄 Atualizar Dados", type="primary"):
            st.session_state.filtro_data_inicio = data_inicio
            st.session_state.filtro_data_fim = data_fim
            if carregar_dados_extrato():
                st.success("✅ Dados atualizados!")
                st.rerun()
        
        # Estatísticas
        st.markdown("---")
        st.header("📊 Estatísticas")
        
        stats_resultado = obter_estatisticas_extrato(
            data_inicio.strftime("%Y-%m-%d"),
            data_fim.strftime("%Y-%m-%d")
        )
        
        if stats_resultado.get("success"):
            stats = stats_resultado["estatisticas"]
            
            st.metric("Total de Registros", stats["total_registros"])
            st.metric("Novos (não processados)", stats["novos"], delta=f"R$ {stats['valor_novos']:,.2f}")
            st.metric("Registrados", stats["registrados"], delta=f"R$ {stats['valor_registrados']:,.2f}")
            st.metric("% Processado", f"{stats['percentual_processado']}%")
            
            # Gráfico de progresso
            fig = px.pie(
                values=[stats["novos"], stats["registrados"]],
                names=["Novos", "Registrados"],
                title="Status dos Registros",
                color_discrete_map={"Novos": "#ff7f0e", "Registrados": "#2ca02c"}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "✅ Pagamentos COM Responsável",
        "❓ Pagamentos SEM Responsável", 
        "👥 Gestão de Alunos/Responsáveis",
        "📋 Histórico"
    ])
    
    # ==========================================================
    # TAB 1: PAGAMENTOS COM RESPONSÁVEL
    # ==========================================================
    with tab1:
        st.header("✅ Pagamentos com Responsável Cadastrado")
        
        if st.session_state.dados_extrato is None:
            st.info("👆 Use os filtros na barra lateral para carregar os dados")
        else:
            dados_com = st.session_state.dados_extrato.get("com_responsavel", [])
            
            if not dados_com:
                st.success("🎉 Todos os pagamentos já foram processados!")
            else:
                st.info(f"📊 {len(dados_com)} registros encontrados com responsáveis cadastrados")
                
                # Converter para DataFrame
                df = pd.DataFrame(dados_com)
                
                # Botões de ação principal
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    modo_processamento = st.radio(
                        "🎯 Modo de Processamento:",
                        ["🚀 Processamento Rápido", "⚙️ Configuração Avançada"],
                        help="Rápido: 1 tipo por pagamento | Avançado: múltiplos tipos/alunos por pagamento"
                    )
                
                with col2:
                    if modo_processamento == "🚀 Processamento Rápido":
                        acao_massa = st.selectbox(
                            "Tipo Padrão",
                            ["matricula", "mensalidade", "material", "fardamento", "evento", "outro"],
                            key="acao_massa_com"
                        )
                    else:
                        st.write("⚙️ Configuração individual por registro")
                
                with col3:
                    if st.button("🚀 PROCESSAR SELECIONADOS", type="primary"):
                        processar_acoes_com_responsavel()
                
                # Mostrar registros
                st.subheader("📋 Registros Disponíveis")
                
                # Processar cada registro individualmente
                registros_configurados = []
                
                for idx, registro in enumerate(dados_com):
                    responsavel_info = registro.get('responsaveis', {})
                    nome_responsavel = responsavel_info.get('nome', 'N/A') if responsavel_info else 'N/A'
                    
                    with st.expander(
                        f"💰 R$ {registro['valor']:.2f} - {registro['nome_remetente']} ({nome_responsavel}) - {registro['data_pagamento']}",
                        expanded=False
                    ):
                        # Verificar se responsável tem múltiplos alunos
                        id_responsavel = registro.get('id_responsavel')
                        if id_responsavel:
                            alunos_vinculados = listar_alunos_vinculados_responsavel(id_responsavel)
                            tem_multiplos_alunos = alunos_vinculados.get("tem_multiplos_alunos", False)
                        else:
                            tem_multiplos_alunos = False
                        
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**👤 Responsável:** {nome_responsavel}")
                            st.write(f"**💰 Valor:** R$ {registro['valor']:.2f}")
                            st.write(f"**📅 Data:** {registro['data_pagamento']}")
                            if tem_multiplos_alunos:
                                st.info(f"ℹ️ Este responsável tem múltiplos alunos vinculados")
                        
                        with col2:
                            # Checkbox para selecionar
                            selecionado = st.checkbox(
                                "Processar este registro",
                                key=f"select_{registro['id']}"
                            )
                            
                            if selecionado:
                                if modo_processamento == "🚀 Processamento Rápido":
                                    # Modo rápido: apenas selecionar o tipo
                                    tipo_pagamento = st.selectbox(
                                        "Tipo de Pagamento:",
                                        ["matricula", "mensalidade", "material", "fardamento", "evento", "outro"],
                                        index=["matricula", "mensalidade", "material", "fardamento", "evento", "outro"].index(acao_massa),
                                        key=f"tipo_{registro['id']}"
                                    )
                                    
                                    # Se tem múltiplos alunos, permitir seleção
                                    if tem_multiplos_alunos and alunos_vinculados.get("success"):
                                        alunos = alunos_vinculados["alunos"]
                                        opcoes_alunos = {aluno["label"]: aluno for aluno in alunos}
                                        aluno_selecionado = st.selectbox(
                                            "Aluno:",
                                            list(opcoes_alunos.keys()),
                                            key=f"aluno_{registro['id']}"
                                        )
                                        aluno_data = opcoes_alunos[aluno_selecionado]
                                        id_aluno = aluno_data["id"]
                                    else:
                                        # Usar primeiro aluno vinculado
                                        if alunos_vinculados.get("success") and alunos_vinculados.get("alunos"):
                                            id_aluno = alunos_vinculados["alunos"][0]["id"]
                                        else:
                                            id_aluno = None
                                            st.error("❌ Nenhum aluno vinculado!")
                                    
                                    if id_aluno:
                                        registros_configurados.append({
                                            'id_extrato': registro['id'],
                                            'id_responsavel': id_responsavel,
                                            'configuracao_simples': True,
                                            'id_aluno': id_aluno,
                                            'tipo_pagamento': tipo_pagamento,
                                            'valor': registro['valor'],
                                            'registro': registro
                                        })
                        
                        with col3:
                            if selecionado and modo_processamento == "⚙️ Configuração Avançada":
                                if st.button("⚙️ Configurar", key=f"config_{registro['id']}"):
                                    st.session_state[f"show_config_{registro['id']}"] = True
                        
                # Modal de configuração avançada (fora dos expanders)
                registro_para_configurar = None
                for registro in dados_com:
                    if st.session_state.get(f"show_config_{registro['id']}", False):
                        registro_para_configurar = registro
                        break
                
                if registro_para_configurar:
                    st.markdown("---")
                    st.markdown("## ⚙️ Configuração Avançada de Pagamento")
                    
                    # Buscar responsável
                    id_responsavel_config = registro_para_configurar.get('id_responsavel')
                    
                    config_resultado = mostrar_modal_pagamento_avancado(registro_para_configurar, id_responsavel_config)
                    
                    if config_resultado:
                        # Adicionar configuração avançada
                        registros_configurados.append({
                            'id_extrato': registro_para_configurar['id'],
                            'id_responsavel': id_responsavel_config,
                            'configuracao_multipla': True,
                            'pagamentos_detalhados': config_resultado['pagamentos_detalhados'],
                            'valor_total': config_resultado['valor_total'],
                            'registro': registro_para_configurar
                        })
                        
                        st.session_state[f"show_config_{registro_para_configurar['id']}"] = False
                        st.success(f"✅ Configuração salva: {config_resultado['total_pagamentos']} pagamentos")
                        st.rerun()
                
                # Salvar configurações no estado da sessão
                st.session_state.registros_configurados = registros_configurados
                
                # Resumo dos registros configurados
                if registros_configurados:
                    st.markdown("---")
                    st.subheader("📊 Resumo dos Registros Configurados")
                    
                    total_simples = len([r for r in registros_configurados if r.get('configuracao_simples')])
                    total_multiplos = len([r for r in registros_configurados if r.get('configuracao_multipla')])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🚀 Processamento Rápido", total_simples)
                    with col2:
                        st.metric("⚙️ Configuração Avançada", total_multiplos)
                    with col3:
                        st.metric("📋 Total", len(registros_configurados))
                    
                    # Detalhes
                    for config in registros_configurados:
                        if config.get('configuracao_simples'):
                            st.write(f"• **Simples:** R$ {config['valor']:.2f} - {config['tipo_pagamento']}")
                        elif config.get('configuracao_multipla'):
                            detalhes = config['pagamentos_detalhados']
                            tipos = ", ".join([d['tipo_pagamento'] for d in detalhes])
                            st.write(f"• **Múltiplo:** R$ {config['valor_total']:.2f} - {tipos} ({len(detalhes)} pagamentos)")
    
    # ==========================================================
    # TAB 2: PAGAMENTOS SEM RESPONSÁVEL
    # ==========================================================
    with tab2:
        st.header("❓ Pagamentos sem Responsável Cadastrado")
        
        if st.session_state.dados_extrato is None:
            st.info("👆 Use os filtros na barra lateral para carregar os dados")
        else:
            dados_sem = st.session_state.dados_extrato.get("sem_responsavel", [])
            
            if not dados_sem:
                st.success("🎉 Todos os pagamentos têm responsáveis identificados!")
            else:
                st.info(f"📊 {len(dados_sem)} registros sem responsável cadastrado")
                
                # Filtro de busca
                busca_nome = st.text_input("🔍 Filtrar por nome do remetente", key="busca_sem_resp")
                
                # Filtrar dados
                if busca_nome:
                    dados_filtrados = [
                        r for r in dados_sem 
                        if busca_nome.lower() in r.get('nome_remetente', '').lower()
                    ]
                else:
                    dados_filtrados = dados_sem
                
                # Mostrar registros em expansores
                for idx, registro in enumerate(dados_filtrados[:20]):  # Limitar a 20 para performance
                    with st.expander(
                        f"💰 {registro['nome_remetente']} - R$ {registro['valor']:.2f} - {registro['data_pagamento']}"
                    ):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**ID:** {registro['id']}")
                            st.write(f"**Valor:** R$ {registro['valor']:.2f}")
                            st.write(f"**Data:** {registro['data_pagamento']}")
                            if registro.get('observacoes'):
                                st.write(f"**Observações:** {registro['observacoes']}")
                        
                        with col2:
                            if st.button(
                                "📝 Cadastrar Responsável", 
                                key=f"cad_resp_{registro['id']}"
                            ):
                                st.session_state[f"show_form_{registro['id']}"] = True
                        
                        # Mostrar formulário se solicitado
                        if st.session_state.get(f"show_form_{registro['id']}", False):
                            st.markdown("---")
                            resultado = mostrar_formulario_responsavel(registro['nome_remetente'])
                            
                            if resultado and resultado.get("success"):
                                # Atualizar o registro do extrato com o novo responsável
                                from funcoes_extrato_otimizadas import supabase
                                supabase.table("extrato_pix").update({
                                    "id_responsavel": resultado["id_responsavel"],
                                    "atualizado_em": datetime.now().isoformat()
                                }).eq("id", registro["id"]).execute()
                                
                                st.success("✅ Responsável cadastrado e extrato atualizado!")
                                st.session_state[f"show_form_{registro['id']}"] = False
                                
                                # Recarregar dados
                                carregar_dados_extrato()
                                st.rerun()
                
                if len(dados_sem) > 20:
                    st.info(f"Mostrando 20 de {len(dados_sem)} registros. Use o filtro para encontrar registros específicos.")
    
    # ==========================================================
    # TAB 3: GESTÃO DE ALUNOS/RESPONSÁVEIS
    # ==========================================================
    with tab3:
        st.header("👥 Gestão de Alunos e Responsáveis")
        
        # Busca de aluno melhorada
        busca_aluno = st.text_input("🔍 Buscar aluno por nome", key="busca_gestao_aluno", placeholder="Digite pelo menos 2 caracteres...")
        
        # Inicializar lista de alunos
        if 'lista_alunos_gestao' not in st.session_state:
            st.session_state.lista_alunos_gestao = []
        
        # Buscar alunos automaticamente conforme digita
        if len(busca_aluno) >= 2:
            resultado_busca = buscar_alunos_para_dropdown(busca_aluno)
            if resultado_busca.get("success"):
                st.session_state.lista_alunos_gestao = resultado_busca.get("opcoes", [])
        elif len(busca_aluno) == 0:
            # Se campo vazio, buscar todos os alunos (limitado)
            resultado_busca = buscar_alunos_para_dropdown("")
            if resultado_busca.get("success"):
                st.session_state.lista_alunos_gestao = resultado_busca.get("opcoes", [])
        
        # Exibir lista de alunos encontrados
        if st.session_state.lista_alunos_gestao:
            # Selectbox com os alunos encontrados
            opcoes_formatadas = ["Selecione um aluno..."] + [aluno["label"] for aluno in st.session_state.lista_alunos_gestao]
            
            aluno_escolhido = st.selectbox(
                f"🎓 Alunos encontrados ({len(st.session_state.lista_alunos_gestao)}):",
                options=opcoes_formatadas,
                key="select_gestao_aluno"
            )
            
            # Encontrar o aluno selecionado
            aluno_selecionado = None
            if aluno_escolhido != "Selecione um aluno...":
                for aluno in st.session_state.lista_alunos_gestao:
                    if aluno["label"] == aluno_escolhido:
                        aluno_selecionado = aluno
                        break
            
            if aluno_selecionado:
                st.markdown("---")
                
                # Usar a nova função para mostrar informações editáveis
                mostrar_informacoes_editaveis_aluno(aluno_selecionado)
                
                # Gestão de responsáveis
                st.markdown("---")
                mostrar_gestao_responsaveis_aluno(
                    aluno_selecionado["id"], 
                    aluno_selecionado["nome"]
                )
        elif len(busca_aluno) >= 2:
            st.info("Nenhum aluno encontrado com esse nome")
    
    # ==========================================================
    # TAB 4: HISTÓRICO
    # ==========================================================
    with tab4:
        st.header("📋 Histórico de Ações")
        
        if st.session_state.historico_acoes:
            df_historico = pd.DataFrame(st.session_state.historico_acoes)
            
            # Estatísticas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Ações", len(df_historico))
            with col2:
                sucessos = len(df_historico[df_historico['status'] == 'Sucesso'])
                st.metric("Sucessos", sucessos)
            with col3:
                erros = len(df_historico[df_historico['status'].isin(['Erro', 'Exceção'])])
                st.metric("Erros", erros)
            with col4:
                if len(df_historico) > 0:
                    taxa_sucesso = (sucessos / len(df_historico)) * 100
                    st.metric("Taxa de Sucesso", f"{taxa_sucesso:.1f}%")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_status = st.selectbox(
                    "Filtrar por Status:",
                    ["Todos", "Sucesso", "Erro", "Exceção"],
                    key="filtro_status_historico"
                )
            with col2:
                if st.button("🔄 Atualizar Visualização"):
                    st.rerun()
            
            # Aplicar filtro
            if filtro_status != "Todos":
                df_filtrado = df_historico[df_historico['status'] == filtro_status]
            else:
                df_filtrado = df_historico
            
            # Tabela principal com colunas essenciais
            colunas_mostrar = ['timestamp', 'status', 'acao', 'nome_remetente', 'valor', 'mensagem']
            if 'nome_aluno' in df_filtrado.columns:
                colunas_mostrar.insert(-2, 'nome_aluno')
                
            st.subheader("📊 Resumo das Ações")
            st.dataframe(
                df_filtrado[colunas_mostrar] if len(df_filtrado) > 0 else df_filtrado,
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Data/Hora", format="DD/MM/YYYY HH:mm:ss"),
                    "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                    "status": st.column_config.TextColumn("Status"),
                    "acao": st.column_config.TextColumn("Ação"),
                    "nome_remetente": st.column_config.TextColumn("Remetente"),
                    "nome_aluno": st.column_config.TextColumn("Aluno"),
                    "mensagem": st.column_config.TextColumn("Resultado")
                },
                use_container_width=True,
                height=300
            )
            
            # Detalhes expandidos para cada ação
            st.subheader("🔍 Detalhes das Ações")
            
            for idx, acao in df_filtrado.iterrows():
                status_icon = "✅" if acao['status'] == 'Sucesso' else "❌"
                
                with st.expander(
                    f"{status_icon} [{acao['timestamp'].strftime('%H:%M:%S')}] {acao['acao']} - {acao['nome_remetente']} - R$ {acao['valor']:.2f}",
                    expanded=False
                ):
                    # Informações básicas
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**📋 Informações Básicas:**")
                        st.write(f"• **Status:** {acao['status']}")
                        st.write(f"• **ID Extrato:** {acao.get('id_extrato', 'N/A')}")
                        st.write(f"• **Ação:** {acao['acao']}")
                        st.write(f"• **Resultado:** {acao['mensagem']}")
                    
                    with col2:
                        st.write("**💰 Dados do Pagamento:**")
                        st.write(f"• **Remetente:** {acao['nome_remetente']}")
                        if 'nome_aluno' in acao and pd.notna(acao['nome_aluno']):
                            st.write(f"• **Aluno:** {acao['nome_aluno']}")
                        st.write(f"• **Valor:** R$ {acao['valor']:.2f}")
                        st.write(f"• **Timestamp:** {acao['timestamp']}")
                    
                    # Detalhes técnicos se disponíveis
                    if 'detalhes' in acao and acao['detalhes']:
                        st.write("**🔧 Detalhes Técnicos:**")
                        
                        detalhes = acao['detalhes']
                        if isinstance(detalhes, dict):
                            for key, value in detalhes.items():
                                if key == 'erro_completo' and isinstance(value, dict):
                                    st.write(f"• **Erro Completo:**")
                                    st.json(value)
                                elif key == 'debug_info' and isinstance(value, list):
                                    st.write(f"• **Logs de Debug:**")
                                    st.code("\n".join(value), language="text")
                                else:
                                    st.write(f"• **{key}:** {value}")
                        else:
                            st.write(detalhes)
            
            # Botões de ação
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ Limpar Histórico"):
                    st.session_state.historico_acoes = []
                    st.success("Histórico limpo!")
                    st.rerun()
            
            with col2:
                if st.button("📊 Exportar Histórico"):
                    import json
                    historico_json = json.dumps(st.session_state.historico_acoes, default=str, indent=2)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    st.download_button(
                        label="💾 Download JSON",
                        data=historico_json,
                        file_name=f"historico_extrato_{timestamp}.json",
                        mime="application/json"
                    )
            
            with col3:
                if st.button("🔄 Recarregar Dados"):
                    carregar_dados_extrato()
                    st.rerun()
                    
        else:
            st.info("Nenhuma ação realizada ainda")
            st.markdown("""
            **ℹ️ Como usar o histórico:**
            
            1. Execute algumas ações nas abas anteriores
            2. O histórico registrará todos os detalhes
            3. Use os filtros para encontrar ações específicas
            4. Expanda os detalhes para ver logs completos
            5. Exporte o histórico para análise posterior
            """)

def processar_acoes_com_responsavel():
    """Processa ações selecionadas para registros com responsável com debugging completo"""
    registros = st.session_state.get('registros_configurados', [])
    
    if not registros:
        st.warning("Nenhum registro selecionado!")
        return
    
    # Container para logs em tempo real
    log_container = st.container()
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Inicializar logs
    logs = []
    sucessos = 0
    erros = 0
    
    def log_debug(mensagem: str, tipo: str = "INFO"):
        """Adiciona log e exibe em tempo real"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{tipo}] {mensagem}"
        logs.append(log_entry)
        print(log_entry)  # Também exibe no terminal
        
        # Atualizar interface
        with log_container:
            st.text_area("📋 Logs de Processamento:", 
                        value="\n".join(logs[-10:]),  # Últimas 10 linhas
                        height=200, 
                        key=f"logs_{len(logs)}")
    
    log_debug(f"🚀 INICIANDO PROCESSAMENTO DE {len(registros)} REGISTROS")
    
    for i, item in enumerate(registros):
        progress = (i + 1) / len(registros)
        progress_bar.progress(progress)
        
        # Log detalhado de cada item
        registro = item.get('registro', {})
        log_debug(f"📄 PROCESSANDO ITEM {i+1}/{len(registros)}")
        log_debug(f"   - ID Extrato: {item.get('id_extrato')}")
        log_debug(f"   - ID Responsável: {item.get('id_responsavel')}")
        
        # Verificar tipo de configuração
        if item.get('configuracao_simples'):
            log_debug(f"   - Modo: Configuração Simples")
            log_debug(f"   - ID Aluno: {item.get('id_aluno')}")
            log_debug(f"   - Tipo Pagamento: {item.get('tipo_pagamento')}")
            log_debug(f"   - Valor: R$ {item.get('valor', 0):.2f}")
        elif item.get('configuracao_multipla'):
            log_debug(f"   - Modo: Configuração Múltipla")
            log_debug(f"   - Total Pagamentos: {len(item.get('pagamentos_detalhados', []))}")
            log_debug(f"   - Valor Total: R$ {item.get('valor_total', 0):.2f}")
        
        log_debug(f"   - Nome Remetente: {registro.get('nome_remetente')}")
        
        status_container.write(f"🔄 Processando {i+1}/{len(registros)}: {registro.get('nome_remetente', 'N/A')}")
        
        try:
            if item.get('configuracao_simples'):
                # PROCESSAMENTO SIMPLES (1 pagamento)
                log_debug(f"🔍 ETAPA 1: Processamento simples")
                
                resultado = registrar_pagamento_do_extrato(
                    id_extrato=item['id_extrato'],
                    id_responsavel=item['id_responsavel'],
                    id_aluno=item['id_aluno'],
                    tipo_pagamento=item['tipo_pagamento']
                )
                
                log_debug(f"   - Resultado da função: {resultado}")
                
                if resultado.get('success'):
                    log_debug(f"✅ SUCESSO: {resultado.get('message', 'Pagamento registrado')}", "SUCCESS")
                    sucessos += 1
                    
                    # Registrar no histórico
                    historico_entry = {
                        'timestamp': datetime.now(),
                        'id_extrato': item['id_extrato'],
                        'acao': f"Registrar como {item['tipo_pagamento']} (Simples)",
                        'nome_remetente': registro.get('nome_remetente'),
                        'valor': item.get('valor'),
                        'status': 'Sucesso',
                        'mensagem': resultado.get('message', 'Registrado com sucesso'),
                        'detalhes': {
                            'id_pagamento': resultado.get('id_pagamento'),
                            'id_aluno': item['id_aluno'],
                            'tipo_pagamento': item['tipo_pagamento'],
                            'debug_info': resultado.get('debug_info', [])
                        }
                    }
                else:
                    erro_msg = resultado.get('error', 'Erro desconhecido')
                    log_debug(f"❌ ERRO: {erro_msg}", "ERROR")
                    erros += 1
                    
                    historico_entry = {
                        'timestamp': datetime.now(),
                        'id_extrato': item['id_extrato'],
                        'acao': f"Registrar como {item['tipo_pagamento']} (Simples)",
                        'nome_remetente': registro.get('nome_remetente'),
                        'valor': item.get('valor'),
                        'status': 'Erro',
                        'mensagem': erro_msg,
                        'detalhes': {
                            'erro_completo': resultado,
                            'debug_info': resultado.get('debug_info', [])
                        }
                    }
            
            elif item.get('configuracao_multipla'):
                # PROCESSAMENTO MÚLTIPLO (vários pagamentos)
                log_debug(f"🔍 ETAPA 1: Processamento múltiplo")
                
                resultado = registrar_pagamentos_multiplos_do_extrato(
                    id_extrato=item['id_extrato'],
                    id_responsavel=item['id_responsavel'],
                    pagamentos_detalhados=item['pagamentos_detalhados']
                )
                
                log_debug(f"   - Resultado da função: {resultado}")
                
                if resultado.get('success'):
                    total_criados = resultado.get('total_pagamentos_criados', 0)
                    tipos = ', '.join(resultado.get('tipos_pagamento', []))
                    log_debug(f"✅ SUCESSO: {total_criados} pagamentos criados ({tipos})", "SUCCESS")
                    sucessos += 1
                    
                    # Registrar no histórico
                    historico_entry = {
                        'timestamp': datetime.now(),
                        'id_extrato': item['id_extrato'],
                        'acao': f"Registrar múltiplos pagamentos ({total_criados})",
                        'nome_remetente': registro.get('nome_remetente'),
                        'valor': item.get('valor_total'),
                        'status': 'Sucesso',
                        'mensagem': resultado.get('message', f'{total_criados} pagamentos registrados'),
                        'detalhes': {
                            'pagamentos_criados': resultado.get('pagamentos_criados', []),
                            'tipos_pagamento': resultado.get('tipos_pagamento', []),
                            'alunos_beneficiarios': resultado.get('alunos_beneficiarios', []),
                            'total_pagamentos': total_criados,
                            'valor_total': resultado.get('valor_total_processado'),
                            'debug_info': resultado.get('debug_info', [])
                        }
                    }
                else:
                    erro_msg = resultado.get('error', 'Erro desconhecido')
                    log_debug(f"❌ ERRO: {erro_msg}", "ERROR")
                    erros += 1
                    
                    historico_entry = {
                        'timestamp': datetime.now(),
                        'id_extrato': item['id_extrato'],
                        'acao': f"Registrar múltiplos pagamentos",
                        'nome_remetente': registro.get('nome_remetente'),
                        'valor': item.get('valor_total'),
                        'status': 'Erro',
                        'mensagem': erro_msg,
                        'detalhes': {
                            'erro_completo': resultado,
                            'pagamentos_tentados': item.get('pagamentos_detalhados', []),
                            'debug_info': resultado.get('debug_info', [])
                        }
                    }
            else:
                log_debug(f"❌ ERRO: Configuração inválida - nem simples nem múltipla", "ERROR")
                erros += 1
                continue
            
            st.session_state.historico_acoes.append(historico_entry)
            log_debug(f"📝 Entrada adicionada ao histórico")
            
        except Exception as e:
            erro_msg = f"Exceção durante processamento: {str(e)}"
            log_debug(f"❌ EXCEÇÃO: {erro_msg}", "EXCEPTION")
            erros += 1
            
            # Registrar exceção no histórico
            historico_entry = {
                'timestamp': datetime.now(),
                'id_extrato': item.get('id_extrato', 'N/A'),
                'acao': f"Processamento (exceção)",
                'nome_remetente': registro.get('nome_remetente', 'N/A'),
                'valor': item.get('valor', item.get('valor_total', 0)),
                'status': 'Exceção',
                'mensagem': erro_msg,
                'detalhes': {
                    'item_completo': item,
                    'exception': str(e)
                }
            }
            st.session_state.historico_acoes.append(historico_entry)
        
        log_debug(f"🔄 Item {i+1} processado. Status atual: {sucessos} sucessos, {erros} erros")
        log_debug("─" * 80)
    
    # FINALIZAÇÃO
    log_debug(f"🏁 PROCESSAMENTO FINALIZADO")
    log_debug(f"📊 ESTATÍSTICAS FINAIS:")
    log_debug(f"   - Total processados: {len(registros)}")
    log_debug(f"   - Sucessos: {sucessos}")
    log_debug(f"   - Erros: {erros}")
    log_debug(f"   - Taxa de sucesso: {(sucessos/len(registros)*100):.1f}%")
    
    # Limpar configurações
    st.session_state.registros_configurados = []
    log_debug(f"🧹 Configurações limpas")
    
    # Mostrar resultado final
    progress_bar.empty()
    status_container.empty()
    
    if sucessos > 0:
        st.success(f"✅ {sucessos} pagamentos registrados com sucesso!")
        print(f"✅ SUCESSO: {sucessos} pagamentos processados")
    if erros > 0:
        st.error(f"❌ {erros} erros durante o processamento. Verifique os logs acima para detalhes.")
        print(f"❌ ERRO: {erros} falhas no processamento")
    
    # Mostrar logs finais expandidos
    with st.expander("📋 Ver Logs Completos do Processamento", expanded=False):
        st.code("\n".join(logs), language="text")
    
    # Recarregar dados
    log_debug(f"🔄 Recarregando dados do extrato...")
    carregar_dados_extrato()
    st.rerun()

# ==========================================================
# 🚀 EXECUTAR APLICAÇÃO
# ==========================================================

if __name__ == "__main__":
    main() 