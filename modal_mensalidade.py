#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💰 MODAL DE DETALHAMENTO E AÇÕES DE MENSALIDADE
===============================================

Modal completo para visualizar, editar e executar ações em mensalidades individuais.
Inclui detalhes, edição, ações, histórico e relatórios.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import json

# Importar dependências do sistema
from models.base import (
    supabase, formatar_data_br, formatar_valor_br, obter_timestamp
)

# ==========================================================
# 🔧 FUNÇÕES AUXILIARES
# ==========================================================

def buscar_dados_mensalidade(id_mensalidade: str) -> Dict:
    """
    Busca dados completos da mensalidade incluindo informações do aluno e responsável
    
    Args:
        id_mensalidade: ID da mensalidade
        
    Returns:
        Dict: {"success": bool, "dados": Dict, "error": str}
    """
    try:
        response = supabase.table("mensalidades").select("""
            *,
            alunos!inner(
                id, nome, turno, valor_mensalidade,
                turmas!inner(nome_turma)
            )
        """).eq("id_mensalidade", id_mensalidade).execute()
        
        if not response.data:
            return {"success": False, "error": "Mensalidade não encontrada"}
        
        mensalidade = response.data[0]
        
        # Buscar responsável financeiro do aluno
        id_aluno = mensalidade["alunos"]["id"]
        resp_response = supabase.table("alunos_responsaveis").select("""
            responsaveis!inner(id, nome, telefone, email, cpf)
        """).eq("id_aluno", id_aluno).eq("responsavel_financeiro", True).execute()
        
        responsavel = None
        if resp_response.data:
            responsavel = resp_response.data[0]["responsaveis"]
        
        # Buscar pagamentos relacionados
        pag_response = supabase.table("pagamentos").select("""
            id_pagamento, data_pagamento, valor, forma_pagamento, descricao
        """).eq("id_aluno", id_aluno).eq("tipo_pagamento", "mensalidade").execute()
        
        pagamentos = pag_response.data if pag_response.data else []
        
        return {
            "success": True,
            "dados": {
                "mensalidade": mensalidade,
                "responsavel": responsavel,
                "pagamentos": pagamentos
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def calcular_status_mensalidade(data_vencimento: str, status_atual: str, data_pagamento: str = None) -> Dict:
    """
    Calcula status real da mensalidade baseado na data
    
    Args:
        data_vencimento: Data de vencimento (YYYY-MM-DD)
        status_atual: Status atual no banco
        data_pagamento: Data de pagamento se houver
        
    Returns:
        Dict: {"status": str, "cor": str, "emoji": str}
    """
    try:
        data_hoje = date.today()
        vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
        
        if status_atual in ["Pago", "Pago parcial"]:
            return {
                "status": status_atual,
                "cor": "success",
                "emoji": "✅"
            }
        elif status_atual == "Cancelado":
            return {
                "status": "Cancelado",
                "cor": "secondary", 
                "emoji": "❌"
            }
        elif vencimento < data_hoje:
            dias_atraso = (data_hoje - vencimento).days
            return {
                "status": f"Atrasado ({dias_atraso} dias)",
                "cor": "error",
                "emoji": "⚠️"
            }
        else:
            dias_restantes = (vencimento - data_hoje).days
            return {
                "status": f"A vencer ({dias_restantes} dias)",
                "cor": "warning",
                "emoji": "📅"
            }
            
    except Exception:
        return {
            "status": status_atual,
            "cor": "info",
            "emoji": "❓"
        }

def salvar_alteracoes_mensalidade(id_mensalidade: str, dados_alterados: Dict) -> Dict:
    """
    Salva alterações na mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade
        dados_alterados: Campos alterados
        
    Returns:
        Dict: {"success": bool, "message": str, "error": str}
    """
    try:
        # Adicionar timestamp de atualização
        dados_alterados["updated_at"] = obter_timestamp()
        
        response = supabase.table("mensalidades").update(dados_alterados).eq(
            "id_mensalidade", id_mensalidade
        ).execute()
        
        if response.data:
            # TODO: Registrar no log de auditoria
            # registrar_log_auditoria("mensalidade", id_mensalidade, "update", dados_alterados)
            
            return {
                "success": True,
                "message": "Mensalidade atualizada com sucesso"
            }
        else:
            return {
                "success": False,
                "error": "Erro ao atualizar mensalidade"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def cancelar_mensalidade(id_mensalidade: str, motivo: str) -> Dict:
    """
    Cancela uma mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade
        motivo: Motivo do cancelamento
        
    Returns:
        Dict: {"success": bool, "message": str}
    """
    try:
        dados_cancelamento = {
            "status": "Cancelado",
            "observacoes": f"Cancelada: {motivo}",
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("mensalidades").update(dados_cancelamento).eq(
            "id_mensalidade", id_mensalidade
        ).execute()
        
        if response.data:
            return {
                "success": True,
                "message": "Mensalidade cancelada com sucesso"
            }
        else:
            return {
                "success": False,
                "error": "Erro ao cancelar mensalidade"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def marcar_como_pago(id_mensalidade: str, data_pagamento: str, forma_pagamento: str, observacoes: str = "") -> Dict:
    """
    Marca mensalidade como paga
    
    Args:
        id_mensalidade: ID da mensalidade
        data_pagamento: Data do pagamento
        forma_pagamento: Forma de pagamento
        observacoes: Observações adicionais
        
    Returns:
        Dict: {"success": bool, "message": str}
    """
    try:
        dados_pagamento = {
            "status": "Pago",
            "data_pagamento": data_pagamento,
            "observacoes": observacoes,
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("mensalidades").update(dados_pagamento).eq(
            "id_mensalidade", id_mensalidade
        ).execute()
        
        if response.data:
            # TODO: Criar registro na tabela de pagamentos
            # criar_registro_pagamento(id_mensalidade, data_pagamento, forma_pagamento)
            
            return {
                "success": True,
                "message": "Mensalidade marcada como paga"
            }
        else:
            return {
                "success": False,
                "error": "Erro ao marcar como paga"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🎨 COMPONENTES DA INTERFACE
# ==========================================================

def renderizar_header_modal(dados: Dict):
    """Renderiza o cabeçalho do modal"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    
    st.markdown(f"""
    ## 💰 Mensalidade: {mensalidade['mes_referencia']} – {aluno['nome']}
    
    **ID:** `{mensalidade['id_mensalidade']}` 🎓 **Turma:** {aluno['turmas']['nome_turma']}
    """)

def renderizar_aba_detalhes(dados: Dict):
    """Renderiza a aba de detalhes da mensalidade"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    responsavel = dados.get("responsavel")
    
    # Calcular status atual
    status_info = calcular_status_mensalidade(
        mensalidade["data_vencimento"],
        mensalidade["status"],
        mensalidade.get("data_pagamento")
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👨‍🎓 Informações do Aluno")
        st.info(f"**Nome:** {aluno['nome']}")
        st.info(f"**Turma:** {aluno['turmas']['nome_turma']}")
        st.info(f"**Turno:** {aluno.get('turno', 'Não informado')}")
        st.info(f"**Mensalidade:** {formatar_valor_br(aluno.get('valor_mensalidade', 0))}")
        
        if responsavel:
            st.markdown("### 👤 Responsável Financeiro")
            st.info(f"**Nome:** {responsavel['nome']}")
            st.info(f"**Telefone:** {responsavel.get('telefone', 'Não informado')}")
            st.info(f"**Email:** {responsavel.get('email', 'Não informado')}")
            st.info(f"**CPF:** {responsavel.get('cpf', 'Não informado')}")
    
    with col2:
        st.markdown("### 💰 Detalhes da Mensalidade")
        st.info(f"**Mês de Referência:** {mensalidade['mes_referencia']}")
        st.info(f"**Valor:** {formatar_valor_br(mensalidade['valor'])}")
        st.info(f"**Data de Vencimento:** {formatar_data_br(mensalidade['data_vencimento'])}")
        
        if mensalidade.get('data_pagamento'):
            st.info(f"**Data de Pagamento:** {formatar_data_br(mensalidade['data_pagamento'])}")
        
        # Status com badge colorido
        if status_info["cor"] == "success":
            st.success(f"{status_info['emoji']} **Status:** {status_info['status']}")
        elif status_info["cor"] == "error":
            st.error(f"{status_info['emoji']} **Status:** {status_info['status']}")
        elif status_info["cor"] == "warning":
            st.warning(f"{status_info['emoji']} **Status:** {status_info['status']}")
        else:
            st.info(f"{status_info['emoji']} **Status:** {status_info['status']}")
        
        if mensalidade.get('observacoes'):
            st.markdown("### 📝 Observações")
            st.text_area("", value=mensalidade['observacoes'], disabled=True, height=100)
    
    # Botão para habilitar edição
    if st.button("✏️ Editar Inline", use_container_width=True):
        st.session_state.modal_aba_ativa = "Edição"
        st.rerun()

def renderizar_aba_edicao(dados: Dict):
    """Renderiza a aba de edição da mensalidade"""
    mensalidade = dados["mensalidade"]
    
    st.markdown("### ✏️ Editar Mensalidade")
    st.warning("⚠️ **Atenção:** As alterações serão aplicadas imediatamente após salvar.")
    
    with st.form("form_edicao_mensalidade"):
        col1, col2 = st.columns(2)
        
        with col1:
            novo_valor = st.number_input(
                "💰 Valor (R$):",
                min_value=0.01,
                value=float(mensalidade["valor"]),
                step=0.01,
                format="%.2f"
            )
            
            nova_data_vencimento = st.date_input(
                "📅 Data de Vencimento:",
                value=datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d").date()
            )
        
        with col2:
            novo_status = st.selectbox(
                "📊 Status:",
                options=["A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"],
                index=["A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"].index(
                    mensalidade["status"]
                ) if mensalidade["status"] in ["A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"] else 0
            )
            
            # Data de pagamento só aparece se status for "Pago" ou "Pago parcial"
            nova_data_pagamento = None
            if novo_status in ["Pago", "Pago parcial"]:
                data_atual = None
                if mensalidade.get("data_pagamento"):
                    data_atual = datetime.strptime(mensalidade["data_pagamento"], "%Y-%m-%d").date()
                
                nova_data_pagamento = st.date_input(
                    "📅 Data de Pagamento:",
                    value=data_atual or date.today()
                )
        
        novas_observacoes = st.text_area(
            "📝 Observações:",
            value=mensalidade.get("observacoes", ""),
            height=100
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.form_submit_button("💾 Salvar Alterações", type="primary"):
                # Preparar dados para atualização
                dados_alterados = {
                    "valor": novo_valor,
                    "data_vencimento": nova_data_vencimento.isoformat(),
                    "status": novo_status,
                    "observacoes": novas_observacoes
                }
                
                if nova_data_pagamento:
                    dados_alterados["data_pagamento"] = nova_data_pagamento.isoformat()
                elif novo_status not in ["Pago", "Pago parcial"]:
                    dados_alterados["data_pagamento"] = None
                
                # Salvar alterações
                resultado = salvar_alteracoes_mensalidade(mensalidade["id_mensalidade"], dados_alterados)
                
                if resultado.get("success"):
                    st.success("✅ Mensalidade atualizada com sucesso!")
                    st.session_state.modal_dados_atualizados = True
                    st.session_state.modal_aba_ativa = "Detalhes"
                    st.rerun()
                else:
                    st.error(f"❌ Erro ao salvar: {resultado.get('error')}")
        
        with col_btn2:
            if st.form_submit_button("🔄 Reverter", type="secondary"):
                st.session_state.modal_aba_ativa = "Detalhes"
                st.rerun()

def renderizar_aba_acoes(dados: Dict):
    """Renderiza a aba de ações da mensalidade"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    
    st.markdown("### ⚡ Ações Disponíveis")
    
    # Grid de ações (2 colunas)
    col1, col2 = st.columns(2)
    
    with col1:
        # Cancelar Mensalidade
        if st.button("❌ Cancelar Mensalidade", use_container_width=True, type="secondary"):
            st.session_state.show_cancelar_modal = True
        
        # Marcar como Pago
        if mensalidade["status"] not in ["Pago", "Cancelado"]:
            if st.button("✅ Marcar como Pago", use_container_width=True, type="primary"):
                st.session_state.show_marcar_pago_modal = True
    
    with col2:
        # Emitir Cobrança
        if st.button("📄 Emitir Cobrança", use_container_width=True):
            # TODO: Integrar com sistema de geração de PDF
            st.info("🔧 Funcionalidade em desenvolvimento")
        
        # Gerar Recibo (só se pago)
        if mensalidade["status"] in ["Pago", "Pago parcial"]:
            if st.button("🧾 Gerar Recibo", use_container_width=True):
                # TODO: Integrar com sistema de geração de recibos
                st.info("🔧 Funcionalidade em desenvolvimento")
    
    # Modais secundários para confirmação
    if st.session_state.get('show_cancelar_modal', False):
        with st.container():
            st.markdown("---")
            st.markdown("#### ❌ Confirmar Cancelamento")
            
            motivo_cancelamento = st.text_area(
                "Motivo do cancelamento:",
                placeholder="Digite o motivo do cancelamento..."
            )
            
            col_cancel1, col_cancel2 = st.columns(2)
            
            with col_cancel1:
                if st.button("Confirmar Cancelamento", type="primary"):
                    if motivo_cancelamento:
                        resultado = cancelar_mensalidade(mensalidade["id_mensalidade"], motivo_cancelamento)
                        
                        if resultado.get("success"):
                            st.success("✅ Mensalidade cancelada com sucesso!")
                            st.session_state.show_cancelar_modal = False
                            st.session_state.modal_dados_atualizados = True
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao cancelar: {resultado.get('error')}")
                    else:
                        st.error("Digite o motivo do cancelamento")
            
            with col_cancel2:
                if st.button("Cancelar", type="secondary"):
                    st.session_state.show_cancelar_modal = False
                    st.rerun()
    
    if st.session_state.get('show_marcar_pago_modal', False):
        with st.container():
            st.markdown("---")
            st.markdown("#### ✅ Registrar Pagamento")
            
            with st.form("form_marcar_pago"):
                col_pago1, col_pago2 = st.columns(2)
                
                with col_pago1:
                    data_pagamento = st.date_input(
                        "📅 Data do Pagamento:",
                        value=date.today()
                    )
                    
                    forma_pagamento = st.selectbox(
                        "💳 Forma de Pagamento:",
                        options=["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência"]
                    )
                
                with col_pago2:
                    observacoes_pagamento = st.text_area(
                        "📝 Observações:",
                        placeholder="Observações sobre o pagamento..."
                    )
                
                col_btn_pago1, col_btn_pago2 = st.columns(2)
                
                with col_btn_pago1:
                    if st.form_submit_button("Confirmar Pagamento", type="primary"):
                        resultado = marcar_como_pago(
                            mensalidade["id_mensalidade"],
                            data_pagamento.isoformat(),
                            forma_pagamento,
                            observacoes_pagamento
                        )
                        
                        if resultado.get("success"):
                            st.success("✅ Pagamento registrado com sucesso!")
                            st.session_state.show_marcar_pago_modal = False
                            st.session_state.modal_dados_atualizados = True
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao registrar pagamento: {resultado.get('error')}")
                
                with col_btn_pago2:
                    if st.form_submit_button("Cancelar", type="secondary"):
                        st.session_state.show_marcar_pago_modal = False
                        st.rerun()

def renderizar_aba_historico(dados: Dict):
    """Renderiza a aba de histórico de alterações"""
    mensalidade = dados["mensalidade"]
    
    st.markdown("### 📚 Histórico de Alterações")
    
    # TODO: Implementar sistema de auditoria
    # historico = buscar_historico_alteracoes(mensalidade["id_mensalidade"])
    
    # Dados fictícios para demonstração
    historico_exemplo = [
        {
            "data_hora": "2025-01-07 10:30:00",
            "usuario": "admin",
            "campo": "status",
            "valor_antigo": "A vencer",
            "valor_novo": "Atrasado"
        },
        {
            "data_hora": "2025-01-05 14:20:00", 
            "usuario": "secretaria",
            "campo": "observacoes",
            "valor_antigo": "",
            "valor_novo": "Aguardando pagamento"
        }
    ]
    
    if historico_exemplo:
        # Tabela de histórico
        df_historico = pd.DataFrame(historico_exemplo)
        
        st.dataframe(
            df_historico,
            column_config={
                "data_hora": st.column_config.DatetimeColumn("Data/Hora"),
                "usuario": st.column_config.TextColumn("Usuário"),
                "campo": st.column_config.TextColumn("Campo"),
                "valor_antigo": st.column_config.TextColumn("Valor Anterior"),
                "valor_novo": st.column_config.TextColumn("Valor Atual")
            },
            use_container_width=True,
            height=300
        )
        
        # Campo de busca
        busca_historico = st.text_input("🔍 Buscar no histórico:", placeholder="Digite para filtrar...")
        
        if busca_historico:
            st.info(f"Funcionalidade de busca será implementada para: '{busca_historico}'")
    else:
        st.info("ℹ️ Nenhuma alteração registrada ainda")

def renderizar_aba_relatorios(dados: Dict):
    """Renderiza a aba de relatórios e exportação"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    
    st.markdown("### 📊 Relatórios e Exportação")
    
    col_rel1, col_rel2 = st.columns(2)
    
    with col_rel1:
        st.markdown("#### 📄 Documentos")
        
        # Baixar .docx
        if st.button("📥 Baixar Relatório (.docx)", use_container_width=True):
            # TODO: Integrar com funcoes_relatorios.gerar_relatorio_interface
            try:
                # Configuração para relatório individual
                configuracao = {
                    'tipo': 'mensalidade_individual',
                    'id_mensalidade': mensalidade['id_mensalidade'],
                    'incluir_aluno': True,
                    'incluir_responsavel': True,
                    'incluir_historico': True
                }
                
                # resultado = funcoes_relatorios.gerar_relatorio_interface('mensalidade', configuracao)
                st.info("🔧 Geração de relatório .docx será implementada")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {str(e)}")
        
        # Exportar dados
        if st.button("💾 Exportar Dados (JSON)", use_container_width=True):
            dados_exportacao = {
                "mensalidade": mensalidade,
                "aluno": aluno,
                "timestamp_exportacao": datetime.now().isoformat()
            }
            
            json_str = json.dumps(dados_exportacao, indent=2, default=str, ensure_ascii=False)
            
            st.download_button(
                label="📁 Download JSON",
                data=json_str,
                file_name=f"mensalidade_{mensalidade['id_mensalidade']}_{date.today().isoformat()}.json",
                mime="application/json"
            )
    
    with col_rel2:
        st.markdown("#### 📧 Comunicação")
        
        # Template de email/WhatsApp
        template_texto = st.text_area(
            "✏️ Editar template de cobrança:",
            value=f"""Olá! 

Referente à mensalidade de {mensalidade['mes_referencia']} do(a) aluno(a) {aluno['nome']}.

Valor: {formatar_valor_br(mensalidade['valor'])}
Vencimento: {formatar_data_br(mensalidade['data_vencimento'])}

Atenciosamente,
Secretaria Escolar""",
            height=200
        )
        
        col_btn_com1, col_btn_com2 = st.columns(2)
        
        with col_btn_com1:
            if st.button("📧 Enviar Email", use_container_width=True):
                # TODO: Implementar envio de email
                st.info("🔧 Envio de email será implementado")
        
        with col_btn_com2:
            if st.button("📱 WhatsApp", use_container_width=True):
                # TODO: Implementar integração WhatsApp
                st.info("🔧 Integração WhatsApp será implementada")

# ==========================================================
# 🚀 FUNÇÃO PRINCIPAL DO MODAL
# ==========================================================

def open_modal(id_mensalidade: str):
    """
    Abre o modal de detalhamento da mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade para exibir
    """
    
    # Inicializar estado do modal se necessário
    if 'modal_dados' not in st.session_state:
        st.session_state.modal_dados = None
    if 'modal_aba_ativa' not in st.session_state:
        st.session_state.modal_aba_ativa = "Detalhes"
    if 'modal_dados_atualizados' not in st.session_state:
        st.session_state.modal_dados_atualizados = False
    
    # Carregar dados da mensalidade (só se necessário)
    if (st.session_state.modal_dados is None or 
        st.session_state.modal_dados.get('mensalidade', {}).get('id_mensalidade') != id_mensalidade or
        st.session_state.modal_dados_atualizados):
        
        with st.spinner("Carregando dados da mensalidade..."):
            resultado = buscar_dados_mensalidade(id_mensalidade)
        
        if not resultado.get("success"):
            st.error(f"❌ Erro ao carregar mensalidade: {resultado.get('error')}")
            return
        
        st.session_state.modal_dados = resultado["dados"]
        st.session_state.modal_dados_atualizados = False
    
    dados = st.session_state.modal_dados
    
    # Container principal do modal
    with st.container():
        # Header
        renderizar_header_modal(dados)
        
        # Tabs principais
        tab_detalhes, tab_edicao, tab_acoes, tab_historico, tab_relatorios = st.tabs([
            "📋 Detalhes",
            "✏️ Edição", 
            "⚡ Ações",
            "📚 Histórico",
            "📊 Relatórios"
        ])
        
        # Renderizar aba ativa
        with tab_detalhes:
            if st.session_state.modal_aba_ativa == "Detalhes":
                renderizar_aba_detalhes(dados)
        
        with tab_edicao:
            if st.session_state.modal_aba_ativa == "Edição":
                renderizar_aba_edicao(dados)
        
        with tab_acoes:
            renderizar_aba_acoes(dados)
        
        with tab_historico:
            renderizar_aba_historico(dados)
        
        with tab_relatorios:
            renderizar_aba_relatorios(dados)
        
        # Footer
        st.markdown("---")
        col_footer1, col_footer2 = st.columns([3, 1])
        
        with col_footer1:
            ultima_atualizacao = dados["mensalidade"].get("updated_at", dados["mensalidade"].get("inserted_at", ""))
            if ultima_atualizacao:
                try:
                    dt_atualizacao = datetime.fromisoformat(ultima_atualizacao.replace('Z', '+00:00'))
                    st.caption(f"Última atualização em {dt_atualizacao.strftime('%d/%m/%Y às %H:%M')}")
                except:
                    st.caption("Última atualização: dados não disponíveis")
            else:
                st.caption("Dados de atualização não disponíveis")
        
        with col_footer2:
            if st.button("❌ Fechar", type="secondary", use_container_width=True):
                # Limpar estado do modal
                st.session_state.modal_dados = None
                st.session_state.modal_aba_ativa = "Detalhes"
                st.session_state.modal_dados_atualizados = False
                
                # Limpar modais secundários
                for key in list(st.session_state.keys()):
                    if key.startswith('show_'):
                        del st.session_state[key]
                
                st.rerun()

# ==========================================================
# 📋 EXEMPLO DE USO
# ==========================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Modal Mensalidade - Teste",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("🧪 Teste do Modal de Mensalidade")
    
    # Input para testar
    id_teste = st.text_input("ID da Mensalidade para teste:", value="MENS_123456")
    
    if st.button("🔍 Abrir Modal"):
        open_modal(id_teste) 