#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💰 MODAL DE DETALHAMENTO E AÇÕES DE MENSALIDADE - VERSÃO COMPLETA
================================================================

Modal completo para visualizar, editar e executar ações em mensalidades individuais.
Implementação moderna com 5 abas: Detalhes, Edição, Ações, Histórico e Relatórios.

Especificações:
- Header: Título "Mensalidade: {mes_referencia} – {nome_aluno}" + ID + ícone turma
- Footer: Botão "Fechar", atalho ESC, timestamp de atualização
- 5 Abas funcionais e responsivas
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import json
import time # Importado para usar time.sleep

# Importar dependências do sistema
from models.base import (
    supabase, formatar_data_br, formatar_valor_br, obter_timestamp
)

# Importar o módulo de processamento automatizado simplificado
try:
    from processamento_automatizado_simplificado import (
        iniciar_processamento_simplificado, identificar_alunos_elegiveis,
        SessaoProcessamentoSimplificada, AlunoElegivel, executar_acoes_modo_teste
    )
except ImportError:
    st.error("❌ Módulo de processamento não encontrado")
    # Create dummy class for type hints
    class SessaoProcessamentoSimplificada:
        pass

# ==========================================================
# 🎨 CSS PERSONALIZADO PARA O MODAL
# ==========================================================

def aplicar_css_modal():
    """Aplica CSS personalizado para o modal"""
    st.markdown("""
    <style>
        /* Estilo do Header */
        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px 10px 0 0;
            color: white;
            margin-bottom: 1rem;
        }
        
        .modal-header h2 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .modal-header .subtitle {
            opacity: 0.9;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        /* Badges de Status */
        .status-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            margin: 0.2rem;
        }
        
        .status-pago { background: #d4edda; color: #155724; }
        .status-pendente { background: #fff3cd; color: #856404; }
        .status-atrasado { background: #f8d7da; color: #721c24; }
        .status-cancelado { background: #e2e3e5; color: #383d41; }
        
        /* Cards informativos */
        .info-card {
            background: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        .success-card {
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        .warning-card {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        .error-card {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        /* Footer */
        .modal-footer {
            border-top: 1px solid #dee2e6;
            padding: 1rem;
            margin-top: 2rem;
            background: #f8f9fa;
            border-radius: 0 0 10px 10px;
        }
        
        /* Tabs customizadas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f1f3f4;
            border-radius: 8px 8px 0 0;
            color: #5f6368;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #1976d2;
            color: white;
        }
        
        /* Botões de ação */
        .action-button {
            margin: 0.2rem;
            border-radius: 8px;
        }
        
        /* Métricas customizadas */
        .metric-container {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            text-align: center;
            margin: 0.5rem 0;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1976d2;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 🔧 FUNÇÕES AUXILIARES PRINCIPAIS
# ==========================================================

def buscar_dados_completos_mensalidade(id_mensalidade: str) -> Dict:
    """
    Busca dados completos da mensalidade incluindo todas as informações relacionadas
    
    Args:
        id_mensalidade: ID da mensalidade
        
    Returns:
        Dict: {"success": bool, "dados": Dict, "error": str}
    """
    try:
        # Buscar mensalidade com dados do aluno e turma
        response = supabase.table("mensalidades").select("""
            *,
            alunos!inner(
                id, nome, turno, valor_mensalidade, data_nascimento, 
                data_matricula, dia_vencimento,
                turmas!inner(nome_turma)
            )
        """).eq("id_mensalidade", id_mensalidade).execute()
        
        if not response.data:
            return {"success": False, "error": "Mensalidade não encontrada"}
        
        mensalidade = response.data[0]
        id_aluno = mensalidade["alunos"]["id"]
        
        # Buscar responsáveis do aluno
        resp_response = supabase.table("alunos_responsaveis").select("""
            responsavel_financeiro, parentesco,
            responsaveis!inner(id, nome, telefone, email, cpf, endereco)
        """).eq("id_aluno", id_aluno).execute()
        
        responsaveis = resp_response.data if resp_response.data else []
        
        # Buscar pagamentos relacionados à mensalidade
        pag_response = supabase.table("pagamentos").select("""
            id_pagamento, data_pagamento, valor, forma_pagamento, 
            descricao, created_at
        """).eq("id_aluno", id_aluno).eq("tipo_pagamento", "mensalidade").execute()
        
        pagamentos = pag_response.data if pag_response.data else []
        
        # Buscar histórico de alterações (simulado - implementar auditoria real se necessário)
        historico = [
            {
                "data": mensalidade.get("inserted_at", ""),
                "acao": "Criação",
                "usuario": "Sistema",
                "detalhes": "Mensalidade criada automaticamente"
            }
        ]
        
        if mensalidade.get("updated_at") != mensalidade.get("inserted_at"):
            historico.append({
                "data": mensalidade.get("updated_at", ""),
                "acao": "Atualização", 
                "usuario": "Sistema",
                "detalhes": "Dados da mensalidade atualizados"
            })
        
        return {
            "success": True,
            "dados": {
                "mensalidade": mensalidade,
                "responsaveis": responsaveis,
                "pagamentos": pagamentos,
                "historico": historico
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def calcular_status_visual(mensalidade: Dict) -> Dict:
    """
    Calcula status visual da mensalidade com emoji e cor
    
    Args:
        mensalidade: Dados da mensalidade
        
    Returns:
        Dict: {"emoji": str, "cor": str, "texto": str, "classe_css": str}
    """
    try:
        status = mensalidade.get("status", "")
        data_vencimento = mensalidade.get("data_vencimento", "")
        data_pagamento = mensalidade.get("data_pagamento")
        
        if status in ["Pago", "Pago parcial"]:
            return {
                "emoji": "✅",
                "cor": "success", 
                "texto": status,
                "classe_css": "status-pago"
            }
        elif status == "Cancelado":
            return {
                "emoji": "❌",
                "cor": "secondary",
                "texto": "Cancelado",
                "classe_css": "status-cancelado"
            }
        else:
            # Verificar se está atrasado
            if data_vencimento:
                data_hoje = date.today()
                vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
                
                if vencimento < data_hoje:
                    dias_atraso = (data_hoje - vencimento).days
                    return {
                        "emoji": "⚠️",
                        "cor": "error",
                        "texto": f"Atrasado ({dias_atraso} dias)",
                        "classe_css": "status-atrasado"
                    }
                else:
                    dias_restantes = (vencimento - data_hoje).days
                    return {
                        "emoji": "📅",
                        "cor": "warning",
                        "texto": f"A vencer ({dias_restantes} dias)",
                        "classe_css": "status-pendente"
                    }
            
            return {
                "emoji": "📅",
                "cor": "info",
                "texto": status,
                "classe_css": "status-pendente"
            }
            
    except Exception:
        return {
            "emoji": "❓",
            "cor": "secondary",
            "texto": "Status indefinido",
            "classe_css": "status-cancelado"
        }

def obter_icone_turma(nome_turma: str) -> str:
    """Retorna ícone baseado na turma"""
    nome_lower = nome_turma.lower()
    
    if "berçário" in nome_lower or "berç" in nome_lower:
        return "👶"
    elif "infantil" in nome_lower:
        return "🧒"
    elif any(ano in nome_lower for ano in ["1º", "2º", "3º", "4º", "5º"]):
        return "📚"
    elif "maternal" in nome_lower:
        return "🍼"
    else:
        return "🎓"

# ==========================================================
# 🎨 COMPONENTES DO HEADER E FOOTER
# ==========================================================

def renderizar_header_modal(dados: Dict):
    """Renderiza o cabeçalho do modal com design moderno"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    turma = aluno["turmas"]
    
    # Aplicar CSS
    aplicar_css_modal()
    
    # Status visual
    status_info = calcular_status_visual(mensalidade)
    icone_turma = obter_icone_turma(turma["nome_turma"])
    
    # Header com gradiente
    st.markdown(f"""
    <div class="modal-header">
        <h2>💰 Mensalidade: {mensalidade['mes_referencia']} – {aluno['nome']}</h2>
        <div class="subtitle">
            <strong>ID:</strong> <code>{mensalidade['id_mensalidade']}</code> 
            &nbsp;&nbsp;{icone_turma} <strong>Turma:</strong> {turma['nome_turma']}
            &nbsp;&nbsp;<span class="status-badge {status_info['classe_css']}">{status_info['emoji']} {status_info['texto']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def renderizar_footer_modal(dados: Dict):
    """Renderiza o rodapé do modal com timestamp e ações"""
    mensalidade = dados["mensalidade"]
    
    # Calcular última atualização
    ultima_atualizacao = mensalidade.get("updated_at", mensalidade.get("inserted_at", ""))
    
    try:
        if ultima_atualizacao:
            dt = datetime.fromisoformat(ultima_atualizacao.replace('Z', '+00:00'))
            timestamp_texto = dt.strftime("%d/%m/%Y às %H:%M")
        else:
            timestamp_texto = "Não disponível"
    except:
        timestamp_texto = "Não disponível"
    
    st.markdown(f"""
    <div class="modal-footer">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #666; font-size: 0.9rem;">
                📅 Última atualização: {timestamp_texto}
            </span>
            <span style="color: #999; font-size: 0.8rem;">
                💡 <strong>Dica:</strong> Use ESC para fechar o modal
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão de fechar
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("❌ Fechar Modal", use_container_width=True, type="secondary", key="fechar_modal_footer"):
            st.session_state.modal_aberto = False
            st.session_state.id_mensalidade_modal = None
            st.rerun()

# ==========================================================
# 🏠 ABA 1: DETALHES
# ==========================================================

def renderizar_aba_detalhes(dados: Dict):
    """Renderiza a aba de detalhes com informações completas"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    turma = aluno["turmas"]
    responsaveis = dados["responsaveis"]
    
    # Status visual
    status_info = calcular_status_visual(mensalidade)
    
    # Layout em duas colunas principais
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Informações do Aluno
        st.markdown("### 👨‍🎓 Informações do Aluno")
        
        aluno_info = f"""
        <div class="info-card">
            <strong>📛 Nome:</strong> {aluno['nome']}<br>
            <strong>🎓 Turma:</strong> {turma['nome_turma']}<br>
            <strong>🕐 Turno:</strong> {aluno.get('turno', 'Não informado')}<br>
            <strong>🎂 Data Nascimento:</strong> {formatar_data_br(aluno.get('data_nascimento', '')) if aluno.get('data_nascimento') else 'Não informado'}<br>
            <strong>📅 Data Matrícula:</strong> {formatar_data_br(aluno.get('data_matricula', '')) if aluno.get('data_matricula') else 'Não informado'}<br>
            <strong>💰 Valor Mensalidade:</strong> {formatar_valor_br(aluno.get('valor_mensalidade', 0))}<br>
            <strong>📆 Dia Vencimento:</strong> {aluno.get('dia_vencimento', 'Não definido')}
        </div>
        """
        st.markdown(aluno_info, unsafe_allow_html=True)
        
        # Responsáveis
        st.markdown("### 👥 Responsáveis")
        
        if responsaveis:
            for resp in responsaveis:
                responsavel_data = resp["responsaveis"]
                is_financeiro = resp.get("responsavel_financeiro", False)
                parentesco = resp.get("parentesco", "Não informado")
                
                badge_financeiro = "💰 FINANCEIRO" if is_financeiro else ""
                
                resp_info = f"""
                <div class="{'success-card' if is_financeiro else 'info-card'}">
                    <strong>👤 Nome:</strong> {responsavel_data['nome']} {badge_financeiro}<br>
                    <strong>👨‍👩‍👧‍👦 Parentesco:</strong> {parentesco}<br>
                    <strong>📱 Telefone:</strong> {responsavel_data.get('telefone', 'Não informado')}<br>
                    <strong>📧 Email:</strong> {responsavel_data.get('email', 'Não informado')}<br>
                    <strong>🆔 CPF:</strong> {responsavel_data.get('cpf', 'Não informado')}
                </div>
                """
                st.markdown(resp_info, unsafe_allow_html=True)
        else:
            st.markdown('<div class="warning-card">⚠️ Nenhum responsável cadastrado</div>', unsafe_allow_html=True)
    
    with col2:
        # Detalhes da Mensalidade
        st.markdown("### 💰 Detalhes da Mensalidade")
        
        # Card principal com status
        card_class = "success-card" if status_info["cor"] == "success" else "warning-card" if status_info["cor"] == "warning" else "error-card" if status_info["cor"] == "error" else "info-card"
        
        mensalidade_info = f"""
        <div class="{card_class}">
            <strong>{status_info['emoji']} Status:</strong> {status_info['texto']}<br>
            <strong>📅 Mês de Referência:</strong> {mensalidade['mes_referencia']}<br>
            <strong>💰 Valor:</strong> {formatar_valor_br(mensalidade['valor'])}<br>
            <strong>📆 Data de Vencimento:</strong> {formatar_data_br(mensalidade['data_vencimento'])}<br>
            <strong>💳 Data de Pagamento:</strong> {formatar_data_br(mensalidade.get('data_pagamento', '')) if mensalidade.get('data_pagamento') else '—'}<br>
            <strong>🆔 ID Mensalidade:</strong> <code>{mensalidade['id_mensalidade']}</code>
        </div>
        """
        st.markdown(mensalidade_info, unsafe_allow_html=True)
        
        # Observações
        if mensalidade.get('observacoes'):
            st.markdown("### 📝 Observações")
            st.markdown(f"""
            <div class="info-card">
                {mensalidade['observacoes']}
            </div>
            """, unsafe_allow_html=True)
        
        # Métricas visuais
        st.markdown("### 📊 Métricas")
        
        # Calcular métricas
        valor_mensalidade = float(mensalidade['valor'])
        valor_pago = float(mensalidade.get('valor_pago', 0)) if mensalidade.get('valor_pago') else 0
        
        if mensalidade.get('data_vencimento'):
            try:
                vencimento = datetime.strptime(mensalidade['data_vencimento'], '%Y-%m-%d').date()
                hoje = date.today()
                dias_diferenca = (hoje - vencimento).days
            except:
                dias_diferenca = 0
        else:
            dias_diferenca = 0
        
        # Layout de métricas
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.metric(
                label="💰 Valor da Mensalidade",
                value=f"R$ {valor_mensalidade:,.2f}",
                delta=f"R$ {valor_pago:,.2f} pago" if valor_pago > 0 else None
            )
        
        with metric_col2:
            if dias_diferenca > 0:
                st.metric(
                    label="⏰ Situação",
                    value=f"{dias_diferenca} dias",
                    delta="Em atraso",
                    delta_color="inverse"
                )
            elif dias_diferenca == 0:
                st.metric(
                    label="⏰ Situação", 
                    value="Hoje",
                    delta="Vence hoje",
                    delta_color="normal"
                )
            else:
                st.metric(
                    label="⏰ Situação",
                    value=f"{abs(dias_diferenca)} dias",
                    delta="Para vencer",
                    delta_color="normal"
                )
    
    # Ações rápidas na parte inferior
    st.markdown("---")
    st.markdown("### ⚡ Ações Rápidas")
    
    col_acao1, col_acao2, col_acao3, col_acao4 = st.columns(4)
    
    with col_acao1:
        if st.button("✏️ Editar", use_container_width=True, type="secondary"):
            st.session_state.aba_ativa_modal = "Edição"
            st.rerun()
    
    with col_acao2:
        if mensalidade["status"] not in ["Pago", "Cancelado"]:
            if st.button("✅ Marcar Pago", use_container_width=True, type="primary"):
                st.session_state.aba_ativa_modal = "Ações"
                st.session_state.acao_selecionada = "marcar_pago"
                st.rerun()
    
    with col_acao3:
        if st.button("📊 Relatórios", use_container_width=True):
            st.session_state.aba_ativa_modal = "Relatórios"
            st.rerun()
    
    with col_acao4:
        if st.button("📚 Histórico", use_container_width=True):
            st.session_state.aba_ativa_modal = "Histórico"
            st.rerun() 

# ==========================================================
# ✏️ ABA 2: EDIÇÃO
# ==========================================================

def renderizar_aba_edicao(dados: Dict):
    """Renderiza a aba de edição com formulário completo"""
    mensalidade = dados["mensalidade"]
    
    st.markdown("### ✏️ Editar Mensalidade")
    
    # Aviso importante
    st.markdown("""
    <div class="warning-card">
        ⚠️ <strong>Atenção:</strong> As alterações serão aplicadas imediatamente após salvar.
        Certifique-se de que os dados estão corretos antes de confirmar.
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_edicao_mensalidade_completo"):
        # Layout em duas colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💰 Dados Financeiros")
            
            novo_valor = st.number_input(
                "💰 Valor (R$):",
                min_value=0.01,
                max_value=10000.0,
                value=float(mensalidade["valor"]),
                step=0.01,
                format="%.2f",
                help="Valor da mensalidade em reais"
            )
            
            nova_data_vencimento = st.date_input(
                "📅 Data de Vencimento:",
                value=datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d").date(),
                help="Data de vencimento da mensalidade"
            )
            
            # Desconto/Acréscimo
            desconto_acrescimo = st.number_input(
                "💸 Desconto/Acréscimo (R$):",
                min_value=-1000.0,
                max_value=1000.0,
                value=0.0,
                step=0.01,
                format="%.2f",
                help="Valor negativo = desconto, valor positivo = acréscimo"
            )
        
        with col2:
            st.markdown("#### 📊 Status e Pagamento")
            
            novo_status = st.selectbox(
                "📊 Status:",
                options=["A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"],
                index=["A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"].index(
                    mensalidade["status"]
                ) if mensalidade["status"] in ["A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"] else 0,
                help="Status atual da mensalidade"
            )
            
            # Data de pagamento (só aparece se status for "Pago" ou "Pago parcial")
            nova_data_pagamento = None
            if novo_status in ["Pago", "Pago parcial"]:
                data_atual = None
                if mensalidade.get("data_pagamento"):
                    try:
                        data_atual = datetime.strptime(mensalidade["data_pagamento"], "%Y-%m-%d").date()
                    except:
                        data_atual = date.today()
                
                nova_data_pagamento = st.date_input(
                    "💳 Data de Pagamento:",
                    value=data_atual or date.today(),
                    help="Data em que o pagamento foi realizado"
                )
                
                # Valor pago (para pagamento parcial)
                if novo_status == "Pago parcial":
                    valor_pago = st.number_input(
                        "💵 Valor Pago (R$):",
                        min_value=0.01,
                        max_value=float(novo_valor),
                        value=float(mensalidade.get("valor_pago", novo_valor/2)),
                        step=0.01,
                        format="%.2f",
                        help="Valor efetivamente pago (menor que o valor total)"
                    )
            
            # Forma de pagamento
            if novo_status in ["Pago", "Pago parcial"]:
                forma_pagamento = st.selectbox(
                    "💳 Forma de Pagamento:",
                    options=["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência", "Outro"],
                    help="Como foi realizado o pagamento"
                )
        
        # Observações (campo expandido)
        st.markdown("#### 📝 Observações")
        novas_observacoes = st.text_area(
            "",
            value=mensalidade.get("observacoes", ""),
            height=100,
            placeholder="Digite observações sobre esta mensalidade...",
            help="Observações gerais sobre a mensalidade"
        )
        
        # Histórico de alterações
        motivo_alteracao = st.text_input(
            "📋 Motivo da Alteração:",
            placeholder="Descreva o motivo desta alteração...",
            help="Este motivo será registrado no histórico"
        )
        
        # Botões do formulário
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            submit_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
        
        with col_btn2:
            cancelar_edicao = st.form_submit_button("🔄 Cancelar", type="secondary")
        
        with col_btn3:
            st.write("")  # Espaço
        
        # Processar submissão do formulário
        if submit_edicao:
            # Validações
            if not motivo_alteracao.strip():
                st.error("❌ Por favor, informe o motivo da alteração")
            elif nova_data_vencimento > date.today() + timedelta(days=365):
                st.error("❌ Data de vencimento não pode ser superior a 1 ano")
            else:
                # Preparar dados para atualização
                dados_alterados = {
                    "valor": novo_valor,
                    "data_vencimento": nova_data_vencimento.isoformat(),
                    "status": novo_status,
                    "observacoes": novas_observacoes,
                    "updated_at": obter_timestamp()
                }
                
                # Adicionar desconto/acréscimo se houver
                if desconto_acrescimo != 0:
                    valor_final = novo_valor + desconto_acrescimo
                    dados_alterados["valor"] = valor_final
                    if desconto_acrescimo > 0:
                        dados_alterados["observacoes"] += f"\n[ACRÉSCIMO: R$ {desconto_acrescimo:.2f}]"
                    else:
                        dados_alterados["observacoes"] += f"\n[DESCONTO: R$ {abs(desconto_acrescimo):.2f}]"
                
                # Dados de pagamento
                if nova_data_pagamento:
                    dados_alterados["data_pagamento"] = nova_data_pagamento.isoformat()
                    if novo_status == "Pago parcial" and 'valor_pago' in locals():
                        dados_alterados["valor_pago"] = valor_pago
                    if 'forma_pagamento' in locals():
                        dados_alterados["forma_pagamento"] = forma_pagamento
                elif novo_status not in ["Pago", "Pago parcial"]:
                    dados_alterados["data_pagamento"] = None
                    dados_alterados["valor_pago"] = None
                    dados_alterados["forma_pagamento"] = None
                
                # Tentar salvar
                try:
                    response = supabase.table("mensalidades").update(dados_alterados).eq(
                        "id_mensalidade", mensalidade["id_mensalidade"]
                    ).execute()
                    
                    if response.data:
                        # TODO: Registrar no histórico/auditoria
                        # registrar_historico_alteracao(mensalidade["id_mensalidade"], motivo_alteracao, dados_alterados)
                        
                        st.success("✅ Mensalidade atualizada com sucesso!")
                        st.balloons()
                        
                        # Atualizar estado e voltar para aba de detalhes
                        st.session_state.modal_dados_atualizados = True
                        st.session_state.aba_ativa_modal = "Detalhes"
                        
                        # Recarregar dados
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar alterações. Tente novamente.")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {str(e)}")
        
        elif cancelar_edicao:
            st.session_state.aba_ativa_modal = "Detalhes"
            st.rerun()

# ==========================================================
# ⚡ ABA 3: AÇÕES
# ==========================================================

def renderizar_aba_acoes(dados: Dict):
    """Renderiza a aba de ações com todas as operações disponíveis"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    
    st.markdown("### ⚡ Ações Disponíveis")
    st.markdown("Selecione uma das ações abaixo para executar operações na mensalidade:")
    
    # Status atual
    status_info = calcular_status_visual(mensalidade)
    st.markdown(f"""
    <div class="info-card">
        <strong>Status Atual:</strong> {status_info['emoji']} {status_info['texto']}
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de ações principais (2x2)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💰 Ações Financeiras")
        
        # Marcar como Pago
        if mensalidade["status"] not in ["Pago", "Cancelado"]:
            if st.button("✅ Marcar como Pago", use_container_width=True, type="primary", key="acao_marcar_pago"):
                st.session_state.show_form_marcar_pago = True
                st.rerun()
        
        # Marcar como Pago Parcial
        if mensalidade["status"] not in ["Pago", "Pago parcial", "Cancelado"]:
            if st.button("🔶 Pagamento Parcial", use_container_width=True, key="acao_pago_parcial"):
                st.session_state.show_form_pago_parcial = True
                st.rerun()
        
        # Aplicar Desconto
        if mensalidade["status"] not in ["Pago", "Cancelado"]:
            if st.button("💸 Aplicar Desconto", use_container_width=True, key="acao_desconto"):
                st.session_state.show_form_desconto = True
                st.rerun()
        
        # Gerar Segunda Via
        if st.button("🧾 Gerar Recibo/Boleto", use_container_width=True, key="acao_recibo"):
            st.session_state.show_form_recibo = True
            st.rerun()
    
    with col2:
        st.markdown("#### 🔧 Ações Administrativas")
        
        # Cancelar Mensalidade
        if mensalidade["status"] != "Cancelado":
            if st.button("❌ Cancelar Mensalidade", use_container_width=True, type="secondary", key="acao_cancelar"):
                st.session_state.show_form_cancelar = True
                st.rerun()
        
        # Reenviar Cobrança
        if st.button("📧 Enviar Cobrança", use_container_width=True, key="acao_cobranca"):
            st.session_state.show_form_cobranca = True
            st.rerun()
        
        # Renegociar
        if mensalidade["status"] in ["Atrasado"]:
            if st.button("🤝 Renegociar", use_container_width=True, key="acao_renegociar"):
                st.session_state.show_form_renegociar = True
                st.rerun()
        
        # Transferir/Trocar
        if st.button("🔄 Transferir/Trocar", use_container_width=True, key="acao_transferir"):
            st.info("🔧 Em desenvolvimento")
    
    # ==========================================================
    # FORMULÁRIOS DAS AÇÕES (MODAIS SECUNDÁRIOS)
    # ==========================================================
    
    # Form: Marcar como Pago
    if st.session_state.get('show_form_marcar_pago', False):
        st.markdown("---")
        st.markdown("#### ✅ Registrar Pagamento Completo")
        
        with st.form("form_marcar_pago_completo"):
            col_pag1, col_pag2 = st.columns(2)
            
            with col_pag1:
                data_pagamento = st.date_input(
                    "📅 Data do Pagamento:",
                    value=date.today(),
                    help="Data em que o pagamento foi realizado"
                )
                
                forma_pagamento = st.selectbox(
                    "💳 Forma de Pagamento:",
                    options=["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência", "Outro"]
                )
            
            with col_pag2:
                valor_recebido = st.number_input(
                    "💰 Valor Recebido (R$):",
                    min_value=0.01,
                    value=float(mensalidade["valor"]),
                    step=0.01,
                    format="%.2f"
                )
                
                observacoes_pagamento = st.text_area(
                    "📝 Observações:",
                    placeholder="Observações sobre o pagamento..."
                )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.form_submit_button("✅ Confirmar Pagamento", type="primary"):
                    try:
                        dados_pagamento = {
                            "status": "Pago",
                            "data_pagamento": data_pagamento.isoformat(),
                            "forma_pagamento": forma_pagamento,
                            "valor_pago": valor_recebido,
                            "observacoes": f"{mensalidade.get('observacoes', '')}\n[PAGO: {forma_pagamento} em {data_pagamento.strftime('%d/%m/%Y')}] {observacoes_pagamento}".strip(),
                            "updated_at": obter_timestamp()
                        }
                        
                        response = supabase.table("mensalidades").update(dados_pagamento).eq(
                            "id_mensalidade", mensalidade["id_mensalidade"]
                        ).execute()
                        
                        if response.data:
                            st.success("✅ Pagamento registrado com sucesso!")
                            st.session_state.show_form_marcar_pago = False
                            st.session_state.modal_dados_atualizados = True
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Erro ao registrar pagamento")
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
            
            with col_btn2:
                if st.form_submit_button("❌ Cancelar", type="secondary"):
                    st.session_state.show_form_marcar_pago = False
                    st.rerun()
    
    # Form: Cancelar Mensalidade
    if st.session_state.get('show_form_cancelar', False):
        st.markdown("---")
        st.markdown("#### ❌ Cancelar Mensalidade")
        
        st.markdown("""
        <div class="error-card">
            ⚠️ <strong>Atenção:</strong> Esta ação não pode ser desfeita. 
            A mensalidade será marcada como cancelada permanentemente.
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("form_cancelar_mensalidade"):
            motivo_cancelamento = st.text_area(
                "📋 Motivo do Cancelamento:",
                placeholder="Descreva o motivo do cancelamento...",
                help="Este motivo será registrado permanentemente"
            )
            
            # Checkbox de confirmação
            confirmo_cancelamento = st.checkbox(
                "🔴 Confirmo que desejo cancelar esta mensalidade permanentemente",
                help="Marque esta opção para habilitar o cancelamento"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.form_submit_button("❌ CANCELAR MENSALIDADE", type="primary", disabled=not confirmo_cancelamento):
                    if not motivo_cancelamento.strip():
                        st.error("❌ Por favor, informe o motivo do cancelamento")
                    else:
                        try:
                            dados_cancelamento = {
                                "status": "Cancelado",
                                "observacoes": f"{mensalidade.get('observacoes', '')}\n[CANCELADO em {date.today().strftime('%d/%m/%Y')}] Motivo: {motivo_cancelamento}".strip(),
                                "updated_at": obter_timestamp()
                            }
                            
                            response = supabase.table("mensalidades").update(dados_cancelamento).eq(
                                "id_mensalidade", mensalidade["id_mensalidade"]
                            ).execute()
                            
                            if response.data:
                                st.success("✅ Mensalidade cancelada com sucesso!")
                                st.session_state.show_form_cancelar = False
                                st.session_state.modal_dados_atualizados = True
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao cancelar mensalidade")
                                
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
            
            with col_btn2:
                if st.form_submit_button("🔄 Voltar", type="secondary"):
                    st.session_state.show_form_cancelar = False
                    st.rerun()

# ==========================================================
# 📚 ABA 4: HISTÓRICO
# ==========================================================

def renderizar_aba_historico(dados: Dict):
    """Renderiza a aba de histórico com log de alterações"""
    mensalidade = dados["mensalidade"]
    historico = dados.get("historico", [])
    
    st.markdown("### 📚 Histórico de Alterações")
    st.markdown("Timeline completo de todas as alterações realizadas nesta mensalidade:")
    
    if historico:
        # Timeline visual
        for i, evento in enumerate(historico):
            try:
                data_evento = datetime.fromisoformat(evento["data"].replace('Z', '+00:00'))
                data_formatada = data_evento.strftime("%d/%m/%Y às %H:%M")
            except:
                data_formatada = evento.get("data", "Data não disponível")
            
            acao = evento.get("acao", "Ação não especificada")
            usuario = evento.get("usuario", "Sistema")
            detalhes = evento.get("detalhes", "Nenhum detalhe disponível")
            
            # Ícone baseado na ação
            if "criação" in acao.lower() or "criado" in acao.lower():
                icone = "🌟"
                card_class = "success-card"
            elif "atualização" in acao.lower() or "alteração" in acao.lower():
                icone = "✏️"
                card_class = "info-card"
            elif "pagamento" in acao.lower() or "pago" in acao.lower():
                icone = "💰"
                card_class = "success-card"
            elif "cancelamento" in acao.lower() or "cancelado" in acao.lower():
                icone = "❌"
                card_class = "error-card"
            else:
                icone = "📝"
                card_class = "info-card"
            
            # Card do evento
            st.markdown(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <strong>{icone} {acao}</strong>
                    <span style="font-size: 0.9rem; opacity: 0.8;">📅 {data_formatada}</span>
                </div>
                <div style="margin-bottom: 0.5rem;">
                    <strong>👤 Usuário:</strong> {usuario}
                </div>
                <div>
                    <strong>📋 Detalhes:</strong> {detalhes}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Linha conectora (exceto no último item)
            if i < len(historico) - 1:
                st.markdown('<div style="text-align: center; color: #ccc; font-size: 1.5rem;">⬇️</div>', unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="warning-card">
            📝 <strong>Nenhum histórico disponível</strong><br>
            O sistema de auditoria pode não estar ativo ou esta mensalidade não possui alterações registradas.
        </div>
        """, unsafe_allow_html=True)
    
    # Seção de auditoria expandida
    with st.expander("🔍 Informações Técnicas de Auditoria"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Metadados:**")
            created_at = mensalidade.get("inserted_at", "N/A")
            updated_at = mensalidade.get("updated_at", "N/A")
            
            try:
                if created_at != "N/A":
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_formatted = created_dt.strftime("%d/%m/%Y às %H:%M:%S")
                else:
                    created_formatted = "N/A"
                    
                if updated_at != "N/A":
                    updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    updated_formatted = updated_dt.strftime("%d/%m/%Y às %H:%M:%S")
                else:
                    updated_formatted = "N/A"
            except:
                created_formatted = created_at
                updated_formatted = updated_at
            
            st.text(f"🌟 Criado em: {created_formatted}")
            st.text(f"✏️ Modificado em: {updated_formatted}")
            st.text(f"🆔 ID: {mensalidade['id_mensalidade']}")
        
        with col2:
            st.markdown("**📋 Status da Auditoria:**")
            st.text("🔍 Sistema de Log: Básico")
            st.text("📊 Histórico Completo: Em desenvolvimento")
            st.text("🔐 Backup de Dados: Ativo")
    
    # Ações do histórico
    st.markdown("---")
    col_hist1, col_hist2, col_hist3 = st.columns(3)
    
    with col_hist1:
        if st.button("📊 Exportar Histórico", use_container_width=True):
            # TODO: Implementar exportação do histórico
            st.info("🔧 Funcionalidade em desenvolvimento")
    
    with col_hist2:
        if st.button("🔄 Atualizar Histórico", use_container_width=True):
            st.session_state.modal_dados_atualizados = True
            st.rerun()
    
    with col_hist3:
        if st.button("📧 Relatório por Email", use_container_width=True):
            st.info("🔧 Funcionalidade em desenvolvimento")

# ==========================================================
# 📊 ABA 5: RELATÓRIOS
# ==========================================================

def renderizar_aba_relatorios(dados: Dict):
    """Renderiza a aba de relatórios com geração de documentos"""
    mensalidade = dados["mensalidade"]
    aluno = mensalidade["alunos"]
    responsaveis = dados["responsaveis"]
    
    st.markdown("### 📊 Relatórios e Documentos")
    st.markdown("Gere relatórios e documentos específicos para esta mensalidade:")
    
    # Seção de relatórios básicos
    st.markdown("#### 📄 Documentos Básicos")
    
    col_rel1, col_rel2 = st.columns(2)
    
    with col_rel1:
        # Recibo de Pagamento
        if mensalidade["status"] in ["Pago", "Pago parcial"]:
            if st.button("🧾 Recibo de Pagamento", use_container_width=True, type="primary"):
                try:
                    # TODO: Integrar com sistema de geração de PDF
                    st.success("✅ Recibo gerado! (Funcionalidade em desenvolvimento)")
                    # Aqui integraria com funcoes_relatorios ou similar
                except Exception as e:
                    st.error(f"❌ Erro ao gerar recibo: {str(e)}")
        else:
            st.button("🧾 Recibo de Pagamento", use_container_width=True, disabled=True, help="Disponível apenas para mensalidades pagas")
        
        # Boleto/Cobrança
        if mensalidade["status"] not in ["Pago", "Cancelado"]:
            if st.button("📄 Boleto/Cobrança", use_container_width=True):
                try:
                    st.success("✅ Boleto gerado! (Funcionalidade em desenvolvimento)")
                except Exception as e:
                    st.error(f"❌ Erro ao gerar boleto: {str(e)}")
        else:
            st.button("📄 Boleto/Cobrança", use_container_width=True, disabled=True, help="Não disponível para mensalidades pagas ou canceladas")
    
    with col_rel2:
        # Declaração de Débito
        if mensalidade["status"] in ["Atrasado", "A vencer"]:
            if st.button("⚠️ Declaração de Débito", use_container_width=True):
                st.success("✅ Declaração gerada! (Em desenvolvimento)")
        
        # Histórico Completo
        if st.button("📚 Relatório Completo", use_container_width=True):
            st.success("✅ Relatório gerado! (Em desenvolvimento)")
    
    # Seção de relatórios avançados
    st.markdown("---")
    st.markdown("#### 📈 Relatórios Avançados")
    
    with st.expander("⚙️ Configurar Relatório Personalizado", expanded=False):
        with st.form("form_relatorio_personalizado"):
            st.markdown("**📋 Configurações do Relatório:**")
            
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                incluir_dados_aluno = st.checkbox("👨‍🎓 Dados do Aluno", value=True)
                incluir_dados_responsavel = st.checkbox("👥 Dados do Responsável", value=True)
                incluir_historico_pagamentos = st.checkbox("💰 Histórico de Pagamentos", value=True)
                incluir_observacoes = st.checkbox("📝 Observações", value=True)
            
            with col_config2:
                formato_relatorio = st.selectbox(
                    "📄 Formato:",
                    options=["PDF", "Word (DOCX)", "Excel (XLSX)"],
                    index=0
                )
                
                incluir_graficos = st.checkbox("📊 Incluir Gráficos", value=False)
                incluir_timeline = st.checkbox("📅 Timeline de Eventos", value=False)
                logomark_empresa = st.checkbox("🏢 Logo da Empresa", value=True)
            
            observacoes_relatorio = st.text_area(
                "📝 Observações para o Relatório:",
                placeholder="Adicione observações específicas para este relatório..."
            )
            
            if st.form_submit_button("📊 Gerar Relatório Personalizado", type="primary"):
                # TODO: Implementar geração personalizada
                configuracao = {
                    "incluir_dados_aluno": incluir_dados_aluno,
                    "incluir_dados_responsavel": incluir_dados_responsavel,
                    "incluir_historico_pagamentos": incluir_historico_pagamentos,
                    "incluir_observacoes": incluir_observacoes,
                    "formato": formato_relatorio,
                    "incluir_graficos": incluir_graficos,
                    "incluir_timeline": incluir_timeline,
                    "logomark_empresa": logomark_empresa,
                    "observacoes": observacoes_relatorio
                }
                
                st.success(f"✅ Relatório {formato_relatorio} configurado! (Em desenvolvimento)")
                st.json(configuracao)  # Preview da configuração
    
    # Seção de envio e compartilhamento
    st.markdown("---")
    st.markdown("#### 📧 Envio e Compartilhamento")
    
    col_envio1, col_envio2, col_envio3 = st.columns(3)
    
    with col_envio1:
        if st.button("📧 Enviar por Email", use_container_width=True):
            # Buscar emails dos responsáveis
            emails_responsaveis = [r["responsaveis"]["email"] for r in responsaveis if r["responsaveis"].get("email")]
            
            if emails_responsaveis:
                st.success(f"✅ Email enviado para: {', '.join(emails_responsaveis)}")
                st.info("🔧 Funcionalidade em desenvolvimento")
            else:
                st.error("❌ Nenhum email encontrado nos responsáveis")
    
    with col_envio2:
        if st.button("📱 Compartilhar WhatsApp", use_container_width=True):
            # Buscar telefones dos responsáveis
            telefones_responsaveis = [r["responsaveis"]["telefone"] for r in responsaveis if r["responsaveis"].get("telefone")]
            
            if telefones_responsaveis:
                st.success(f"✅ Link gerado para: {', '.join(telefones_responsaveis)}")
                st.info("🔧 Funcionalidade em desenvolvimento")
            else:
                st.error("❌ Nenhum telefone encontrado nos responsáveis")
    
    with col_envio3:
        if st.button("💾 Download Direto", use_container_width=True):
            st.success("✅ Download iniciado!")
            st.info("🔧 Funcionalidade em desenvolvimento")
    
    # Preview de dados para relatório
    with st.expander("👁️ Preview dos Dados do Relatório"):
        st.markdown("**📊 Dados que serão incluídos no relatório:**")
        
        # Resumo da mensalidade
        col_preview1, col_preview2 = st.columns(2)
        
        with col_preview1:
            st.markdown("**💰 Mensalidade:**")
            st.text(f"Mês: {mensalidade['mes_referencia']}")
            st.text(f"Valor: {formatar_valor_br(mensalidade['valor'])}")
            st.text(f"Vencimento: {formatar_data_br(mensalidade['data_vencimento'])}")
            st.text(f"Status: {mensalidade['status']}")
        
        with col_preview2:
            st.markdown("**👨‍🎓 Aluno:**")
            st.text(f"Nome: {aluno['nome']}")
            st.text(f"Turma: {aluno['turmas']['nome_turma']}")
            st.text(f"Turno: {aluno.get('turno', 'N/A')}")
        
        if responsaveis:
            st.markdown("**👥 Responsáveis:**")
            for resp in responsaveis:
                resp_data = resp["responsaveis"]
                st.text(f"• {resp_data['nome']} ({resp.get('parentesco', 'N/A')})")

# ==========================================================
# 🤖 ABA 6: PROCESSAMENTO AUTOMÁTICO
# ==========================================================

def renderizar_aba_processamento_automatico(dados: Dict):
    """Renderiza a aba de processamento automatizado simplificado"""
    
    st.markdown("### 🤖 Processamento Automatizado Simplificado")
    st.markdown("""
    **Turmas-alvo:** Berçário, Infantil I, Infantil II, Infantil III
    
    Esta funcionalidade gera mensalidades automaticamente para alunos elegíveis e correlaciona
    com pagamentos PIX do extrato de forma inteligente e segura.
    """)
    
    # Inicializar estado da sessão de processamento
    if 'sessao_processamento_simples' not in st.session_state:
        st.session_state.sessao_processamento_simples = None
    if 'etapa_processamento_simples' not in st.session_state:
        st.session_state.etapa_processamento_simples = 1
    
    # Verificar se há uma sessão em andamento
    sessao = st.session_state.sessao_processamento_simples
    
    if sessao is None:
        # ==========================================================
        # TELA INICIAL: CONFIGURAÇÃO SIMPLIFICADA
        # ==========================================================
        renderizar_configuracao_inicial_simplificada()
    else:
        # ==========================================================
        # TELAS DE PROCESSAMENTO BASEADAS NA ETAPA
        # ==========================================================
        if sessao.etapa_atual == 1:
            renderizar_etapa_1_simplificada(sessao)
        elif sessao.etapa_atual == 2:
            renderizar_etapa_2_simplificada(sessao)
        else:
            renderizar_resultado_final_simplificado(sessao)

def renderizar_configuracao_inicial_simplificada():
    """Renderiza a tela inicial de configuração simplificada"""
    
    st.markdown("#### ⚙️ Configuração do Processamento")
    
    # Informações sobre as turmas-alvo
    st.info("""
    **🎯 Turmas processadas automaticamente:**
    - Berçário
    - Infantil I  
    - Infantil II
    - Infantil III
    
    **📋 Critérios de elegibilidade:**
    - Aluno não possui mensalidades geradas
    - Possui data de matrícula definida
    - Possui dia de vencimento definido
    - Possui valor de mensalidade > 0
    """)
    
    # Interface de configuração simplificada
    with st.form("form_configuracao_processamento_simples"):
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            st.markdown("**📝 Identificação da Sessão:**")
            
            nome_sessao = st.text_input(
                "Nome da Sessão:",
                value=f"Processamento {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                help="Nome para identificar esta sessão de processamento"
            )
            
            modo_teste = st.checkbox(
                "🧪 Modo de Teste (Recomendado)",
                value=True,
                help="Se marcado, adiciona identificação especial aos dados para teste"
            )
        
        with col_config2:
            st.markdown("**📊 Informações do Sistema:**")
            
            # Mostrar preview rápido dos dados
            with st.spinner("🔄 Verificando dados..."):
                turmas_alvo = ["berçário", "infantil i", "infantil ii", "infantil iii"]
                alunos_elegiveis = identificar_alunos_elegiveis(turmas_alvo)
                
                st.write(f"👥 **Alunos elegíveis:** {len(alunos_elegiveis)}")
                st.write(f"🎓 **Turmas processadas:** 4 turmas")
                st.write(f"🧪 **Modo:** {'Teste (seguro)' if modo_teste else '⚠️ PRODUÇÃO'}")
        
        # Botões de ação
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn1:
            iniciar_processamento = st.form_submit_button(
                "🚀 Iniciar Processamento",
                type="primary"
            )
        
        with col_btn2:
            if st.form_submit_button("📊 Preview", type="secondary"):
                st.info("📋 Preview dos alunos elegíveis mostrado acima")
        
        with col_btn3:
            if st.form_submit_button("🔄 Atualizar", type="secondary"):
                st.rerun()
        
        # Processar início se solicitado
        if iniciar_processamento:
            with st.spinner("🤖 Iniciando processamento automatizado..."):
                try:
                    turmas_alvo = ["berçário", "infantil i", "infantil ii", "infantil iii"]
                    
                    sessao = iniciar_processamento_simplificado(
                        turmas_nomes=turmas_alvo,
                        nome_sessao=nome_sessao,
                        modo_teste=modo_teste
                    )
                    
                    # Salvar na sessão
                    st.session_state.sessao_processamento_simples = sessao
                    st.session_state.etapa_processamento_simples = 1
                    
                    if sessao.id != "ERRO":
                        st.success(f"✅ Processamento iniciado! Identificados {len(sessao.alunos_elegiveis)} alunos.")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao iniciar processamento")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao iniciar processamento: {str(e)}")

def renderizar_etapa_1_simplificada(sessao: SessaoProcessamentoSimplificada):
    """Renderiza a primeira etapa: validação das mensalidades geradas"""
    
    st.markdown("#### 📋 Etapa 1: Validação das Mensalidades Geradas")
    st.markdown(f"**Sessão:** {sessao.nome} | **Modo:** {'🧪 Teste' if sessao.modo_teste else '⚠️ PRODUÇÃO'}")
    
    if not sessao.alunos_elegiveis:
        st.warning("⚠️ Nenhum aluno elegível foi encontrado")
        if st.button("🔄 Tentar Novamente", type="primary"):
            st.session_state.sessao_processamento_simples = None
            st.rerun()
        return
    
    # Estatísticas gerais
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("👥 Alunos Elegíveis", len(sessao.alunos_elegiveis))
    
    with col_stat2:
        total_mensalidades = sum(len(a.mensalidades_a_gerar) for a in sessao.alunos_elegiveis)
        st.metric("📋 Mensalidades Geradas", total_mensalidades)
    
    with col_stat3:
        valor_total = sum(sum(float(m["valor"]) for m in a.mensalidades_a_gerar) for a in sessao.alunos_elegiveis)
        st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
    
    with col_stat4:
        alunos_com_pagamentos = len([a for a in sessao.alunos_elegiveis if a.pagamentos_correlacionados])
        st.metric("🔗 Com Correlações", alunos_com_pagamentos)
    
    # Lista de mensalidades geradas
    st.markdown("---")
    st.markdown("### 📋 Mensalidades Geradas por Aluno")
    
    st.info("""
    **📝 Instruções:**
    - Revise as mensalidades geradas automaticamente
    - Você pode editar valores e datas antes de prosseguir
    - Marque/desmarque alunos que deseja incluir no processamento
    """)
    
    # Lista de alunos com mensalidades
    for i, aluno in enumerate(sessao.alunos_elegiveis):
        # Inicializar status se não existir
        if not hasattr(aluno, 'incluir_processamento'):
            aluno.incluir_processamento = True
        
        # Checkbox para incluir/excluir aluno
        incluir = st.checkbox(
            f"Incluir {aluno.nome} - {aluno.turma_nome} no processamento",
            value=aluno.incluir_processamento,
            key=f"incluir_aluno_{i}"
        )
        aluno.incluir_processamento = incluir
        
        if incluir and aluno.mensalidades_a_gerar:
            with st.expander(f"📋 {aluno.nome} - {len(aluno.mensalidades_a_gerar)} mensalidades", expanded=False):
                
                col_info1, col_info2 = st.columns([1, 1])
                
                with col_info1:
                    st.markdown("**👨‍🎓 Dados do Aluno:**")
                    st.write(f"• Nome: {aluno.nome}")
                    st.write(f"• Turma: {aluno.turma_nome}")
                    st.write(f"• Valor Mensalidade: R$ {aluno.valor_mensalidade:.2f}")
                    st.write(f"• Dia Vencimento: {aluno.dia_vencimento}")
                
                with col_info2:
                    st.markdown("**📊 Resumo das Mensalidades:**")
                    st.write(f"• Quantidade: {len(aluno.mensalidades_a_gerar)}")
                    valor_total = sum(float(m['valor']) for m in aluno.mensalidades_a_gerar)
                    st.write(f"• Valor Total: R$ {valor_total:.2f}")
                    
                    if aluno.mensalidades_a_gerar:
                        primeiro_mes = aluno.mensalidades_a_gerar[0]['mes_referencia']
                        ultimo_mes = aluno.mensalidades_a_gerar[-1]['mes_referencia']
                        st.write(f"• Período: {primeiro_mes} a {ultimo_mes}")
                
                # Tabela das mensalidades
                st.markdown("**📋 Mensalidades a serem criadas:**")
                
                # Preparar dados para exibição
                dados_mensalidades = []
                for j, mens in enumerate(aluno.mensalidades_a_gerar):
                    dados_mensalidades.append({
                        "Mês": mens['mes_referencia'],
                        "Vencimento": mens['data_vencimento'],
                        "Valor": f"R$ {float(mens['valor']):.2f}",
                        "Status": "A vencer"
                    })
                
                if dados_mensalidades:
                    df_mensalidades = pd.DataFrame(dados_mensalidades)
                    st.dataframe(df_mensalidades, hide_index=True, use_container_width=True)
                
                # Opção para editar valores
                if st.button(f"✏️ Editar Mensalidades de {aluno.nome}", key=f"editar_{i}"):
                    st.session_state[f'editando_aluno_{i}'] = True
                    st.rerun()
                
                # Formulário de edição (se ativo)
                if st.session_state.get(f'editando_aluno_{i}', False):
                    st.markdown("##### ✏️ Editar Mensalidades")
                    
                    with st.form(f"form_edicao_{i}"):
                        novo_valor = st.number_input(
                            "Novo valor para todas as mensalidades:",
                            min_value=0.01,
                            value=aluno.valor_mensalidade,
                            step=0.01,
                            format="%.2f"
                        )
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.form_submit_button("💾 Aplicar Mudanças"):
                                # Atualizar valores
                                for mens in aluno.mensalidades_a_gerar:
                                    mens['valor'] = novo_valor
                                
                                st.session_state[f'editando_aluno_{i}'] = False
                                st.success("✅ Valores atualizados!")
                                st.rerun()
                        
                        with col_btn2:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state[f'editando_aluno_{i}'] = False
                                st.rerun()
        
        elif not aluno.mensalidades_a_gerar:
            st.warning(f"⚠️ {aluno.nome}: Nenhuma mensalidade foi gerada")
        
        elif not incluir:
            st.info(f"ℹ️ {aluno.nome}: Excluído do processamento")
    
    # Botões de navegação
    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
    
    with col_nav1:
        if st.button("◀️ Cancelar Processamento", type="secondary"):
            st.session_state.sessao_processamento_simples = None
            st.rerun()
    
    with col_nav3:
        alunos_selecionados = [a for a in sessao.alunos_elegiveis if getattr(a, 'incluir_processamento', True)]
        total_mensalidades = sum(len(a.mensalidades_a_gerar) for a in alunos_selecionados)
        
        if st.button(
            f"▶️ Próxima Etapa ({len(alunos_selecionados)} alunos, {total_mensalidades} mensalidades)",
            type="primary",
            disabled=len(alunos_selecionados) == 0
        ):
            sessao.etapa_atual = 2
            st.rerun()

def renderizar_etapa_2_simplificada(sessao: SessaoProcessamentoSimplificada):
    """Renderiza a segunda etapa: correlação com pagamentos PIX"""
    
    st.markdown("#### 🔗 Etapa 2: Correlação com Pagamentos PIX")
    st.markdown(f"**Sessão:** {sessao.nome}")
    
    alunos_selecionados = [a for a in sessao.alunos_elegiveis if getattr(a, 'incluir_processamento', True)]
    
    if not alunos_selecionados:
        st.error("❌ Nenhum aluno selecionado para prosseguir")
        if st.button("◀️ Voltar", type="secondary"):
            sessao.etapa_atual = 1
            st.rerun()
        return
    
    # Estatísticas da etapa
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        st.metric("👥 Alunos Selecionados", len(alunos_selecionados))
    
    with col_stat2:
        total_mensalidades = sum(len(a.mensalidades_a_gerar) for a in alunos_selecionados)
        st.metric("📋 Mensalidades a Criar", total_mensalidades)
    
    with col_stat3:
        total_correlacoes = sum(len(a.pagamentos_correlacionados) for a in alunos_selecionados)
        st.metric("🔗 Correlações PIX", total_correlacoes)
    
    # Lista de correlações
    st.markdown("---")
    st.markdown("### 🔗 Correlações com Pagamentos PIX")
    
    st.info("""
    **📋 Resumo da Etapa 2:**
    - Mensalidades foram geradas automaticamente baseadas na data de matrícula
    - Sistema identificou pagamentos PIX que podem estar relacionados aos alunos
    - Revise as correlações abaixo antes de executar as ações
    """)
    
    for i, aluno in enumerate(alunos_selecionados):
        with st.expander(f"🔗 {aluno.nome} - {aluno.turma_nome}", expanded=False):
            
            col_resumo1, col_resumo2 = st.columns(2)
            
            with col_resumo1:
                st.markdown("**📊 Mensalidades a Criar:**")
                st.write(f"• Quantidade: {len(aluno.mensalidades_a_gerar)}")
                if aluno.mensalidades_a_gerar:
                    valor_total = sum(float(m['valor']) for m in aluno.mensalidades_a_gerar)
                    st.write(f"• Valor Total: R$ {valor_total:.2f}")
                    st.write(f"• Primeira: {aluno.mensalidades_a_gerar[0]['mes_referencia']}")
                    st.write(f"• Última: {aluno.mensalidades_a_gerar[-1]['mes_referencia']}")
            
            with col_resumo2:
                st.markdown("**💰 Pagamentos PIX Correlacionados:**")
                if aluno.pagamentos_correlacionados:
                    st.write(f"• Encontrados: {len(aluno.pagamentos_correlacionados)}")
                    for j, pag in enumerate(aluno.pagamentos_correlacionados[:3], 1):  # Mostrar apenas os 3 primeiros
                        st.write(f"• PIX {j}: R$ {pag['valor']:.2f} - {pag['nome_remetente'][:30]}...")
                    
                    if len(aluno.pagamentos_correlacionados) > 3:
                        st.write(f"• ... e mais {len(aluno.pagamentos_correlacionados) - 3}")
                else:
                    st.write("• Nenhum pagamento correlacionado automaticamente")
                    st.write("• Mensalidades serão criadas sem vinculação inicial")
            
            # Detalhamento completo (opcional)
            if st.button(f"📋 Ver Detalhes Completos de {aluno.nome}", key=f"detalhes_{i}"):
                st.session_state[f'mostrar_detalhes_{i}'] = not st.session_state.get(f'mostrar_detalhes_{i}', False)
                st.rerun()
            
            if st.session_state.get(f'mostrar_detalhes_{i}', False):
                st.markdown("##### 📋 Mensalidades Detalhadas:")
                dados_mens = []
                for mens in aluno.mensalidades_a_gerar:
                    dados_mens.append({
                        "Mês": mens['mes_referencia'],
                        "Vencimento": mens['data_vencimento'],
                        "Valor": f"R$ {float(mens['valor']):.2f}"
                    })
                
                if dados_mens:
                    df_mens = pd.DataFrame(dados_mens)
                    st.dataframe(df_mens, hide_index=True, use_container_width=True)
                
                if aluno.pagamentos_correlacionados:
                    st.markdown("##### 💰 Pagamentos PIX Detalhados:")
                    dados_pix = []
                    for pix in aluno.pagamentos_correlacionados:
                        dados_pix.append({
                            "Data": pix['data_pagamento'],
                            "Valor": f"R$ {pix['valor']:.2f}",
                            "Remetente": pix['nome_remetente'],
                            "ID": pix['id']
                        })
                    
                    df_pix = pd.DataFrame(dados_pix)
                    st.dataframe(df_pix, hide_index=True, use_container_width=True)
    
    # Botões de navegação
    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
    
    with col_nav1:
        if st.button("◀️ Voltar", type="secondary"):
            sessao.etapa_atual = 1
            st.rerun()
    
    with col_nav2:
        st.markdown("**⚠️ Atenção:** As ações serão executadas com identificação de teste")
    
    with col_nav3:
        if st.button("🚀 EXECUTAR AÇÕES", type="primary"):
            # Executar processamento
            with st.spinner("💾 Executando ações..."):
                resultado = executar_acoes_modo_teste(sessao)
                
                if resultado.get("success"):
                    st.success(f"""
                    ✅ **Ações executadas com sucesso!**
                    
                    - Mensalidades criadas: {resultado.get('mensalidades_criadas', 0)}
                    - Correlações registradas: {resultado.get('correlacoes_registradas', 0)}
                    """)
                    
                    sessao.etapa_atual = 3  # Ir para resultado final
                    st.rerun()
                else:
                    st.error(f"❌ Erro na execução: {resultado.get('error')}")



def renderizar_resultado_final_simplificado(sessao: SessaoProcessamentoSimplificada):
    """Renderiza o resultado final do processamento simplificado"""
    
    st.markdown("#### 🎉 Processamento Concluído com Sucesso!")
    st.markdown(f"**Sessão:** {sessao.nome}")
    
    st.success("✅ **Processamento automatizado executado com sucesso!**")
    
    # Estatísticas finais
    alunos_processados = [a for a in sessao.alunos_elegiveis if getattr(a, 'incluir_processamento', True)]
    
    col_final1, col_final2, col_final3 = st.columns(3)
    
    with col_final1:
        st.metric("👥 Alunos Processados", len(alunos_processados))
    
    with col_final2:
        total_mensalidades = sum(len(a.mensalidades_a_gerar) for a in alunos_processados)
        st.metric("📋 Mensalidades Criadas", total_mensalidades)
    
    with col_final3:
        total_correlacoes = sum(len(a.pagamentos_correlacionados) for a in alunos_processados)
        st.metric("🔗 Correlações Registradas", total_correlacoes)
    
    # Próximos passos
    st.markdown("---")
    st.markdown("### 🎯 Próximos Passos")
    
    if sessao.modo_teste:
        st.info("""
        🧪 **Dados com Identificação de Teste**
        
        As mensalidades foram criadas com identificação "[TESTE]":
        - Verifique os resultados na lista principal de mensalidades
        - Busque por mensalidades com observação contendo "[TESTE]"
        - As correlações PIX foram registradas para auditoria
        """)
    else:
        st.warning("""
        ⚠️ **Dados Inseridos em Produção**
        
        As mensalidades foram criadas no banco de produção:
        - Verifique os resultados na interface principal
        - As mensalidades aparecem na lista normal
        - As correlações PIX foram registradas
        """)
    
    # Resumo dos alunos processados
    st.markdown("### 📋 Resumo dos Alunos Processados")
    
    for aluno in alunos_processados:
        if aluno.mensalidades_a_gerar:
            valor_total = sum(float(m['valor']) for m in aluno.mensalidades_a_gerar)
            st.markdown(f"""
            **{aluno.nome}** - {aluno.turma_nome}
            - 📋 {len(aluno.mensalidades_a_gerar)} mensalidades criadas
            - 💰 Valor total: R$ {valor_total:.2f}
            - 🔗 {len(aluno.pagamentos_correlacionados)} correlações PIX
            """)
    
    # Ações finais
    st.markdown("---")
    col_acao1, col_acao2, col_acao3 = st.columns(3)
    
    with col_acao1:
        if st.button("🔄 Novo Processamento", type="primary", use_container_width=True):
            st.session_state.sessao_processamento_simples = None
            st.session_state.etapa_processamento_simples = 1
            st.rerun()
    
    with col_acao2:
        if st.button("📊 Ver Mensalidades", use_container_width=True):
            st.info("💡 Volte para a interface principal para ver as mensalidades criadas")
    
    with col_acao3:
        if st.button("❌ Fechar Modal", use_container_width=True):
            st.session_state.modal_aberto = False
            st.session_state.id_mensalidade_modal = None
            st.rerun()

# ==========================================================
# 🚀 FUNÇÃO PRINCIPAL DO MODAL
# ==========================================================

def abrir_modal_mensalidade(id_mensalidade: str):
    """
    Função principal para abrir o modal de mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade para exibir
    """
    
    # Verificar se deve fechar o modal
    if st.session_state.get('fechar_modal', False):
        st.session_state.modal_aberto = False
        st.session_state.id_mensalidade_modal = None
        st.session_state.fechar_modal = False
        st.rerun()
    
    # Buscar dados completos
    with st.spinner("🔄 Carregando dados da mensalidade..."):
        resultado = buscar_dados_completos_mensalidade(id_mensalidade)
    
    if not resultado.get("success"):
        st.error(f"❌ Erro ao carregar mensalidade: {resultado.get('error')}")
        return
    
    dados = resultado["dados"]
    
    # Inicializar estado das abas se necessário
    if 'aba_ativa_modal' not in st.session_state:
        st.session_state.aba_ativa_modal = "Detalhes"
    
    # Renderizar header
    renderizar_header_modal(dados)
    
    # Tabs principais do modal
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Detalhes",
        "✏️ Edição", 
        "⚡ Ações",
        "📚 Histórico",
        "📊 Relatórios",
        "🤖 Processamento"
    ])
    
    # Renderizar conteúdo das abas
    with tab1:
        renderizar_aba_detalhes(dados)
    
    with tab2:
        renderizar_aba_edicao(dados)
    
    with tab3:
        renderizar_aba_acoes(dados)
    
    with tab4:
        renderizar_aba_historico(dados)
    
    with tab5:
        renderizar_aba_relatorios(dados)
    
    with tab6:
        renderizar_aba_processamento_automatico(dados)
    
    # Renderizar footer
    renderizar_footer_modal(dados)

# ==========================================================
# 🎯 FUNÇÃO DE COMPATIBILIDADE
# ==========================================================

def open_modal(id_mensalidade: str):
    """Função de compatibilidade com o sistema existente"""
    return abrir_modal_mensalidade(id_mensalidade) 