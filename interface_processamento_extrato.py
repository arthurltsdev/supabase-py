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
    buscar_dados_completos_alunos_responsavel,
    listar_turmas_disponiveis,
    cadastrar_responsavel_e_vincular,
    cadastrar_aluno_e_vincular,
    buscar_responsaveis_para_dropdown,
    registrar_pagamento_do_extrato,
    registrar_pagamentos_multiplos_do_extrato,
    atualizar_aluno_campos,
    atualizar_vinculo_responsavel,
    obter_estatisticas_extrato,
    verificar_responsavel_existe,
    ignorar_registro_extrato,
    verificar_e_corrigir_extrato_duplicado,
    verificar_consistencia_extrato_pagamentos,
    atualizar_responsaveis_extrato_pix,
    corrigir_status_extrato_com_pagamentos,
    supabase
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
        'last_update': None,
        'registros_configurados': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def carregar_dados_extrato():
    """Carrega dados do extrato com filtros aplicados"""
    with st.spinner("Carregando dados do extrato..."):
        filtro_turma = st.session_state.get('filtro_turma_com_resp', None)
        if filtro_turma == "Todas as turmas":
            filtro_turma = None
            
        resultado = listar_extrato_com_sem_responsavel(
            data_inicio=st.session_state.filtro_data_inicio.strftime("%Y-%m-%d"),
            data_fim=st.session_state.filtro_data_fim.strftime("%Y-%m-%d"),
            filtro_turma=filtro_turma
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
    
    # Primeiro, calcular o valor já configurado nos pagamentos anteriores
    valor_ja_configurado = 0.0
    for i in range(len(st.session_state.pagamentos_config)):
        config = st.session_state.pagamentos_config[i]
        valor_ja_configurado += config.get("valor", 0.0)
    
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
            
            # NOVA SEÇÃO: Seleção de mensalidade se o tipo for "mensalidade"
            mensalidade_selecionada = None
            if tipo_pagamento == "mensalidade":
                st.markdown("**📅 Selecionar Mensalidade:**")
                
                # Buscar mensalidades disponíveis para o aluno
                from funcoes_extrato_otimizadas import listar_mensalidades_disponiveis_aluno
                mensalidades_resultado = listar_mensalidades_disponiveis_aluno(aluno_data["id"])
                
                if mensalidades_resultado.get("success") and mensalidades_resultado.get("mensalidades"):
                    mensalidades_disponiveis = mensalidades_resultado["mensalidades"]
                    
                    # Criar opções para o selectbox
                    opcoes_mensalidades = ["Selecione uma mensalidade..."] + [m["label"] for m in mensalidades_disponiveis]
                    
                    mensalidade_escolhida = st.selectbox(
                        f"Mensalidades disponíveis para {aluno_data['nome']}:",
                        options=opcoes_mensalidades,
                        key=f"mens_pag_{i}",
                        index=opcoes_mensalidades.index(config.get("mensalidade_label")) if config.get("mensalidade_label") in opcoes_mensalidades else 0
                    )
                    
                    if mensalidade_escolhida != "Selecione uma mensalidade...":
                        # Encontrar mensalidade selecionada
                        mensalidade_selecionada = next(
                            (m for m in mensalidades_disponiveis if m["label"] == mensalidade_escolhida), 
                            None
                        )
                        
                        if mensalidade_selecionada:
                            # Mostrar detalhes da mensalidade
                            col_det1, col_det2 = st.columns(2)
                            with col_det1:
                                st.info(f"📅 **Vencimento:** {mensalidade_selecionada['data_vencimento_fmt']}")
                            with col_det2:
                                st.info(f"⚠️ **Status:** {mensalidade_selecionada['status_texto']}")
                            
                            # Sugerir valor da mensalidade
                            valor_sugerido_mensalidade = mensalidade_selecionada["valor"]
                    else:
                        st.warning("⚠️ Selecione uma mensalidade para continuar")
                else:
                    st.warning(f"⚠️ Nenhuma mensalidade pendente encontrada para {aluno_data['nome']}")
                    st.info("💡 **Dica:** Verifique se as mensalidades foram geradas para este aluno ou se todas já foram pagas.")
            
            with col3:
                # Botão para remover (só se houver mais de 1)
                if len(st.session_state.pagamentos_config) > 1:
                    if st.button("🗑️ Remover", key=f"remove_pag_{i}"):
                        st.session_state.pagamentos_config.pop(i)
                        st.rerun()
            
            # Valor do pagamento
            col1, col2 = st.columns(2)
            
            with col1:
                # Calcular valor configurado até agora (excluindo este item)
                valor_outros_pagamentos = 0.0
                for j, other_config in enumerate(st.session_state.pagamentos_config):
                    if j != i:
                        valor_outros_pagamentos += other_config.get("valor", 0.0)
                
                # Determinar valor sugerido baseado no contexto
                valor_sugerido = 0.01
                help_text = None
                
                # Se é mensalidade e tem uma selecionada, usar valor da mensalidade
                if tipo_pagamento == "mensalidade" and mensalidade_selecionada:
                    valor_sugerido = mensalidade_selecionada["valor"]
                    help_text = f"Valor da mensalidade {mensalidade_selecionada['mes_referencia']}"
                # Se é o último pagamento e há múltiplos, sugerir valor restante
                elif i == len(st.session_state.pagamentos_config) - 1 and len(st.session_state.pagamentos_config) > 1:
                    valor_restante = max(0.01, valor_total - valor_outros_pagamentos)
                    valor_sugerido = valor_restante
                    help_text = f"Valor restante: R$ {valor_restante:.2f}"
                # Para o primeiro pagamento ou único
                elif len(st.session_state.pagamentos_config) == 1:
                    valor_sugerido = config.get("valor", valor_total)
                else:
                    valor_sugerido = config.get("valor", 0.01)
                
                # Calcular max_valor
                max_valor = valor_total - valor_outros_pagamentos + 0.01
                max_valor = max(max_valor, valor_sugerido + 0.01)
                
                valor_pagamento = st.number_input(
                    "💰 Valor:",
                    min_value=0.01,
                    max_value=max_valor,
                    value=valor_sugerido,
                    step=0.01,
                    key=f"valor_pag_{i}",
                    help=help_text
                )
            
            with col2:
                observacoes = st.text_input(
                    "📝 Observações:",
                    value=config.get("observacoes", ""),
                    key=f"obs_pag_{i}"
                )
            
            # Atualizar configuração
            config_atualizada = {
                "aluno_label": aluno_selecionado,
                "aluno_data": aluno_data,
                "tipo_pagamento": tipo_pagamento,
                "valor": valor_pagamento,
                "observacoes": observacoes
            }
            
            # Se é mensalidade, salvar dados da mensalidade selecionada
            if tipo_pagamento == "mensalidade" and mensalidade_selecionada:
                config_atualizada["mensalidade_selecionada"] = mensalidade_selecionada
                config_atualizada["mensalidade_label"] = mensalidade_selecionada["label"]
            
            st.session_state.pagamentos_config[i] = config_atualizada
            
            # Adicionar aos pagamentos detalhados
            pagamento_detalhado = {
                "id_aluno": aluno_data["id"],
                "nome_aluno": aluno_data["nome"],
                "tipo_pagamento": tipo_pagamento,
                "valor": valor_pagamento,
                "observacoes": observacoes
            }
            
            # Se é mensalidade, incluir dados da mensalidade
            if tipo_pagamento == "mensalidade" and mensalidade_selecionada:
                pagamento_detalhado["id_mensalidade"] = mensalidade_selecionada["id_mensalidade"]
                pagamento_detalhado["mes_referencia"] = mensalidade_selecionada["mes_referencia"]
                pagamento_detalhado["data_vencimento"] = mensalidade_selecionada["data_vencimento"]
            
            pagamentos_detalhados.append(pagamento_detalhado)
        
        # Separador visual entre pagamentos
        if i < len(st.session_state.pagamentos_config) - 1:
            st.markdown("---")
    
    # Calcular valor total configurado
    valor_total_configurado = sum(pag["valor"] for pag in pagamentos_detalhados)
    
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
    
    # Verificar duplicatas de aluno+tipo e mensalidades duplicadas
    combinacoes = set()
    mensalidades_usadas = set()
    
    for pag in pagamentos_detalhados:
        # Verificar duplicata de aluno+tipo (exceto mensalidades que podem ter múltiplas)
        if pag["tipo_pagamento"] != "mensalidade":
            combinacao = (pag["id_aluno"], pag["tipo_pagamento"])
            if combinacao in combinacoes:
                st.error(f"❌ Combinação duplicada: {pag['nome_aluno']} + {pag['tipo_pagamento']}")
                return None
            combinacoes.add(combinacao)
        
        # Verificar mensalidades duplicadas
        if pag["tipo_pagamento"] == "mensalidade" and pag.get("id_mensalidade"):
            id_mensalidade = pag["id_mensalidade"]
            if id_mensalidade in mensalidades_usadas:
                st.error(f"❌ Mensalidade duplicada: {pag['mes_referencia']} para {pag['nome_aluno']}")
                return None
            mensalidades_usadas.add(id_mensalidade)
    
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

def mostrar_formulario_cadastro_aluno():
    """Formulário para cadastrar novo aluno com possibilidade de vincular responsável"""
    with st.form("form_novo_aluno", clear_on_submit=True):
        st.subheader("🎓 Cadastrar Novo Aluno")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo*", key="aluno_nome")
            
            # Buscar turmas disponíveis
            turmas_result = listar_turmas_disponiveis()
            if turmas_result.get("success") and turmas_result.get("turmas"):
                opcoes_turmas = ["Selecionar turma..."] + turmas_result["turmas"]
                turma_selecionada = st.selectbox("Turma*", opcoes_turmas, key="aluno_turma")
                
                # Buscar ID da turma selecionada
                id_turma_selecionada = None
                if turma_selecionada != "Selecionar turma...":
                    # Buscar ID da turma pelo nome
                    turma_response = supabase.table("turmas").select("id").eq("nome_turma", turma_selecionada).execute()
                    if turma_response.data:
                        id_turma_selecionada = turma_response.data[0]["id"]
            else:
                st.error("❌ Erro ao carregar turmas")
                return None
            
            turno = st.selectbox("Turno*", ["Matutino", "Vespertino", "Integral"], key="aluno_turno")
            data_nascimento = st.date_input("Data de Nascimento", key="aluno_data_nasc")
        
        with col2:
            dia_vencimento = st.selectbox("Dia de Vencimento", list(range(1, 32)), index=4, key="aluno_dia_venc")
            valor_mensalidade = st.number_input("Valor da Mensalidade (R$)", min_value=0.0, step=10.0, key="aluno_valor_mens")
            
            st.markdown("**👤 Vincular a Responsável (Opcional)**")
            
            # Campo de busca de responsável
            busca_responsavel = st.text_input("🔍 Digite o nome do responsável", key="busca_resp_aluno", placeholder="Digite para buscar...")
            
            responsavel_selecionado = None
            if busca_responsavel and len(busca_responsavel.strip()) >= 2:
                resultado_busca = buscar_responsaveis_para_dropdown(busca_responsavel.strip())
                if resultado_busca.get("success") and resultado_busca.get("opcoes"):
                    opcoes_resp = {op["label"]: op for op in resultado_busca["opcoes"]}
                    
                    if opcoes_resp:
                        responsavel_escolhido = st.selectbox(
                            f"Responsáveis encontrados ({len(opcoes_resp)}):",
                            ["Não vincular"] + list(opcoes_resp.keys()),
                            key="select_resp_aluno"
                        )
                        
                        if responsavel_escolhido != "Não vincular":
                            responsavel_selecionado = opcoes_resp[responsavel_escolhido]
                    else:
                        st.info("Nenhum responsável encontrado")
                elif len(busca_responsavel.strip()) >= 2:
                    st.info("Nenhum responsável encontrado com esse nome")
            
            # Tipo de relação se responsável selecionado
            tipo_relacao = "pai"
            responsavel_financeiro = True
            if responsavel_selecionado:
                tipo_relacao = st.selectbox(
                    "Tipo de Relação*",
                    ["pai", "mãe", "avô", "avó", "tio", "tia", "responsável legal", "outro"],
                    key="tipo_relacao_aluno"
                )
                responsavel_financeiro = st.checkbox("É responsável financeiro", value=True, key="resp_financeiro_aluno")
        
        submitted = st.form_submit_button("🎓 Cadastrar Aluno", type="primary")
        
        if submitted:
            # Validações
            if not nome:
                st.error("Nome é obrigatório!")
                return None
            
            if turma_selecionada == "Selecionar turma..." or not id_turma_selecionada:
                st.error("Selecione uma turma!")
                return None
            
            # Preparar dados do aluno
            dados_aluno = {
                "nome": nome,
                "id_turma": id_turma_selecionada,
                "turno": turno,
                "data_nascimento": data_nascimento.isoformat() if data_nascimento else None,
                "dia_vencimento": str(dia_vencimento),
                "valor_mensalidade": valor_mensalidade if valor_mensalidade > 0 else None
            }
            
            # Cadastrar aluno
            resultado = cadastrar_aluno_e_vincular(
                dados_aluno=dados_aluno,
                id_responsavel=responsavel_selecionado["id"] if responsavel_selecionado else None,
                tipo_relacao=tipo_relacao,
                responsavel_financeiro=responsavel_financeiro
            )
            
            if resultado.get("success"):
                # Mensagem de sucesso
                st.success(f"✅ Aluno {nome} cadastrado com sucesso!")
                
                if resultado.get("vinculo_criado"):
                    st.success(f"✅ Vinculado ao responsável: {resultado.get('nome_responsavel')}")
                elif responsavel_selecionado and not resultado.get("vinculo_criado"):
                    st.warning(f"⚠️ Aluno cadastrado, mas houve erro no vínculo: {resultado.get('vinculo_erro')}")
                
                # Mostrar informações do aluno criado
                st.info(f"🆔 **ID do Aluno:** {resultado.get('id_aluno')}")
                st.info(f"🎓 **Turma:** {turma_selecionada}")
                st.info(f"🕐 **Turno:** {turno}")
                
                return resultado
            else:
                st.error(f"❌ Erro ao cadastrar aluno: {resultado.get('error')}")
                return None

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
        
        # Botão para verificação manual de consistência
        if st.button("🔍 Verificar Consistência", help="Verifica e corrige registros duplicados manualmente"):
            with st.spinner("Verificando consistência..."):
                resultado_verificacao = verificar_consistencia_extrato_pagamentos(
                    data_inicio.strftime("%Y-%m-%d"),
                    data_fim.strftime("%Y-%m-%d")
                )
                
                if resultado_verificacao.get("success"):
                    relatorio = resultado_verificacao["relatorio"]
                    
                    if relatorio["inconsistencias"]:
                        st.warning(f"⚠️ {len(relatorio['inconsistencias'])} inconsistências encontradas!")
                        
                        # Executar correção automática
                        correcao = verificar_e_corrigir_extrato_duplicado()
                        if correcao.get("success") and correcao.get("corrigidos", 0) > 0:
                            st.success(f"✅ {correcao['corrigidos']} registros corrigidos automaticamente!")
                            # Recarregar dados após correção
                            carregar_dados_extrato()
                            st.rerun()
                        else:
                            st.info("ℹ️ Nenhuma correção aplicada")
                    else:
                        st.success("✅ Nenhuma inconsistência encontrada!")
                else:
                    st.error(f"❌ Erro na verificação: {resultado_verificacao.get('error')}")
        
        # Botão para atualizar responsáveis
        if st.button("👥 Atualizar Responsáveis", help="Identifica registros sem responsável e tenta associá-los automaticamente"):
            with st.spinner("Analisando registros sem responsável..."):
                resultado_responsaveis = atualizar_responsaveis_extrato_pix()
                
                if resultado_responsaveis.get("success"):
                    atualizados = resultado_responsaveis.get("atualizados", 0)
                    usou_nome_norm = resultado_responsaveis.get("usou_nome_norm", False)
                    
                    # Mostrar informação sobre normalização
                    if usou_nome_norm:
                        st.info("🔍 Usando campo 'nome_norm' para melhor correspondência!")
                    else:
                        st.warning("⚠️ Campo 'nome_norm' não encontrado - usando campo 'nome' padrão")
                    
                    if atualizados > 0:
                        st.success(f"✅ {atualizados} registros atualizados com responsáveis!")
                        
                        # Mostrar correspondências encontradas
                        correspondencias = resultado_responsaveis.get("correspondencias", [])
                        if correspondencias:
                            with st.expander(f"📋 Ver {len(correspondencias)} correspondências encontradas"):
                                for correspondencia in correspondencias:
                                    col1, col2, col3 = st.columns([3, 3, 2])
                                    
                                    with col1:
                                        st.write(f"**Remetente:** {correspondencia['nome_remetente']}")
                                    
                                    with col2:
                                        st.write(f"**Responsável:** {correspondencia['nome_responsavel']}")
                                        if correspondencia.get('usado_nome_norm'):
                                            st.write(f"*(comparado com: {correspondencia['nome_usado_comparacao']})*")
                                    
                                    with col3:
                                        similaridade = correspondencia['similaridade']
                                        cor = "🟢" if similaridade >= 95 else "🟡"
                                        st.write(f"{cor} {similaridade:.1f}%")
                                    
                                    alunos_vinculados = correspondencia['alunos_vinculados']
                                    id_aluno_preenchido = correspondencia['id_aluno_preenchido']
                                    
                                    if alunos_vinculados == 1:
                                        st.info(f"   ✅ ID do aluno preenchido automaticamente ({alunos_vinculados} aluno vinculado)")
                                    else:
                                        st.info(f"   ⚠️ {alunos_vinculados} alunos vinculados - ID será preenchido no registro do pagamento")
                                    
                                    st.markdown("---")
                        
                        # Recarregar dados após atualização
                        carregar_dados_extrato()
                        st.rerun()
                    else:
                        st.info("ℹ️ Nenhum registro sem responsável encontrado ou sem correspondências válidas (>90%)")
                        
                        # Mostrar debug info se disponível
                        debug_info = resultado_responsaveis.get("debug_info", [])
                        if debug_info:
                            with st.expander("📋 Ver detalhes da análise"):
                                for debug_line in debug_info:
                                    st.text(debug_line)
                else:
                    st.error(f"❌ Erro ao atualizar responsáveis: {resultado_responsaveis.get('error')}")
        
        # Botão para corrigir status dos registros
        if st.button("🔧 Corrigir Status Extrato", help="Atualiza registros com pagamentos vinculados para status 'registrado'"):
            with st.spinner("Corrigindo status dos registros..."):
                resultado_correcao = corrigir_status_extrato_com_pagamentos()
                
                if resultado_correcao.get("success"):
                    corrigidos = resultado_correcao.get("corrigidos", 0)
                    total_analisados = resultado_correcao.get("total_analisados", 0)
                    
                    if corrigidos > 0:
                        st.success(f"✅ {corrigidos} registros corrigidos de 'novo' para 'registrado'!")
                        
                        # Mostrar detalhes das correções
                        detalhes = resultado_correcao.get("detalhes_correcoes", [])
                        if detalhes:
                            with st.expander(f"📋 Ver {len(detalhes)} correções aplicadas"):
                                for detalhe in detalhes:
                                    col1, col2, col3 = st.columns([3, 2, 2])
                                    
                                    with col1:
                                        st.write(f"**{detalhe['nome_remetente']}**")
                                        st.write(f"Data: {detalhe['data_pagamento']}")
                                    
                                    with col2:
                                        st.write(f"Valor: R$ {detalhe['valor']:.2f}")
                                        st.write(f"Extrato: {detalhe['id_extrato'][:8]}...")
                                    
                                    with col3:
                                        st.write(f"Pagamentos: {detalhe['pagamentos_vinculados']}")
                                        if detalhe.get('id_aluno'):
                                            st.write("✅ ID aluno preenchido")
                                        else:
                                            st.write("⚠️ Múltiplos alunos")
                                    
                                    st.markdown("---")
                        
                        # Recarregar dados após correção
                        carregar_dados_extrato()
                        st.rerun()
                    else:
                        if total_analisados == 0:
                            st.success("✅ Nenhum registro com status 'novo' encontrado!")
                        else:
                            st.info("ℹ️ Nenhum registro com pagamentos vinculados precisava de correção")
                else:
                    st.error(f"❌ Erro ao corrigir status: {resultado_correcao.get('error')}")
                    
                    # Mostrar logs de debug
                    debug_info = resultado_correcao.get("debug_info", [])
                    if debug_info:
                        with st.expander("🔍 Ver detalhes do erro"):
                            for debug_line in debug_info:
                                st.text(debug_line)
        
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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "✅ Pagamentos COM Responsável",
        "❓ Pagamentos SEM Responsável", 
        "👥 Gestão de Alunos/Responsáveis",
        "📋 Histórico",
        "🔍 Consistência",
        "🔗 Vincular Responsáveis"
    ])
    
    # ==========================================================
    # TAB 1: PAGAMENTOS COM RESPONSÁVEL
    # ==========================================================
    with tab1:
        st.header("✅ Pagamentos com Responsável Cadastrado")
        
        # Filtros adicionais para a aba
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Filtro por turma
            turmas_resultado = listar_turmas_disponiveis()
            if turmas_resultado.get("success"):
                opcoes_turmas = ["Todas as turmas"] + turmas_resultado["turmas"]
                filtro_turma = st.selectbox(
                    "🎓 Filtrar por Turma:",
                    options=opcoes_turmas,
                    key="filtro_turma_com_resp"
                )
        
        with col2:
            if st.button("🔄 Aplicar Filtros", type="secondary"):
                carregar_dados_extrato()
                st.rerun()
        
        if st.session_state.dados_extrato is None:
            st.info("👆 Use os filtros na barra lateral para carregar os dados")
        else:
            dados_com = st.session_state.dados_extrato.get("com_responsavel", [])
            
            # Mostrar feedback sobre correções automáticas
            correcoes_aplicadas = st.session_state.dados_extrato.get("correcoes_aplicadas", 0)
            if correcoes_aplicadas > 0:
                st.success(f"✅ {correcoes_aplicadas} registros duplicados foram automaticamente corrigidos!")
                
                # Mostrar detalhes das correções se houver
                detalhes_correcoes = st.session_state.dados_extrato.get("detalhes_correcoes", [])
                if detalhes_correcoes:
                    with st.expander(f"📋 Ver detalhes das {correcoes_aplicadas} correções aplicadas"):
                        for i, correcao in enumerate(detalhes_correcoes):
                            st.write(f"**{i+1}.** {correcao['nome_remetente']} - R$ {correcao['valor']:.2f}")
                            st.write(f"   📅 Data: {correcao['data_pagamento']}")
                            st.write(f"   🆔 Extrato: {correcao['id_extrato']}")
                            st.write(f"   💳 Pagamento: {correcao['id_pagamento_encontrado']}")
                            st.write(f"   📝 Motivo: {correcao['motivo']}")
                            if i < len(detalhes_correcoes) - 1:
                                st.write("---")
            
            if not dados_com:
                if st.session_state.get('filtro_turma_com_resp') and st.session_state.get('filtro_turma_com_resp') != "Todas as turmas":
                    st.info(f"🎓 Nenhum pagamento encontrado para a turma '{st.session_state.get('filtro_turma_com_resp')}'")
                else:
                    st.success("🎉 Todos os pagamentos já foram processados!")
            else:
                turma_info = f" (Turma: {st.session_state.get('filtro_turma_com_resp', 'Todas')})" if st.session_state.get('filtro_turma_com_resp') != "Todas as turmas" else ""
                st.info(f"📊 {len(dados_com)} registros encontrados com responsáveis cadastrados{turma_info}")
                
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
                
                # Botão para limpar configurações com contador visual
                configuracoes_salvas = st.session_state.get('registros_configurados', [])
                if configuracoes_salvas:
                    col_botao1, col_botao2 = st.columns(2)
                    
                    with col_botao1:
                        st.info(f"📋 {len(configuracoes_salvas)} configurações salvas")
                    
                    with col_botao2:
                        if st.button("🗑️ Limpar Configurações", type="secondary", help="Remove todas as configurações salvas"):
                            st.session_state.registros_configurados = []
                            # Limpar também qualquer configuração de pagamento ativa
                            if 'pagamentos_config' in st.session_state:
                                del st.session_state.pagamentos_config
                            st.success("✅ Todas as configurações foram limpas!")
                            st.rerun()
                
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
                        # Buscar dados completos dos alunos vinculados
                        id_responsavel = registro.get('id_responsavel')
                        alunos_completos = None
                        tem_multiplos_alunos = False
                        
                        if id_responsavel:
                            resultado_alunos = buscar_dados_completos_alunos_responsavel(id_responsavel)
                            if resultado_alunos.get("success"):
                                alunos_completos = resultado_alunos["alunos"]
                                tem_multiplos_alunos = resultado_alunos.get("tem_multiplos_alunos", False)
                        
                        col1, col2, col3 = st.columns([3, 3, 2])
                        
                        with col1:
                            st.markdown("**💰 Dados do Pagamento:**")
                            st.write(f"• **Responsável:** {nome_responsavel}")
                            st.write(f"• **Valor:** R$ {registro['valor']:.2f}")
                            st.write(f"• **Data:** {registro['data_pagamento']}")
                            if registro.get('observacoes'):
                                st.write(f"• **Observações:** {registro['observacoes']}")
                        
                        with col2:
                            st.markdown("**👨‍🎓 Alunos Vinculados:**")
                            if alunos_completos:
                                for i, aluno in enumerate(alunos_completos):
                                    st.write(f"**{i+1}. {aluno['nome']}**")
                                    st.write(f"   📚 Turma: {aluno['turma_nome']}")
                                    st.write(f"   💰 Mensalidade: {aluno['valor_mensalidade_fmt']}")
                                    st.write(f"   📅 Vencimento: {aluno['dia_vencimento_fmt']}")
                                    if aluno.get('data_matricula'):
                                        st.write(f"   🎓 Matrícula: {aluno['data_matricula']}")
                                    if aluno.get('turno'):
                                        st.write(f"   🕐 Turno: {aluno['turno']}")
                                    if i < len(alunos_completos) - 1:
                                        st.write("---")
                            else:
                                st.write("❌ Nenhum aluno vinculado")
                            
                            if tem_multiplos_alunos:
                                st.info(f"ℹ️ {len(alunos_completos)} alunos vinculados")
                        
                        with col3:
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
                                    if tem_multiplos_alunos and alunos_completos:
                                        opcoes_alunos = {f"{aluno['nome']} - {aluno['turma_nome']}": aluno for aluno in alunos_completos}
                                        aluno_selecionado = st.selectbox(
                                            "Aluno:",
                                            list(opcoes_alunos.keys()),
                                            key=f"aluno_{registro['id']}"
                                        )
                                        aluno_data = opcoes_alunos[aluno_selecionado]
                                        id_aluno = aluno_data["id"]
                                    else:
                                        # Usar primeiro aluno vinculado
                                        if alunos_completos and len(alunos_completos) > 0:
                                            id_aluno = alunos_completos[0]["id"]
                                            aluno_data = alunos_completos[0]
                                        else:
                                            id_aluno = None
                                            aluno_data = None
                                            st.error("❌ Nenhum aluno vinculado!")
                                    
                                    # Se é mensalidade, permitir seleção de mensalidade específica
                                    mensalidade_selecionada = None
                                    if tipo_pagamento == "mensalidade" and id_aluno:
                                        from funcoes_extrato_otimizadas import listar_mensalidades_disponiveis_aluno
                                        mensalidades_resultado = listar_mensalidades_disponiveis_aluno(id_aluno)
                                        
                                        if mensalidades_resultado.get("success") and mensalidades_resultado.get("mensalidades"):
                                            mensalidades_disponiveis = mensalidades_resultado["mensalidades"]
                                            opcoes_mensalidades = ["Selecione uma mensalidade..."] + [m["label"] for m in mensalidades_disponiveis]
                                            
                                            mensalidade_escolhida = st.selectbox(
                                                f"Mensalidade para {aluno_data['nome'] if aluno_data else 'aluno'}:",
                                                options=opcoes_mensalidades,
                                                key=f"mens_rapido_{registro['id']}"
                                            )
                                            
                                            if mensalidade_escolhida != "Selecione uma mensalidade...":
                                                mensalidade_selecionada = next(
                                                    (m for m in mensalidades_disponiveis if m["label"] == mensalidade_escolhida), 
                                                    None
                                                )
                                                
                                                if mensalidade_selecionada:
                                                    st.info(f"📅 {mensalidade_selecionada['mes_referencia']} - {mensalidade_selecionada['status_texto']}")
                                            else:
                                                st.warning("⚠️ Selecione uma mensalidade")
                                        else:
                                            st.warning(f"⚠️ Nenhuma mensalidade pendente para {aluno_data['nome'] if aluno_data else 'este aluno'}")
                                    
                                    if id_aluno and (tipo_pagamento != "mensalidade" or mensalidade_selecionada):
                                        config_rapida = {
                                            'id_extrato': registro['id'],
                                            'id_responsavel': id_responsavel,
                                            'configuracao_simples': True,
                                            'id_aluno': id_aluno,
                                            'tipo_pagamento': tipo_pagamento,
                                            'valor': registro['valor'],
                                            'registro': registro
                                        }
                                        
                                        # Se é mensalidade, adicionar dados da mensalidade
                                        if tipo_pagamento == "mensalidade" and mensalidade_selecionada:
                                            config_rapida['id_mensalidade'] = mensalidade_selecionada["id_mensalidade"]
                                            config_rapida['mes_referencia'] = mensalidade_selecionada["mes_referencia"]
                                            config_rapida['data_vencimento'] = mensalidade_selecionada["data_vencimento"]
                                        
                                        registros_configurados.append(config_rapida)
                        
                        with col3:
                            if selecionado and modo_processamento == "⚙️ Configuração Avançada":
                                if st.button("⚙️ Configurar", key=f"config_{registro['id']}"):
                                    st.session_state[f"show_config_{registro['id']}"] = True
                        
                # Salvar configurações do processamento rápido no estado da sessão
                # IMPORTANTE: Mesclar com configurações avançadas existentes, não sobrescrever
                configuracoes_existentes = st.session_state.get('registros_configurados', [])
                
                # Remover configurações simples do mesmo registro se houver
                configuracoes_existentes = [
                    config for config in configuracoes_existentes 
                    if not (config.get('configuracao_simples') and 
                           config.get('id_extrato') in [r.get('id_extrato') for r in registros_configurados])
                ]
                
                # Adicionar novas configurações simples
                configuracoes_existentes.extend(registros_configurados)
                
                # Atualizar session state
                st.session_state.registros_configurados = configuracoes_existentes
                
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
                        # Buscar configurações existentes
                        configuracoes_existentes = st.session_state.get('registros_configurados', [])
                        
                        # Remover configuração existente do mesmo registro se houver
                        configuracoes_existentes = [
                            config for config in configuracoes_existentes 
                            if config.get('id_extrato') != registro_para_configurar['id']
                        ]
                        
                        # Adicionar nova configuração avançada
                        configuracoes_existentes.append({
                            'id_extrato': registro_para_configurar['id'],
                            'id_responsavel': id_responsavel_config,
                            'configuracao_multipla': True,
                            'pagamentos_detalhados': config_resultado['pagamentos_detalhados'],
                            'valor_total': config_resultado['valor_total'],
                            'registro': registro_para_configurar
                        })
                        
                        # Salvar no session state
                        st.session_state.registros_configurados = configuracoes_existentes
                        st.session_state[f"show_config_{registro_para_configurar['id']}"] = False
                        
                        st.success(f"✅ Configuração salva: {config_resultado['total_pagamentos']} pagamentos")
                        st.rerun()
                
                # Resumo dos registros configurados (incluindo avançados já salvos)
                todas_configuracoes = st.session_state.get('registros_configurados', [])
                
                if todas_configuracoes:
                    st.markdown("---")
                    st.subheader("📊 Resumo dos Registros Configurados")
                    
                    total_simples = len([r for r in todas_configuracoes if r.get('configuracao_simples')])
                    total_multiplos = len([r for r in todas_configuracoes if r.get('configuracao_multipla')])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🚀 Processamento Rápido", total_simples)
                    with col2:
                        st.metric("⚙️ Configuração Avançada", total_multiplos)
                    with col3:
                        st.metric("📋 Total", len(todas_configuracoes))
                    
                    # Detalhes melhorados
                    st.markdown("### 📋 Detalhes dos Registros Configurados")
                    
                    for i, config in enumerate(todas_configuracoes, 1):
                        registro = config.get('registro', {})
                        
                        if config.get('configuracao_simples'):
                            # Buscar dados do aluno
                            aluno_id = config.get('id_aluno')
                            aluno_nome = "N/A"
                            
                            # Tentar buscar nome do aluno a partir dos dados já carregados
                            if registro and registro.get('responsaveis'):
                                # Se há dados de responsáveis no registro, pode haver dados de alunos
                                pass  # Aqui poderia buscar se necessário
                            
                            responsavel_nome = registro.get('nome_remetente', 'N/A')
                            data_pagamento = registro.get('data_pagamento', 'N/A')
                            
                            # Informações sobre mensalidade se aplicável
                            info_mensalidade = ""
                            if config.get('tipo_pagamento') == 'mensalidade' and config.get('mes_referencia'):
                                info_mensalidade = f" ({config.get('mes_referencia')})"
                            
                            with st.container():
                                st.markdown(f"""
                                **🚀 {i}. Processamento Rápido** - R$ {config['valor']:.2f}
                                - 📅 **Data:** {data_pagamento}
                                - 👤 **Responsável:** {responsavel_nome}
                                - 💳 **Tipo:** {config['tipo_pagamento']}{info_mensalidade}
                                - 🆔 **Extrato:** {config.get('id_extrato', 'N/A')[:8]}...
                                """)
                                
                        elif config.get('configuracao_multipla'):
                            detalhes = config['pagamentos_detalhados']
                            responsavel_nome = registro.get('nome_remetente', 'N/A')
                            data_pagamento = registro.get('data_pagamento', 'N/A')
                            
                            with st.container():
                                st.markdown(f"""
                                **⚙️ {i}. Configuração Avançada** - R$ {config['valor_total']:.2f}
                                - 📅 **Data:** {data_pagamento}
                                - 👤 **Responsável:** {responsavel_nome}
                                - 🆔 **Extrato:** {config.get('id_extrato', 'N/A')[:8]}...
                                """)
                                
                                # Listar cada pagamento detalhado
                                for j, det in enumerate(detalhes, 1):
                                    info_mensalidade = ""
                                    if det.get('tipo_pagamento') == 'mensalidade' and det.get('mes_referencia'):
                                        info_mensalidade = f" ({det.get('mes_referencia')})"
                                    
                                    st.markdown(f"  **{j}.** {det.get('nome_aluno', 'N/A')} - {det.get('tipo_pagamento')}{info_mensalidade} - R$ {det.get('valor', 0):.2f}")
                        
                        if i < len(todas_configuracoes):
                            st.markdown("---")
                
                elif registros_configurados:
                    # Fallback para mostrar apenas os configurados no loop atual
                    st.markdown("---")
                    st.subheader("📊 Registros Selecionados para Processamento")
                    
                    total_simples = len([r for r in registros_configurados if r.get('configuracao_simples')])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("🚀 Processamento Rápido", total_simples)
                    with col2:
                        st.metric("📋 Total", len(registros_configurados))
                    
                    # Detalhes melhorados
                    st.markdown("### 📋 Detalhes dos Registros Selecionados")
                    
                    for i, config in enumerate(registros_configurados, 1):
                        registro = config.get('registro', {})
                        
                        if config.get('configuracao_simples'):
                            responsavel_nome = registro.get('nome_remetente', 'N/A')
                            data_pagamento = registro.get('data_pagamento', 'N/A')
                            
                            # Informações sobre mensalidade se aplicável
                            info_mensalidade = ""
                            if config.get('tipo_pagamento') == 'mensalidade' and config.get('mes_referencia'):
                                info_mensalidade = f" ({config.get('mes_referencia')})"
                            
                            st.markdown(f"""
                            **🚀 {i}. Processamento Rápido** - R$ {config['valor']:.2f}
                            - 📅 **Data:** {data_pagamento}
                            - 👤 **Responsável:** {responsavel_nome}
                            - 💳 **Tipo:** {config['tipo_pagamento']}{info_mensalidade}
                            - 🆔 **Extrato:** {config.get('id_extrato', 'N/A')[:8]}...
                            """)
    
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
                            st.markdown("**🎯 Ações:**")
                            
                            # Botão para cadastrar responsável
                            if st.button(
                                "📝 Cadastrar Responsável", 
                                key=f"cad_resp_{registro['id']}",
                                use_container_width=True
                            ):
                                st.session_state[f"show_form_{registro['id']}"] = True
                            
                            # Botão para ignorar registro
                            if st.button(
                                "🚫 Ignorar Registro", 
                                key=f"ignore_{registro['id']}",
                                help="Marca como ignorado e remove da lista",
                                use_container_width=True
                            ):
                                resultado_ignore = ignorar_registro_extrato(registro['id'])
                                if resultado_ignore.get("success"):
                                    st.success("✅ Registro marcado como ignorado!")
                                    # Recarregar dados
                                    carregar_dados_extrato()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erro: {resultado_ignore.get('error')}")
                        
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
        
        # Botões principais
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Busca de aluno melhorada
            busca_aluno = st.text_input("🔍 Buscar aluno por nome", key="busca_gestao_aluno", placeholder="Digite pelo menos 2 caracteres...")
        
        with col2:
            st.write("")  # Espaço para alinhar
            if st.button("🎓 Cadastrar Novo Aluno", type="primary", key="btn_cadastrar_aluno"):
                st.session_state.show_cadastro_aluno = True
        
        # Formulário de cadastro de aluno
        if st.session_state.get('show_cadastro_aluno', False):
            st.markdown("---")
            resultado = mostrar_formulario_cadastro_aluno()
            
            if resultado:
                # Sucesso no cadastro - limpar flag e recarregar busca
                st.session_state.show_cadastro_aluno = False
                # Atualizar lista de alunos se estava buscando
                if busca_aluno:
                    resultado_busca = buscar_alunos_para_dropdown(busca_aluno)
                    if resultado_busca.get("success"):
                        st.session_state.lista_alunos_gestao = resultado_busca.get("opcoes", [])
                st.rerun()
        
        # Botão para fechar formulário de cadastro
        if st.session_state.get('show_cadastro_aluno', False):
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("❌ Cancelar Cadastro", type="secondary"):
                    st.session_state.show_cadastro_aluno = False
                    st.rerun()
            st.markdown("---")
        
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
        
        # Exibir lista de alunos encontrados (apenas se não estiver mostrando cadastro)
        if not st.session_state.get('show_cadastro_aluno', False):
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
            elif len(busca_aluno) == 0:
                st.info("🔍 Digite o nome de um aluno para buscar ou clique em 'Cadastrar Novo Aluno' para adicionar um novo aluno.")
    
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
        # ==========================================================
    # TAB 5: CONSISTÊNCIA
    # ==========================================================
    with tab5:
        st.header("🔍 Verificação de Consistência")
        st.markdown("Ferramentas para verificar e corrigir inconsistências entre extrato PIX e pagamentos registrados.")
        
        # Controles de período
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            data_inicio_consist = st.date_input(
                "📅 Data Início",
                value=st.session_state.filtro_data_inicio,
                key="consist_inicio"
            )
        
        with col2:
            data_fim_consist = st.date_input(
                "📅 Data Fim", 
                value=st.session_state.filtro_data_fim,
                key="consist_fim"
            )
        
        with col3:
            st.write(" ")  # Espaço
            if st.button("🔍 Executar Verificação", type="primary"):
                st.session_state.executar_verificacao = True
        
        # Executar verificação se solicitado
        if st.session_state.get('executar_verificacao', False):
            st.session_state.executar_verificacao = False  # Reset flag
            
            with st.spinner("🔍 Analisando consistência..."):
                # 1. Relatório de consistência
                resultado_consistencia = verificar_consistencia_extrato_pagamentos(
                    data_inicio_consist.strftime("%Y-%m-%d"),
                    data_fim_consist.strftime("%Y-%m-%d")
                )
                
                if resultado_consistencia.get("success"):
                    relatorio = resultado_consistencia["relatorio"]
                    
                    # Métricas principais
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Total Extrato", relatorio["total_extrato"])
                    
                    with col2:
                        st.metric("💳 Pagamentos (Origem Extrato)", relatorio["total_pagamentos_origem_extrato"])
                    
                    with col3:
                        inconsistencias = len(relatorio["inconsistencias"])
                        st.metric("⚠️ Inconsistências", inconsistencias, delta="Problema" if inconsistencias > 0 else "OK")
                    
                    with col4:
                        novos = relatorio["status_extrato"].get("novo", 0)
                        st.metric("🆕 Status 'Novo'", novos)
                    
                    # Status breakdown
                    st.subheader("📊 Distribuição por Status")
                    
                    if relatorio["status_extrato"]:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            for status, count in relatorio["status_extrato"].items():
                                emoji = "🆕" if status == "novo" else "✅" if status == "registrado" else "🚫" if status == "ignorado" else "❓"
                                st.write(f"{emoji} **{status.title()}:** {count} registros")
                        
                        with col2:
                            # Gráfico de pizza para status
                            if len(relatorio["status_extrato"]) > 1:
                                df_status = pd.DataFrame(
                                    list(relatorio["status_extrato"].items()),
                                    columns=["Status", "Quantidade"]
                                )
                                
                                fig = px.pie(
                                    df_status, 
                                    values="Quantidade", 
                                    names="Status",
                                    title="Distribuição de Status",
                                    color_discrete_map={
                                        "novo": "#ff7f0e",
                                        "registrado": "#2ca02c", 
                                        "ignorado": "#d62728"
                                    }
                                )
                                fig.update_layout(height=300)
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Inconsistências encontradas
                    if relatorio["inconsistencias"]:
                        st.subheader("⚠️ Inconsistências Encontradas")
                        st.error(f"Foram encontradas {len(relatorio['inconsistencias'])} inconsistências que precisam ser corrigidas.")
                        
                        # Mostrar detalhes das inconsistências
                        for i, inconsistencia in enumerate(relatorio["inconsistencias"]):
                            with st.expander(f"❌ Inconsistência {i+1}: {inconsistencia['nome_remetente']} - R$ {inconsistencia['valor']:.2f}"):
                                st.write(f"**🆔 ID Extrato:** {inconsistencia['id_extrato']}")
                                st.write(f"**📅 Data:** {inconsistencia['data']}")
                                st.write(f"**💰 Valor:** R$ {inconsistencia['valor']:.2f}")
                                st.write(f"**🔄 Status no Extrato:** novo (deveria ser 'registrado')")
                                st.write(f"**💳 Pagamentos Encontrados:** {', '.join(inconsistencia['pagamentos_encontrados'])}")
                        
                        # Botão para corrigir automaticamente
                        st.markdown("---")
                        if st.button("🔧 CORRIGIR AUTOMATICAMENTE", type="primary"):
                            with st.spinner("Aplicando correções..."):
                                resultado_correcao = verificar_e_corrigir_extrato_duplicado()
                                
                                if resultado_correcao.get("success"):
                                    corrigidos = resultado_correcao.get("corrigidos", 0)
                                    if corrigidos > 0:
                                        st.success(f"✅ {corrigidos} registros corrigidos com sucesso!")
                                        
                                        # Mostrar detalhes das correções
                                        detalhes = resultado_correcao.get("detalhes", [])
                                        if detalhes:
                                            st.subheader("✅ Correções Aplicadas")
                                            for correcao in detalhes:
                                                st.write(f"• **{correcao['nome_remetente']}** - R$ {correcao['valor']:.2f}")
                                                st.write(f"  📅 {correcao['data_pagamento']} | 🆔 Extrato: {correcao['id_extrato']} | 💳 Pagamento: {correcao['id_pagamento_encontrado']}")
                                        
                                        st.info("🔄 Execute a verificação novamente para confirmar que as inconsistências foram resolvidas.")
                                    else:
                                        st.warning("⚠️ Nenhuma correção foi aplicada.")
                                else:
                                    st.error(f"❌ Erro na correção: {resultado_correcao.get('error')}")
                    
                    else:
                        st.success("✅ Nenhuma inconsistência encontrada! O banco de dados está consistente.")
                        
                        if relatorio["total_extrato"] > 0:
                            st.info(f"📊 Todos os {relatorio['total_extrato']} registros do extrato estão com status correto.")
                
                else:
                    st.error(f"❌ Erro na verificação: {resultado_consistencia.get('error')}")
        
        # Informações sobre a funcionalidade
        if not st.session_state.get('executar_verificacao', False):
            st.markdown("---")
            st.subheader("ℹ️ Sobre a Verificação de Consistência")
            
            st.markdown("""
            **🎯 O que esta ferramenta faz:**
            
            1. **Analisa** registros do extrato PIX com status 'novo'
            2. **Verifica** se já existem pagamentos correspondentes na tabela de pagamentos
            3. **Identifica** registros duplicados ou inconsistentes
            4. **Corrige** automaticamente o status para 'registrado' quando apropriado
            
            **🔍 Critérios de Identificação:**
            
            - Mesmo **responsável**, **valor** e **data de pagamento**
            - Pagamento com flag `origem_extrato = true`
            - Referência ao ID do extrato original (`id_extrato_origem`)
            
            **⚠️ Quando usar:**
            
            - Após importar novos dados do extrato PIX
            - Quando notar registros duplicados na interface
            - Como manutenção periódica do banco de dados
            - Antes de processar pagamentos em lote
            """)
            
            # Botão de verificação rápida
            if st.button("🚀 Verificação Rápida (Últimos 30 dias)", type="secondary"):
                st.session_state.executar_verificacao = True
                st.rerun()

    # ==========================================================
    # TAB 6: VINCULAR RESPONSÁVEIS
    # ==========================================================
    with tab6:
        st.header("🔗 Vincular Responsáveis Automaticamente")
        st.markdown("Ferramenta para identificar e vincular responsáveis aos registros do extrato PIX automaticamente.")
        
        # Informações sobre a funcionalidade
        st.markdown("---")
        st.subheader("ℹ️ Como Funciona")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 O que esta ferramenta faz:**
            
            1. **Identifica** registros do extrato PIX sem `id_responsavel`
            2. **Compara** nome do remetente com nomes na tabela `responsaveis`
            3. **Aplica** correspondência com similaridade **≥ 90%**
            4. **Preenche** automaticamente `id_responsavel` no extrato
            5. **Preenche** `id_aluno` se responsável tem apenas 1 aluno vinculado
            """)
        
        with col2:
            st.markdown("""
            **🔍 Critérios de Correspondência:**
            
            - **Similaridade:** Mínimo 90% entre nomes
            - **Algoritmo:** difflib.SequenceMatcher
            - **Normalização:** Usa `nome_norm` se disponível, senão `nome`
            - **Comparação:** Case insensitive, remove espaços extras
            - **Responsáveis com 1 aluno:** `id_aluno` preenchido automaticamente
            - **Responsáveis com >1 aluno:** `id_aluno` preenchido no registro do pagamento
            """)
        
        # Botão principal
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("🚀 EXECUTAR VINCULAÇÃO", type="primary", help="Analisa todos os registros sem responsável"):
                st.session_state.executar_vinculacao = True
        
        # Executar vinculação se solicitado
        if st.session_state.get('executar_vinculacao', False):
            st.session_state.executar_vinculacao = False  # Reset flag
            
            with st.spinner("🔍 Analisando registros sem responsável..."):
                resultado_responsaveis = atualizar_responsaveis_extrato_pix()
                
                if resultado_responsaveis.get("success"):
                    atualizados = resultado_responsaveis.get("atualizados", 0)
                    total_analisados = resultado_responsaveis.get("total_analisados", 0)
                    usou_nome_norm = resultado_responsaveis.get("usou_nome_norm", False)
                    
                    # Informação sobre normalização
                    if usou_nome_norm:
                        st.success("🔍 **Usando campo 'nome_norm'** - Melhor precisão na correspondência!")
                    else:
                        st.warning("⚠️ **Campo 'nome_norm' não encontrado** - Usando campo 'nome' padrão")
                    
                    # Métricas principais
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Registros Analisados", total_analisados)
                    
                    with col2:
                        st.metric("✅ Vinculações Realizadas", atualizados)
                    
                    with col3:
                        if total_analisados > 0:
                            taxa_sucesso = (atualizados / total_analisados) * 100
                            st.metric("📈 Taxa de Sucesso", f"{taxa_sucesso:.1f}%")
                        else:
                            st.metric("📈 Taxa de Sucesso", "N/A")
                    
                    with col4:
                        restantes = total_analisados - atualizados
                        st.metric("⚠️ Restantes", restantes, delta="Pendentes" if restantes > 0 else "Completo")
                    
                    if atualizados > 0:
                        st.success(f"✅ {atualizados} registros vinculados com sucesso!")
                        
                        # Detalhes das correspondências
                        correspondencias = resultado_responsaveis.get("correspondencias", [])
                        if correspondencias:
                            st.subheader("📋 Correspondências Realizadas")
                            
                            # Criar DataFrame para melhor visualização
                            df_correspondencias = []
                            for i, correspondencia in enumerate(correspondencias, 1):
                                # Criar indicador de nome normalizado
                                nome_comparacao = correspondencia.get('nome_usado_comparacao', correspondencia['nome_responsavel'])
                                nome_display = correspondencia['nome_responsavel']
                                if correspondencia.get('usado_nome_norm'):
                                    nome_display += f" (norm: {nome_comparacao})"
                                
                                df_correspondencias.append({
                                    "#": i,
                                    "Nome Remetente": correspondencia['nome_remetente'],
                                    "Responsável Encontrado": nome_display,
                                    "Similaridade": f"{correspondencia['similaridade']:.1f}%",
                                    "Alunos Vinculados": correspondencia['alunos_vinculados'],
                                    "ID Aluno Preenchido": "✅" if correspondencia['id_aluno_preenchido'] else "⚠️",
                                    "Usado nome_norm": "✅" if correspondencia.get('usado_nome_norm') else "❌"
                                })
                            
                            if df_correspondencias:
                                st.dataframe(
                                    df_correspondencias,
                                    column_config={
                                        "#": st.column_config.NumberColumn("Item", width="small"),
                                        "Nome Remetente": st.column_config.TextColumn("Remetente PIX"),
                                        "Responsável Encontrado": st.column_config.TextColumn("Responsável Cadastrado"),
                                        "Similaridade": st.column_config.TextColumn("Similaridade", width="small"),
                                        "Alunos Vinculados": st.column_config.NumberColumn("Alunos", width="small"),
                                        "ID Aluno Preenchido": st.column_config.TextColumn("Aluno OK", width="small"),
                                        "Usado nome_norm": st.column_config.TextColumn("Nome Norm", width="small")
                                    },
                                    use_container_width=True,
                                    height=300
                                )
                                
                                # Resumo por categoria
                                st.subheader("📊 Resumo por Categoria")
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    # Contagem por número de alunos
                                    alunos_1 = len([c for c in correspondencias if c['alunos_vinculados'] == 1])
                                    alunos_mult = len([c for c in correspondencias if c['alunos_vinculados'] > 1])
                                    
                                    st.markdown("**👨‍🎓 Por Número de Alunos:**")
                                    st.write(f"• **1 aluno vinculado:** {alunos_1} responsáveis (ID aluno preenchido)")
                                    st.write(f"• **Múltiplos alunos:** {alunos_mult} responsáveis (ID aluno pendente)")
                                
                                with col2:
                                    # Contagem por faixa de similaridade
                                    alta_similaridade = len([c for c in correspondencias if c['similaridade'] >= 95])
                                    media_similaridade = len([c for c in correspondencias if 90 <= c['similaridade'] < 95])
                                    
                                    st.markdown("**🎯 Por Similaridade:**")
                                    st.write(f"• **≥ 95%:** {alta_similaridade} correspondências (alta confiança)")
                                    st.write(f"• **90-94%:** {media_similaridade} correspondências (média confiança)")
                        
                        # Recarregar dados após atualização
                        st.info("🔄 Recarregando dados do extrato...")
                        carregar_dados_extrato()
                        st.rerun()
                        
                    else:
                        st.info("ℹ️ Nenhuma correspondência válida encontrada (similaridade ≥ 90%)")
                        
                        # Mostrar análise detalhada
                        debug_info = resultado_responsaveis.get("debug_info", [])
                        if debug_info:
                            with st.expander("📋 Ver Análise Detalhada"):
                                for debug_line in debug_info:
                                    st.text(debug_line)
                
                else:
                    st.error(f"❌ Erro ao executar vinculação: {resultado_responsaveis.get('error')}")
                    
                    # Mostrar informações de debug em caso de erro
                    debug_info = resultado_responsaveis.get("debug_info", [])
                    if debug_info:
                        with st.expander("🔍 Ver Detalhes do Erro"):
                            for debug_line in debug_info:
                                st.text(debug_line)
        
        # Informações adicionais sobre o processo
        if not st.session_state.get('executar_vinculacao', False):
            st.markdown("---")
            st.subheader("💡 Dicas de Uso")
            
            st.markdown("""
            **📝 Antes de Executar:**
            
            - Certifique-se de que os responsáveis estão cadastrados na tabela `responsaveis`
            - Verifique se os nomes estão preenchidos corretamente
            - Execute após importar novos dados do extrato PIX
            
            **⚠️ Importante:**
            
            - Responsáveis com **1 aluno:** O campo `id_aluno` será preenchido automaticamente
            - Responsáveis com **múltiplos alunos:** O `id_aluno` será preenchido durante o registro do pagamento
            - A ferramenta usa **similaridade ≥ 90%** para evitar correspondências incorretas
            - Registros já com `id_responsavel` preenchido são ignorados
            
            **🔄 Após a Execução:**
            
            - Verifique os resultados na aba "✅ Pagamentos COM Responsável"
            - Registros com correspondências aparecerão como "com responsável"
            - Para múltiplos alunos, selecione o aluno específico durante o registro do pagamento
            """)
            
            # Botão de execução rápida
            if st.button("🚀 Executar Agora", type="secondary"):
                st.session_state.executar_vinculacao = True
                st.rerun()


def processar_acoes_com_responsavel():
    """Processa ações selecionadas para registros com responsável com debugging completo"""
    registros = st.session_state.get('registros_configurados', [])
    
    # Debug inicial mais detalhado
    st.write(f"🔍 **DEBUG:** Encontrados {len(registros)} registros no session_state")
    if registros:
        for i, reg in enumerate(registros):
            tipo = 'Múltiplo' if reg.get('configuracao_multipla') else 'Simples'
            st.write(f"   Registro {i+1}: ID={reg.get('id_extrato')}, Tipo={tipo}")
            
            # Detalhes adicionais
            if reg.get('configuracao_multipla'):
                detalhes = reg.get('pagamentos_detalhados', [])
                st.write(f"      - {len(detalhes)} pagamentos detalhados")
                for j, det in enumerate(detalhes):
                    st.write(f"        {j+1}. Aluno: {det.get('id_aluno')}, Tipo: {det.get('tipo_pagamento')}, Valor: R$ {det.get('valor', 0):.2f}")
            elif reg.get('configuracao_simples'):
                st.write(f"      - Aluno: {reg.get('id_aluno')}, Tipo: {reg.get('tipo_pagamento')}, Valor: R$ {reg.get('valor', 0):.2f}")
    else:
        st.write("   ❌ Nenhuma configuração encontrada no session_state")
        
        # Debug adicional: mostrar tudo que está no session state
        st.write("🔍 **DEBUG SESSION STATE:**")
        for key, value in st.session_state.items():
            if 'registros' in key or 'config' in key:
                st.write(f"   - {key}: {type(value)} = {value}")
    
    if not registros:
        st.warning("❌ Nenhum registro configurado encontrado!")
        st.info("📋 **Instruções:**")
        st.info("1. **Processamento Rápido:** Marque os checkboxes 'Processar este registro' nos expanders")
        st.info("2. **Configuração Avançada:** Clique em 'Configurar' e finalize a configuração")
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
                
                # Verificar se tem mensalidade associada
                id_mensalidade = item.get('id_mensalidade') if item.get('tipo_pagamento') == 'mensalidade' else None
                
                resultado = registrar_pagamento_do_extrato(
                    id_extrato=item['id_extrato'],
                    id_responsavel=item['id_responsavel'],
                    id_aluno=item['id_aluno'],
                    tipo_pagamento=item['tipo_pagamento'],
                    id_mensalidade=id_mensalidade
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