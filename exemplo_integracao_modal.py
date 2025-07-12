#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📋 EXEMPLO DE INTEGRAÇÃO DO MODAL DE MENSALIDADE
===============================================

Demonstra como integrar o modal de mensalidade em uma interface principal
de gestão de mensalidades escolares.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

# Importar o modal de mensalidade
from modal_mensalidade import open_modal
from modal_mensalidade_integracoes import (
    gerar_relatorio_mensalidade_docx,
    enviar_email_cobranca,
    gerar_link_whatsapp
)

# Importar dependências do sistema
from models.base import supabase, formatar_data_br, formatar_valor_br

# ==========================================================
# 🔧 FUNÇÕES DE APOIO PARA A INTERFACE PRINCIPAL
# ==========================================================

def buscar_mensalidades_filtradas(filtros: Dict) -> Dict:
    """
    Busca mensalidades aplicando filtros especificados
    
    Args:
        filtros: Dict com filtros (turma, periodo, status, nome_aluno)
        
    Returns:
        Dict: {"success": bool, "mensalidades": List[Dict], "count": int}
    """
    try:
        query = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, 
            data_pagamento, status, observacoes, inserted_at, updated_at,
            alunos!inner(
                id, nome, turno,
                turmas!inner(nome_turma)
            )
        """)
        
        # Aplicar filtros
        if filtros.get("turma") and filtros["turma"] != "Todas":
            query = query.eq("alunos.turmas.nome_turma", filtros["turma"])
        
        if filtros.get("status") and filtros["status"] != "Todos":
            query = query.eq("status", filtros["status"])
        
        if filtros.get("data_inicio"):
            query = query.gte("data_vencimento", filtros["data_inicio"])
        
        if filtros.get("data_fim"):
            query = query.lte("data_vencimento", filtros["data_fim"])
        
        # Executar query
        response = query.order("data_vencimento", desc=True).execute()
        
        mensalidades = response.data if response.data else []
        
        # Filtrar por nome do aluno se especificado
        if filtros.get("nome_aluno"):
            nome_filtro = filtros["nome_aluno"].lower()
            mensalidades = [
                m for m in mensalidades 
                if nome_filtro in m["alunos"]["nome"].lower()
            ]
        
        return {
            "success": True,
            "mensalidades": mensalidades,
            "count": len(mensalidades)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mensalidades": [],
            "count": 0
        }

def aplicar_edicao_em_massa(ids_mensalidades: List[str], dados_alteracao: Dict) -> Dict:
    """
    Aplica alterações em massa para mensalidades selecionadas
    
    Args:
        ids_mensalidades: Lista de IDs das mensalidades
        dados_alteracao: Dados para alterar
        
    Returns:
        Dict: {"success": bool, "alteradas": int, "erros": List[str]}
    """
    try:
        alteradas = 0
        erros = []
        
        for id_mensalidade in ids_mensalidades:
            try:
                response = supabase.table("mensalidades").update(dados_alteracao).eq(
                    "id_mensalidade", id_mensalidade
                ).execute()
                
                if response.data:
                    alteradas += 1
                else:
                    erros.append(f"Erro ao alterar {id_mensalidade}")
                    
            except Exception as e:
                erros.append(f"Erro em {id_mensalidade}: {str(e)}")
        
        return {
            "success": True,
            "alteradas": alteradas,
            "erros": erros
        }
        
    except Exception as e:
        return {
            "success": False,
            "alteradas": 0,
            "erros": [str(e)]
        }

# ==========================================================
# 🎨 INTERFACE PRINCIPAL DE MENSALIDADES
# ==========================================================

def interface_gestao_mensalidades():
    """
    Interface principal para gestão de mensalidades com integração do modal
    """
    
    st.title("💰 Gestão de Mensalidades")
    st.markdown("Interface completa para gerenciar mensalidades escolares")
    
    # Inicializar estado da sessão
    if 'filtros_mensalidades' not in st.session_state:
        st.session_state.filtros_mensalidades = {
            "turma": "Todas",
            "status": "Todos",
            "data_inicio": (date.today() - timedelta(days=90)).isoformat(),
            "data_fim": date.today().isoformat(),
            "nome_aluno": ""
        }
    
    if 'mensalidades_selecionadas' not in st.session_state:
        st.session_state.mensalidades_selecionadas = []
    
    if 'modal_aberto' not in st.session_state:
        st.session_state.modal_aberto = False
    
    if 'id_mensalidade_modal' not in st.session_state:
        st.session_state.id_mensalidade_modal = None
    
    # ==========================================================
    # SEÇÃO DE FILTROS
    # ==========================================================
    
    with st.expander("🔍 Filtros de Busca", expanded=True):
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        
        with col_filtro1:
            # Buscar turmas disponíveis
            try:
                turmas_response = supabase.table("turmas").select("nome_turma").execute()
                turmas_opcoes = ["Todas"] + [t["nome_turma"] for t in turmas_response.data]
            except:
                turmas_opcoes = ["Todas"]
            
            st.session_state.filtros_mensalidades["turma"] = st.selectbox(
                "🎓 Turma:",
                options=turmas_opcoes,
                index=turmas_opcoes.index(st.session_state.filtros_mensalidades["turma"]) if st.session_state.filtros_mensalidades["turma"] in turmas_opcoes else 0
            )
            
            st.session_state.filtros_mensalidades["status"] = st.selectbox(
                "📊 Status:",
                options=["Todos", "A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"]
            )
        
        with col_filtro2:
            st.session_state.filtros_mensalidades["data_inicio"] = st.date_input(
                "📅 Data Início:",
                value=datetime.fromisoformat(st.session_state.filtros_mensalidades["data_inicio"]).date()
            ).isoformat()
            
            st.session_state.filtros_mensalidades["data_fim"] = st.date_input(
                "📅 Data Fim:",
                value=datetime.fromisoformat(st.session_state.filtros_mensalidades["data_fim"]).date()
            ).isoformat()
        
        with col_filtro3:
            st.session_state.filtros_mensalidades["nome_aluno"] = st.text_input(
                "🔍 Nome do Aluno:",
                value=st.session_state.filtros_mensalidades["nome_aluno"],
                placeholder="Digite parte do nome..."
            )
            
            # Botão para aplicar filtros
            if st.button("🔄 Aplicar Filtros", type="primary"):
                st.session_state.dados_atualizados = True
    
    # ==========================================================
    # BUSCAR E EXIBIR MENSALIDADES
    # ==========================================================
    
    # Buscar dados se necessário
    if ('mensalidades_dados' not in st.session_state or 
        st.session_state.get('dados_atualizados', False)):
        
        with st.spinner("Carregando mensalidades..."):
            resultado = buscar_mensalidades_filtradas(st.session_state.filtros_mensalidades)
        
        if resultado.get("success"):
            st.session_state.mensalidades_dados = resultado["mensalidades"]
            st.session_state.dados_atualizados = False
        else:
            st.error(f"Erro ao carregar dados: {resultado.get('error')}")
            st.session_state.mensalidades_dados = []
    
    mensalidades = st.session_state.get('mensalidades_dados', [])
    
    # Métricas principais
    if mensalidades:
        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        
        total_mensalidades = len(mensalidades)
        valor_total = sum(float(m["valor"]) for m in mensalidades)
        pagas = len([m for m in mensalidades if m["status"] in ["Pago", "Pago parcial"]])
        atrasadas = len([m for m in mensalidades if m["status"] == "Atrasado"])
        
        with col_metric1:
            st.metric("📋 Total", total_mensalidades)
        
        with col_metric2:
            st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
        
        with col_metric3:
            st.metric("✅ Pagas", pagas, delta=f"{(pagas/total_mensalidades*100):.1f}%")
        
        with col_metric4:
            if atrasadas > 0:
                st.metric("⚠️ Atrasadas", atrasadas, delta="Atenção", delta_color="inverse")
            else:
                st.metric("⚠️ Atrasadas", 0)
    
    # ==========================================================
    # AÇÕES EM MASSA
    # ==========================================================
    
    if mensalidades:
        st.markdown("---")
        st.subheader("⚡ Ações em Massa")
        
        col_massa1, col_massa2, col_massa3 = st.columns(3)
        
        with col_massa1:
            # Seleção para ações em massa
            selecionadas = st.multiselect(
                "Selecionar mensalidades:",
                options=[m["id_mensalidade"] for m in mensalidades],
                format_func=lambda x: next(
                    f"{m['alunos']['nome']} - {m['mes_referencia']}" 
                    for m in mensalidades if m["id_mensalidade"] == x
                ),
                key="multiselect_mensalidades"
            )
            
            st.session_state.mensalidades_selecionadas = selecionadas
        
        with col_massa2:
            if selecionadas:
                st.info(f"📌 {len(selecionadas)} mensalidades selecionadas")
                
                # Ações disponíveis
                acao_massa = st.selectbox(
                    "Ação a aplicar:",
                    options=["", "Marcar como Pago", "Marcar como Atrasado", "Adicionar Observação"],
                    key="acao_massa_select"
                )
        
        with col_massa3:
            if selecionadas and acao_massa:
                if st.button("🚀 Executar Ação em Massa", type="primary"):
                    
                    dados_alteracao = {}
                    
                    if acao_massa == "Marcar como Pago":
                        dados_alteracao = {
                            "status": "Pago",
                            "data_pagamento": date.today().isoformat()
                        }
                    elif acao_massa == "Marcar como Atrasado":
                        dados_alteracao = {"status": "Atrasado"}
                    elif acao_massa == "Adicionar Observação":
                        observacao = st.text_input("Observação a adicionar:", key="obs_massa")
                        dados_alteracao = {"observacoes": observacao}
                    
                    if dados_alteracao:
                        resultado_massa = aplicar_edicao_em_massa(selecionadas, dados_alteracao)
                        
                        if resultado_massa.get("success"):
                            st.success(f"✅ {resultado_massa['alteradas']} mensalidades alteradas!")
                            if resultado_massa.get("erros"):
                                st.warning(f"⚠️ {len(resultado_massa['erros'])} erros encontrados")
                            st.session_state.dados_atualizados = True
                            st.rerun()
                        else:
                            st.error("❌ Erro na execução em massa")
    
    # ==========================================================
    # TABELA DE MENSALIDADES COM BOTÕES DE AÇÃO
    # ==========================================================
    
    if mensalidades:
        st.markdown("---")
        st.subheader("📋 Lista de Mensalidades")
        
        # Preparar dados para exibição
        dados_tabela = []
        for m in mensalidades:
            # Calcular status visual
            status_emoji = "📅"
            if m["status"] == "Pago":
                status_emoji = "✅"
            elif m["status"] == "Atrasado":
                status_emoji = "⚠️"
            elif m["status"] == "Cancelado":
                status_emoji = "❌"
            
            dados_tabela.append({
                "ID": m["id_mensalidade"],
                "Aluno": m["alunos"]["nome"],
                "Turma": m["alunos"]["turmas"]["nome_turma"],
                "Mês": m["mes_referencia"],
                "Valor": f"R$ {float(m['valor']):,.2f}",
                "Vencimento": formatar_data_br(m["data_vencimento"]),
                "Status": f"{status_emoji} {m['status']}",
                "Observações": m.get("observacoes", "")[:50] + "..." if m.get("observacoes", "") and len(m.get("observacoes", "")) > 50 else m.get("observacoes", "")
            })
        
        # Exibir tabela
        df_mensalidades = pd.DataFrame(dados_tabela)
        
        # Tabela editável (permitir edição de observações)
        df_editado = st.data_editor(
            df_mensalidades,
            column_config={
                "ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
                "Aluno": st.column_config.TextColumn("Aluno", disabled=True),
                "Turma": st.column_config.TextColumn("Turma", disabled=True, width="small"),
                "Mês": st.column_config.TextColumn("Mês", disabled=True, width="small"),
                "Valor": st.column_config.TextColumn("Valor", disabled=True, width="small"),
                "Vencimento": st.column_config.TextColumn("Vencimento", disabled=True, width="small"),
                "Status": st.column_config.TextColumn("Status", disabled=True, width="small"),
                "Observações": st.column_config.TextColumn("Observações", width="medium")
            },
            use_container_width=True,
            height=400,
            key="tabela_mensalidades_editavel"
        )
        
        # Detectar mudanças na tabela e aplicar
        if not df_editado.equals(df_mensalidades):
            st.info("✏️ Modificações detectadas. Use o botão abaixo para salvar.")
            
            if st.button("💾 Salvar Alterações da Tabela", type="primary"):
                # Aplicar alterações das observações
                for idx, row in df_editado.iterrows():
                    id_mensalidade = row["ID"]
                    nova_observacao = row["Observações"]
                    
                    # Buscar observação original
                    mensalidade_original = next(m for m in mensalidades if m["id_mensalidade"] == id_mensalidade)
                    observacao_original = mensalidade_original.get("observacoes", "")
                    
                    # Se mudou, atualizar
                    if nova_observacao != observacao_original:
                        try:
                            supabase.table("mensalidades").update({
                                "observacoes": nova_observacao
                            }).eq("id_mensalidade", id_mensalidade).execute()
                        except Exception as e:
                            st.error(f"Erro ao atualizar {id_mensalidade}: {str(e)}")
                
                st.success("✅ Alterações salvas!")
                st.session_state.dados_atualizados = True
                st.rerun()
        
        # Botões de ação para cada linha
        st.markdown("#### 🎯 Ações Individuais")
        st.info("💡 **Dica:** Clique nos botões abaixo para abrir o modal de detalhes de cada mensalidade")
        
        # Criar colunas para os botões (máximo 5 por linha)
        cols_per_row = 5
        num_rows = (len(mensalidades) + cols_per_row - 1) // cols_per_row
        
        for row in range(num_rows):
            cols = st.columns(cols_per_row)
            
            for col_idx in range(cols_per_row):
                mensalidade_idx = row * cols_per_row + col_idx
                
                if mensalidade_idx < len(mensalidades):
                    mensalidade = mensalidades[mensalidade_idx]
                    
                    with cols[col_idx]:
                        # Botão para abrir modal
                        nome_aluno = mensalidade["alunos"]["nome"]
                        mes_ref = mensalidade["mes_referencia"]
                        
                        # Usar nome curto para o botão
                        nome_curto = nome_aluno.split()[0] if nome_aluno else "Aluno"
                        label_botao = f"👁️ {nome_curto}\n{mes_ref}"
                        
                        if st.button(
                            label_botao,
                            key=f"modal_btn_{mensalidade['id_mensalidade']}",
                            help=f"Ver detalhes de {nome_aluno} - {mes_ref}",
                            use_container_width=True
                        ):
                            st.session_state.modal_aberto = True
                            st.session_state.id_mensalidade_modal = mensalidade["id_mensalidade"]
                            st.rerun()
        
    else:
        st.info("ℹ️ Nenhuma mensalidade encontrada com os filtros aplicados")
        st.info("💡 Ajuste os filtros acima para buscar mensalidades")
    
    # ==========================================================
    # MODAL DE DETALHES (SE ATIVO)
    # ==========================================================
    
    if st.session_state.get('modal_aberto', False) and st.session_state.get('id_mensalidade_modal'):
        st.markdown("---")
        st.markdown("## 🔍 Detalhes da Mensalidade")
        
        # Abrir o modal
        try:
            open_modal(st.session_state.id_mensalidade_modal)
            
        except Exception as e:
            st.error(f"❌ Erro ao abrir modal: {str(e)}")
            st.session_state.modal_aberto = False
            st.session_state.id_mensalidade_modal = None
    
    # ==========================================================
    # AÇÕES GLOBAIS
    # ==========================================================
    
    st.markdown("---")
    st.subheader("🛠️ Ações Globais")
    
    col_global1, col_global2, col_global3 = st.columns(3)
    
    with col_global1:
        if st.button("🔄 Recarregar Dados", use_container_width=True):
            st.session_state.dados_atualizados = True
            st.rerun()
    
    with col_global2:
        if st.button("📊 Exportar Relatório", use_container_width=True):
            # TODO: Implementar exportação de relatório geral
            st.info("🔧 Funcionalidade em desenvolvimento")
    
    with col_global3:
        if st.button("📧 Envio em Massa", use_container_width=True):
            # TODO: Implementar envio de emails em massa
            st.info("🔧 Funcionalidade em desenvolvimento")

# ==========================================================
# 🚀 EXECUTAR A INTERFACE
# ==========================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Gestão de Mensalidades",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
    st.markdown("""
    <style>
        .stButton > button {
            width: 100%;
        }
        .metric-card {
            background: linear-gradient(90deg, #1f77b4, #2ca02c);
            padding: 1rem;
            border-radius: 0.5rem;
            color: white;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Executar interface principal
    interface_gestao_mensalidades() 