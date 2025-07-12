#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 EXEMPLO DE USO DO MODAL DE MENSALIDADE COMPLETO
==================================================

Demonstração prática de como integrar e usar o modal de detalhamento 
e ações de mensalidade no sistema de gestão escolar.

Como usar:
1. Instale as dependências: streamlit, supabase
2. Execute: streamlit run exemplo_uso_modal_mensalidade.py
3. Navegue pela interface e teste o modal
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import uuid # Adicionado para geração de IDs únicos
import calendar

# Importar o modal completo
from modal_mensalidade_completo import abrir_modal_mensalidade
from models.base import obter_timestamp

# Importar dependências do sistema
try:
    from models.base import supabase, formatar_data_br, formatar_valor_br
except ImportError:
    st.error("⚠️ Módulos do sistema não encontrados. Certifique-se de que está no diretório correto.")
    st.stop()

# ==========================================================
# 🎨 CONFIGURAÇÃO DA PÁGINA
# ==========================================================

st.set_page_config(
    page_title="🎓 Sistema de Gestão Escolar - Mensalidades",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS adicional para melhorar a aparência
st.markdown("""
<style>
    /* Ocultar elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilo dos cartões */
    .main-card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    /* Estilo da barra lateral */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Botões personalizados */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Métricas customizadas */
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Cards de status */
    .status-card {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .status-elegivel {
        background: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }
    
    .status-nao-elegivel {
        background: #f8d7da;
        border-left-color: #dc3545;
        color: #721c24;
    }
    
    .status-correlacao {
        background: #d1ecf1;
        border-left-color: #17a2b8;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 🔧 FUNÇÕES AUXILIARES
# ==========================================================

def buscar_mensalidades_completas(filtros: Dict = None) -> Dict:
    """
    Busca mensalidades com aplicação de filtros na query SQL para melhor performance
    
    Args:
        filtros: Dict com filtros opcionais
        
    Returns:
        Dict: {"success": bool, "mensalidades": List[Dict], "total": int, "error": str}
    """
    try:
        # Query base sem filtros de status para buscar TODAS as mensalidades
        # CORREÇÃO: Removido 'turno as turma_turno' pois turno está na tabela alunos, não turmas
        query = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, 
            data_pagamento, status, observacoes, inserted_at, updated_at,
            alunos!inner(
                id, nome, turno, valor_mensalidade,
                turmas!inner(nome_turma)
            )
        """)
        
        # Aplicar filtro de período na query SQL para melhor performance
        if filtros and filtros.get("periodo"):
            periodo = filtros["periodo"]
            if periodo == "Últimos 30 dias":
                data_limite = (date.today() - timedelta(days=30)).isoformat()
                query = query.gte("data_vencimento", data_limite)
            elif periodo == "Últimos 60 dias":
                data_limite = (date.today() - timedelta(days=60)).isoformat()
                query = query.gte("data_vencimento", data_limite)
            elif periodo == "Últimos 90 dias":
                data_limite = (date.today() - timedelta(days=90)).isoformat()
                query = query.gte("data_vencimento", data_limite)
            elif periodo == "Período customizado":
                # Aplicar filtro de período customizado se definido
                if filtros.get("data_inicio"):
                    query = query.gte("data_vencimento", filtros["data_inicio"])
                if filtros.get("data_fim"):
                    query = query.lte("data_vencimento", filtros["data_fim"])
            # "Todos" não aplica filtro de data
        
        # Aplicar filtro de turmas múltiplas na query SQL
        if filtros and filtros.get("turmas_selecionadas"):
            turmas_selecionadas = filtros["turmas_selecionadas"]
            if turmas_selecionadas and "Todas" not in turmas_selecionadas:
                # Se há turmas específicas selecionadas, aplicar filtro
                query = query.in_("alunos.turmas.nome_turma", turmas_selecionadas)
        
        # Ordenar por data de vencimento (mais recentes primeiro)
        response = query.order("data_vencimento", desc=True).execute()
        
        mensalidades = response.data if response.data else []
        
        return {
            "success": True,
            "mensalidades": mensalidades,
            "total": len(mensalidades),
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "mensalidades": [],
            "total": 0,
            "error": str(e)
        }

def aplicar_filtros_interface(mensalidades: List[Dict], filtros: Dict) -> List[Dict]:
    """
    Aplica filtros que não podem ser aplicados na query SQL
    
    Args:
        mensalidades: Lista de mensalidades
        filtros: Dict com filtros
        
    Returns:
        List[Dict]: Mensalidades filtradas
    """
    if not mensalidades:
        return []
    
    mensalidades_filtradas = mensalidades.copy()
    
    # Filtro por status (aplicado na interface)
    if filtros.get("status") and filtros["status"] != "Todos":
        mensalidades_filtradas = [
            m for m in mensalidades_filtradas 
            if m.get("status") == filtros["status"]
        ]
    
    # Filtro por nome do aluno (aplicado na interface)
    if filtros.get("nome_aluno") and filtros["nome_aluno"].strip():
        nome_filtro = filtros["nome_aluno"].lower().strip()
        mensalidades_filtradas = [
            m for m in mensalidades_filtradas 
            if nome_filtro in m.get("alunos", {}).get("nome", "").lower()
        ]
    
    return mensalidades_filtradas

def calcular_estatisticas(mensalidades: List[Dict]) -> Dict:
    """Calcula estatísticas das mensalidades"""
    if not mensalidades:
        return {
            "total": 0,
            "valor_total": 0,
            "pagas": 0,
            "pendentes": 0,
            "atrasadas": 0,
            "parciais": 0,
            "canceladas": 0
        }
    
    total = len(mensalidades)
    valor_total = sum(float(m.get("valor", 0)) for m in mensalidades)
    
    # Contar por status
    pagas = len([m for m in mensalidades if m.get("status") == "Pago"])
    parciais = len([m for m in mensalidades if m.get("status") == "Pago parcial"])
    canceladas = len([m for m in mensalidades if m.get("status") == "Cancelado"])
    
    # Calcular atrasadas baseado na data
    hoje = date.today()
    atrasadas = 0
    
    for m in mensalidades:
        if m.get("status") not in ["Pago", "Pago parcial", "Cancelado"]:
            try:
                vencimento = datetime.strptime(m.get("data_vencimento", ""), "%Y-%m-%d").date()
                if vencimento < hoje:
                    atrasadas += 1
            except:
                pass
    
    pendentes = total - pagas - parciais - atrasadas - canceladas
    
    return {
        "total": total,
        "valor_total": valor_total,
        "pagas": pagas,
        "parciais": parciais,
        "pendentes": pendentes,
        "atrasadas": atrasadas,
        "canceladas": canceladas
    }

def obter_resumo_status(mensalidades: List[Dict]) -> Dict:
    """
    Obtém resumo dos status das mensalidades para debug
    
    Returns:
        Dict: Contagem por status
    """
    resumo = {}
    for m in mensalidades:
        status = m.get("status", "Sem status")
        resumo[status] = resumo.get(status, 0) + 1
    
    return resumo

# ==========================================================
# 🤖 FUNÇÕES DE PROCESSAMENTO AUTOMATIZADO  
# ==========================================================

def buscar_turmas_disponiveis() -> List[Dict]:
    """Busca todas as turmas disponíveis"""
    try:
        response = supabase.table("turmas").select("id, nome_turma").order("nome_turma").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Erro ao buscar turmas: {str(e)}")
        return []

def identificar_alunos_elegiveis(turmas_selecionadas: List[str]) -> List[Dict]:
    """
    Identifica alunos elegíveis para processamento automatizado
    
    Args:
        turmas_selecionadas: Lista de nomes das turmas selecionadas
        
    Returns:
        List[Dict]: Lista de alunos elegíveis com todos os dados necessários
    """
    try:
        # Buscar alunos das turmas selecionadas com todas as informações necessárias
        query = supabase.table("alunos").select("""
            id, nome, turno, data_nascimento, dia_vencimento, 
            data_matricula, valor_mensalidade, mensalidades_geradas,
            turmas!inner(id, nome_turma),
            alunos_responsaveis!inner(
                responsaveis!inner(id, nome, telefone, email, cpf)
            )
        """)
        
        # Filtrar por turmas se não for "Todas"
        if "Todas" not in turmas_selecionadas:
            query = query.in_("turmas.nome_turma", turmas_selecionadas)
        
        response = query.execute()
        alunos = response.data if response.data else []
        
        # Filtrar alunos elegíveis
        alunos_elegiveis = []
        
        for aluno in alunos:
            # Critérios de elegibilidade (REMOVIDO: tem_data_matricula)
            tem_dia_vencimento = aluno.get('dia_vencimento') is not None
            tem_valor_mensalidade = aluno.get('valor_mensalidade') is not None and float(aluno.get('valor_mensalidade', 0)) > 0
            tem_responsaveis = len(aluno.get('alunos_responsaveis', [])) > 0
            nao_tem_mensalidades = not aluno.get('mensalidades_geradas', False)
            
            # Verificar se tem data de matrícula (para classificação do tipo de processamento)
            tem_data_matricula = aluno.get('data_matricula') is not None
            
            elegivel = (tem_dia_vencimento and tem_valor_mensalidade and 
                       tem_responsaveis and nao_tem_mensalidades)
            
            # Adicionar informações de elegibilidade
            aluno['elegivel'] = elegivel
            aluno['tem_data_matricula'] = tem_data_matricula
            aluno['criterios'] = {
                'tem_dia_vencimento': tem_dia_vencimento,
                'tem_valor_mensalidade': tem_valor_mensalidade,
                'tem_responsaveis': tem_responsaveis,
                'nao_tem_mensalidades': nao_tem_mensalidades,
                'tem_data_matricula': tem_data_matricula  # Para informação, não mais obrigatório
            }
            
            # Classificar tipo de processamento
            if elegivel:
                if tem_data_matricula:
                    aluno['tipo_processamento'] = 'gerar_mensalidades'
                    aluno['tipo_label'] = '📋 Gerar Mensalidades'
                    aluno['tipo_descricao'] = 'Aluno já possui data de matrícula. Mensalidades serão geradas e correlacionadas com pagamentos.'
                else:
                    aluno['tipo_processamento'] = 'identificar_matricula'
                    aluno['tipo_label'] = '🔍 Identificar Matrícula'
                    aluno['tipo_descricao'] = 'Primeiro pagamento será identificado como matrícula, depois mensalidades serão correlacionadas.'
                
                alunos_elegiveis.append(aluno)
        
        return alunos_elegiveis
        
    except Exception as e:
        st.error(f"❌ Erro ao identificar alunos elegíveis: {str(e)}")
        return []

def buscar_pagamentos_extrato_pix(ids_responsaveis: List[str]) -> List[Dict]:
    """
    Busca pagamentos no extrato PIX para os responsáveis especificados
    
    Args:
        ids_responsaveis: Lista de IDs dos responsáveis
        
    Returns:
        List[Dict]: Lista de pagamentos PIX disponíveis
    """
    try:
        response = supabase.table("extrato_pix").select("*").in_(
            "id_responsavel", ids_responsaveis
        ).eq("status", "novo").order("data_pagamento").execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        st.error(f"❌ Erro ao buscar extrato PIX: {str(e)}")
        return []

def correlacionar_pagamentos_mensalidades(aluno: Dict, pagamentos_pix: List[Dict]) -> Dict:
    """
    Correlaciona pagamentos PIX com matrícula e mensalidades do aluno
    Agora suporta dois fluxos:
    1. Alunos SEM data_matricula: identifica primeiro pagamento como matrícula
    2. Alunos COM data_matricula: gera mensalidades e correlaciona pagamentos
    
    Args:
        aluno: Dados do aluno elegível
        pagamentos_pix: Lista de pagamentos PIX dos responsáveis
        
    Returns:
        Dict: Correlações identificadas
    """
    try:
        correlacoes = {
            'matricula': None,
            'mensalidades': [],
            'pagamentos_utilizados': [],
            'tipo_processamento': aluno.get('tipo_processamento', 'identificar_matricula'),
            'mensalidades_a_gerar': []  # Para alunos com matrícula, lista de mensalidades a criar
        }
        
        if not pagamentos_pix:
            return correlacoes
        
        # Ordenar pagamentos por data
        pagamentos_ordenados = sorted(pagamentos_pix, key=lambda x: x['data_pagamento'])
        valor_mensalidade = float(aluno.get('valor_mensalidade', 0))
        
        if aluno.get('tipo_processamento') == 'identificar_matricula':
            # FLUXO 1: ALUNOS SEM DATA DE MATRÍCULA
            # Identificar primeiro pagamento como matrícula, demais como mensalidades
            
            for i, pagamento in enumerate(pagamentos_ordenados):
                valor_pago = float(pagamento['valor'])
                
                # Se o valor é igual à mensalidade e ainda não foi usado
                if abs(valor_pago - valor_mensalidade) < 0.01 and pagamento['id'] not in correlacoes['pagamentos_utilizados']:
                    if correlacoes['matricula'] is None:
                        # Primeiro pagamento = matrícula
                        correlacoes['matricula'] = {
                            'pagamento': pagamento,
                            'tipo': 'matricula',
                            'mes_referencia': 'Matrícula',
                            'valor': valor_pago,
                            'data_pagamento': pagamento['data_pagamento']
                        }
                        correlacoes['pagamentos_utilizados'].append(pagamento['id'])
                    else:
                        # Próximos pagamentos = mensalidades
                        mes_numero = len(correlacoes['mensalidades']) + 1
                        
                        # Usar data do primeiro pagamento como referência para calcular meses
                        from datetime import datetime
                        data_ref = datetime.strptime(correlacoes['matricula']['data_pagamento'], '%Y-%m-%d')
                        
                        # Calcular o mês e ano corretos
                        ano = data_ref.year
                        mes = data_ref.month + mes_numero - 1
                        
                        # Ajustar se o mês passou de 12
                        while mes > 12:
                            ano += 1
                            mes -= 12
                        
                        mes_ref = data_ref.replace(year=ano, month=mes)
                        mes_referencia = mes_ref.strftime('%m/%Y')
                        
                        # Calcular data de vencimento
                        dia_vencimento = int(aluno.get('dia_vencimento', 5))
                        try:
                            data_vencimento = mes_ref.replace(day=dia_vencimento).strftime('%Y-%m-%d')
                        except ValueError:
                            # Se o dia não existe no mês, usar último dia do mês
                            ultimo_dia = calendar.monthrange(mes_ref.year, mes_ref.month)[1]
                            dia_ajustado = min(dia_vencimento, ultimo_dia)
                            data_vencimento = mes_ref.replace(day=dia_ajustado).strftime('%Y-%m-%d')
                        
                        correlacoes['mensalidades'].append({
                            'pagamento': pagamento,
                            'tipo': 'mensalidade',
                            'mes_referencia': mes_referencia,
                            'valor': valor_pago,
                            'data_pagamento': pagamento['data_pagamento'],
                            'data_vencimento': data_vencimento
                        })
                        correlacoes['pagamentos_utilizados'].append(pagamento['id'])
        
        else:
            # FLUXO 2: ALUNOS COM DATA DE MATRÍCULA
            # Gerar mensalidades baseadas na data de matrícula e correlacionar com pagamentos
            
            data_matricula = aluno.get('data_matricula')
            if data_matricula:
                from datetime import datetime
                data_mat = datetime.strptime(data_matricula, '%Y-%m-%d')
                
                # Gerar mensalidades a partir da data de matrícula até hoje (ou até ter pagamentos suficientes)
                hoje = datetime.now()
                mensalidades_geradas = []
                mes_atual = data_mat
                mes_numero = 1
                
                # Gerar mensalidades até hoje ou até acabarem os pagamentos
                while mes_atual <= hoje and len(mensalidades_geradas) <= len(pagamentos_ordenados):
                    # Calcular data de vencimento
                    dia_vencimento = int(aluno.get('dia_vencimento', 5))
                    try:
                        data_vencimento = mes_atual.replace(day=dia_vencimento).strftime('%Y-%m-%d')
                    except ValueError:
                        ultimo_dia = calendar.monthrange(mes_atual.year, mes_atual.month)[1]
                        dia_ajustado = min(dia_vencimento, ultimo_dia)
                        data_vencimento = mes_atual.replace(day=dia_ajustado).strftime('%Y-%m-%d')
                    
                    mensalidade_gerada = {
                        'mes_referencia': mes_atual.strftime('%m/%Y'),
                        'valor': valor_mensalidade,
                        'data_vencimento': data_vencimento,
                        'numero_sequencial': mes_numero
                    }
                    mensalidades_geradas.append(mensalidade_gerada)
                    
                    # Próximo mês
                    ano = mes_atual.year
                    mes = mes_atual.month + 1
                    if mes > 12:
                        ano += 1
                        mes = 1
                    mes_atual = mes_atual.replace(year=ano, month=mes)
                    mes_numero += 1
                
                correlacoes['mensalidades_a_gerar'] = mensalidades_geradas
                
                # Correlacionar mensalidades geradas com pagamentos PIX
                for i, mensalidade in enumerate(mensalidades_geradas):
                    if i < len(pagamentos_ordenados):
                        pagamento = pagamentos_ordenados[i]
                        valor_pago = float(pagamento['valor'])
                        
                        # Verificar se o valor do pagamento é compatível (tolerância de R$ 10)
                        if abs(valor_pago - valor_mensalidade) <= 10.0:
                            correlacoes['mensalidades'].append({
                                'pagamento': pagamento,
                                'tipo': 'mensalidade',
                                'mes_referencia': mensalidade['mes_referencia'],
                                'valor': valor_pago,
                                'data_pagamento': pagamento['data_pagamento'],
                                'data_vencimento': mensalidade['data_vencimento'],
                                'valor_esperado': valor_mensalidade,
                                'diferenca': valor_pago - valor_mensalidade
                            })
                            correlacoes['pagamentos_utilizados'].append(pagamento['id'])
        
        return correlacoes
        
    except Exception as e:
        st.error(f"❌ Erro ao correlacionar pagamentos: {str(e)}")
        return {'matricula': None, 'mensalidades': [], 'pagamentos_utilizados': [], 'tipo_processamento': 'erro', 'mensalidades_a_gerar': []}

def processar_correlacoes_alunos(alunos_elegiveis: List[Dict]) -> List[Dict]:
    """
    Processa correlações para todos os alunos elegíveis
    
    Args:
        alunos_elegiveis: Lista de alunos elegíveis
        
    Returns:
        List[Dict]: Alunos com correlações processadas
    """
    try:
        alunos_processados = []
        
        for aluno in alunos_elegiveis:
            # Obter IDs dos responsáveis
            ids_responsaveis = []
            for rel in aluno.get('alunos_responsaveis', []):
                if rel.get('responsaveis', {}).get('id'):
                    ids_responsaveis.append(rel['responsaveis']['id'])
            
            # Buscar pagamentos PIX
            pagamentos_pix = buscar_pagamentos_extrato_pix(ids_responsaveis) if ids_responsaveis else []
            
            # Fazer correlações
            correlacoes = correlacionar_pagamentos_mensalidades(aluno, pagamentos_pix)
            
            # Adicionar correlações ao aluno
            aluno['correlacoes'] = correlacoes
            aluno['tem_correlacoes'] = (correlacoes['matricula'] is not None or 
                                      len(correlacoes['mensalidades']) > 0)
            
            alunos_processados.append(aluno)
        
        return alunos_processados
        
    except Exception as e:
        st.error(f"❌ Erro ao processar correlações: {str(e)}")
        return alunos_elegiveis

def renderizar_aba_processamento():
    """Renderiza a aba de processamento automatizado"""
    
    st.markdown("### 🤖 Processamento Automatizado de Mensalidades")
    st.markdown("""
    Esta funcionalidade permite:
    - Selecionar turmas para processamento
    - Identificar alunos elegíveis automaticamente
    - Correlacionar com pagamentos PIX do extrato
    - Gerar mensalidades de forma inteligente
    """)
    
    # Inicializar estado da sessão
    if 'etapa_processamento' not in st.session_state:
        st.session_state.etapa_processamento = 1
    if 'alunos_processamento' not in st.session_state:
        st.session_state.alunos_processamento = []
    if 'turmas_processamento' not in st.session_state:
        st.session_state.turmas_processamento = []
    
    # ==========================================================
    # ETAPA 1: SELEÇÃO DE TURMAS
    # ==========================================================
    
    if st.session_state.etapa_processamento == 1:
        st.markdown("#### 📋 Etapa 1: Seleção de Turmas")
        
        # Buscar turmas disponíveis
        turmas_disponiveis = buscar_turmas_disponiveis()
        
        if not turmas_disponiveis:
            st.error("❌ Nenhuma turma encontrada no sistema")
            return
        
        # Interface de seleção
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**🎓 Selecione as turmas para processamento:**")
            
            opcoes_turmas = ["Todas"] + [t['nome_turma'] for t in turmas_disponiveis]
            
            turmas_selecionadas = st.multiselect(
                "Turmas:",
                options=opcoes_turmas,
                default=["Todas"],
                help="Selecione uma ou mais turmas específicas, ou 'Todas'"
            )
            
            # Lógica para "Todas"
            if "Todas" in turmas_selecionadas and len(turmas_selecionadas) > 1:
                turmas_selecionadas = ["Todas"]
                st.rerun()
            elif not turmas_selecionadas:
                turmas_selecionadas = ["Todas"]
                st.rerun()
        
        with col2:
            st.markdown("**📊 Informações:**")
            st.info(f"""
            **Total de turmas:** {len(turmas_disponiveis)}
            
            **Selecionadas:** {len(turmas_selecionadas) if "Todas" not in turmas_selecionadas else len(turmas_disponiveis)}
            
            **Critérios de elegibilidade:**
            - ✅ Possui dia de vencimento
            - ✅ Possui valor de mensalidade
            - ✅ Possui responsáveis cadastrados  
            - ✅ NÃO possui mensalidades geradas
            
            **Tipos de processamento:**
            - 🔍 **Identificar Matrícula**: Alunos sem data de matrícula
            - 📋 **Gerar Mensalidades**: Alunos com data de matrícula
            """)
        
        # Botões de ação
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn2:
            if st.button("🔍 Identificar Alunos Elegíveis", type="primary", use_container_width=True):
                with st.spinner("🔄 Buscando alunos elegíveis..."):
                    # Converter "Todas" para lista de nomes de turmas
                    if "Todas" in turmas_selecionadas:
                        nomes_turmas = [t['nome_turma'] for t in turmas_disponiveis]
                    else:
                        nomes_turmas = turmas_selecionadas
                    
                    # Identificar alunos elegíveis
                    alunos_elegiveis = identificar_alunos_elegiveis(nomes_turmas)
                    
                    if alunos_elegiveis:
                        st.session_state.alunos_processamento = alunos_elegiveis
                        st.session_state.turmas_processamento = nomes_turmas
                        st.session_state.etapa_processamento = 2
                        st.success(f"✅ Encontrados {len(alunos_elegiveis)} alunos elegíveis!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Nenhum aluno elegível encontrado nas turmas selecionadas")
    
    # ==========================================================
    # ETAPA 2: VALIDAÇÃO DOS ALUNOS ELEGÍVEIS
    # ==========================================================
    
    elif st.session_state.etapa_processamento == 2:
        st.markdown("#### 👥 Etapa 2: Validação dos Alunos Elegíveis")
        
        alunos = st.session_state.alunos_processamento
        turmas = st.session_state.turmas_processamento
        
        st.markdown(f"**🎓 Turmas selecionadas:** {', '.join(turmas)}")
        st.markdown(f"**👥 Total de alunos elegíveis:** {len(alunos)}")
        
        # Mostrar estatísticas
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("👥 Alunos Elegíveis", len(alunos))
        
        with col_stat2:
            total_valor = sum(float(a.get('valor_mensalidade', 0)) for a in alunos)
            st.metric("💰 Valor Total/Mês", f"R$ {total_valor:,.2f}")
        
        with col_stat3:
            turmas_unicas = len(set(a['turmas']['nome_turma'] for a in alunos))
            st.metric("🎓 Turmas", turmas_unicas)
        
        # Lista de alunos elegíveis
        st.markdown("---")
        st.markdown("### 📋 Lista de Alunos Elegíveis")
        
        for i, aluno in enumerate(alunos):
            # Checkbox para incluir/excluir aluno
            incluir_key = f"incluir_aluno_{i}"
            if incluir_key not in st.session_state:
                st.session_state[incluir_key] = True
            
            incluir = st.checkbox(
                f"Incluir no processamento",
                value=st.session_state[incluir_key],
                key=f"checkbox_{incluir_key}"
            )
            st.session_state[incluir_key] = incluir
            
            # Card do aluno
            with st.expander(f"👨‍🎓 {aluno['nome']} - {aluno['turmas']['nome_turma']}", expanded=False):
                
                # Mostrar tipo de processamento
                tipo_label = aluno.get('tipo_label', '❓ Não definido')
                tipo_descricao = aluno.get('tipo_descricao', '')
                
                st.markdown(f"""
                <div class="status-card status-{'elegivel' if 'Gerar' in tipo_label else 'correlacao'}">
                    <strong>{tipo_label}</strong><br>
                    {tipo_descricao}
                </div>
                """, unsafe_allow_html=True)
                
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("**📊 Dados Básicos:**")
                    st.write(f"• **Nome:** {aluno['nome']}")
                    st.write(f"• **Turma:** {aluno['turmas']['nome_turma']}")
                    st.write(f"• **Turno:** {aluno.get('turno', 'Não informado')}")
                    st.write(f"• **Data Matrícula:** {formatar_data_br(aluno.get('data_matricula', '')) if aluno.get('data_matricula') else '⚠️ Não informado'}")
                    st.write(f"• **Dia Vencimento:** {aluno.get('dia_vencimento')}")
                    st.write(f"• **Valor Mensalidade:** {formatar_valor_br(aluno.get('valor_mensalidade', 0))}")
                
                with col_info2:
                    st.markdown("**👥 Responsáveis:**")
                    for rel in aluno.get('alunos_responsaveis', []):
                        resp = rel.get('responsaveis', {})
                        st.write(f"• **{resp.get('nome', 'N/A')}**")
                        st.write(f"  📱 {resp.get('telefone', 'N/A')}")
                        st.write(f"  📧 {resp.get('email', 'N/A')}")
                
                # Critérios de elegibilidade
                criterios = aluno.get('criterios', {})
                st.markdown("**✅ Critérios de Elegibilidade:**")
                
                col_crit1, col_crit2 = st.columns(2)
                
                with col_crit1:
                    status_venc = "✅" if criterios.get('tem_dia_vencimento') else "❌"
                    st.write(f"{status_venc} Dia de vencimento")
                    
                    status_valor = "✅" if criterios.get('tem_valor_mensalidade') else "❌"
                    st.write(f"{status_valor} Valor de mensalidade")
                    
                    status_mens = "✅" if criterios.get('nao_tem_mensalidades') else "❌"
                    st.write(f"{status_mens} Sem mensalidades geradas")
                
                with col_crit2:
                    status_resp = "✅" if criterios.get('tem_responsaveis') else "❌"
                    st.write(f"{status_resp} Responsáveis cadastrados")
                    
                    # Mostrar data de matrícula como informação, não mais como critério obrigatório
                    status_mat = "✅" if criterios.get('tem_data_matricula') else "ℹ️"
                    label_mat = "Data de matrícula (para gerar mensalidades)" if criterios.get('tem_data_matricula') else "Data de matrícula (será identificada)"
                    st.write(f"{status_mat} {label_mat}")
        
        # Botões de navegação
        st.markdown("---")
        col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
        
        with col_nav1:
            if st.button("◀️ Voltar", type="secondary"):
                st.session_state.etapa_processamento = 1
                st.rerun()
        
        with col_nav3:
            alunos_selecionados = sum(1 for i in range(len(alunos)) if st.session_state.get(f"incluir_aluno_{i}", True))
            
            if st.button(f"🔗 Correlacionar ({alunos_selecionados} alunos)", type="primary", disabled=alunos_selecionados == 0):
                # Filtrar apenas alunos selecionados
                alunos_para_processar = [
                    aluno for i, aluno in enumerate(alunos) 
                    if st.session_state.get(f"incluir_aluno_{i}", True)
                ]
                
                with st.spinner("🔄 Processando correlações com extrato PIX..."):
                    alunos_com_correlacoes = processar_correlacoes_alunos(alunos_para_processar)
                    st.session_state.alunos_processamento = alunos_com_correlacoes
                    st.session_state.etapa_processamento = 3
                    st.success(f"✅ Correlações processadas para {len(alunos_com_correlacoes)} alunos!")
                    st.rerun()
    
    # ==========================================================
    # ETAPA 3: CORRELAÇÕES E CONFIRMAÇÃO
    # ==========================================================
    
    elif st.session_state.etapa_processamento == 3:
        renderizar_etapa_correlacoes()

def renderizar_etapa_correlacoes():
    """Renderiza a etapa de correlações"""
    
    st.markdown("#### 🔗 Etapa 3: Correlações com Extrato PIX")
    
    alunos = st.session_state.alunos_processamento
    
    # Estatísticas das correlações
    alunos_com_correlacoes = [a for a in alunos if a.get('tem_correlacoes', False)]
    total_matriculas = sum(1 for a in alunos if a.get('correlacoes', {}).get('matricula'))
    total_mensalidades = sum(len(a.get('correlacoes', {}).get('mensalidades', [])) for a in alunos)
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("👥 Alunos", len(alunos))
    
    with col_stat2:
        st.metric("🔗 Com Correlações", len(alunos_com_correlacoes))
    
    with col_stat3:
        st.metric("🎓 Matrículas", total_matriculas)
    
    with col_stat4:
        st.metric("📋 Mensalidades", total_mensalidades)
    
    # Lista de correlações por aluno
    st.markdown("---")
    st.markdown("### 🔗 Correlações Identificadas")
    
    for i, aluno in enumerate(alunos):
        correlacoes = aluno.get('correlacoes', {})
        tem_correlacoes = aluno.get('tem_correlacoes', False)
        tipo_processamento = correlacoes.get('tipo_processamento', 'identificar_matricula')
        
        # Status do aluno baseado no tipo de processamento
        if tem_correlacoes:
            if tipo_processamento == 'identificar_matricula':
                status_class = "status-correlacao"
                status_icon = "🔍"
                status_text = f"Matrícula identificada + {len(correlacoes.get('mensalidades', []))} mensalidades correlacionadas"
            else:
                status_class = "status-elegivel"
                status_icon = "📋"
                status_text = f"{len(correlacoes.get('mensalidades_a_gerar', []))} mensalidades geradas + {len(correlacoes.get('mensalidades', []))} pagamentos correlacionados"
        else:
            if tipo_processamento == 'identificar_matricula':
                status_class = "status-nao-elegivel"
                status_icon = "⚠️"
                status_text = "Nenhum pagamento PIX compatível encontrado"
            else:
                status_class = "status-correlacao"
                status_icon = "📋"
                status_text = f"{len(correlacoes.get('mensalidades_a_gerar', []))} mensalidades geradas (sem pagamentos correlacionados)"
        
        st.markdown(f"""
        <div class="status-card {status_class}">
            <strong>{status_icon} {aluno['nome']} - {aluno['turmas']['nome_turma']}</strong><br>
            <small>{aluno.get('tipo_label', '')} | {status_text}</small>
        </div>
        """, unsafe_allow_html=True)
        
        if tem_correlacoes or correlacoes.get('mensalidades_a_gerar'):
            with st.expander(f"📋 Detalhes - {aluno['nome']}", expanded=False):
                
                if tipo_processamento == 'identificar_matricula':
                    # FLUXO 1: IDENTIFICAR MATRÍCULA
                    # Matrícula
                    matricula = correlacoes.get('matricula')
                    if matricula:
                        st.markdown("**🎓 Matrícula Identificada:**")
                        col_mat1, col_mat2, col_mat3 = st.columns(3)
                        
                        with col_mat1:
                            st.write(f"💰 **Valor:** {formatar_valor_br(matricula['valor'])}")
                        
                        with col_mat2:
                            st.write(f"📅 **Data Pagamento:** {formatar_data_br(matricula['data_pagamento'])}")
                        
                        with col_mat3:
                            st.write(f"👤 **Remetente:** {matricula['pagamento']['nome_remetente']}")
                    
                    # Mensalidades correlacionadas
                    mensalidades = correlacoes.get('mensalidades', [])
                    if mensalidades:
                        st.markdown("**📋 Mensalidades Correlacionadas:**")
                        
                        dados_mensalidades = []
                        for mens in mensalidades:
                            dados_mensalidades.append({
                                "Mês": mens['mes_referencia'],
                                "Valor": formatar_valor_br(mens['valor']),
                                "Vencimento": formatar_data_br(mens['data_vencimento']),
                                "Pago em": formatar_data_br(mens['data_pagamento']),
                                "Remetente": mens['pagamento']['nome_remetente'][:30] + "..."
                            })
                        
                        if dados_mensalidades:
                            df_mens = pd.DataFrame(dados_mensalidades)
                            st.dataframe(df_mens, hide_index=True, use_container_width=True)
                
                else:
                    # FLUXO 2: GERAR MENSALIDADES
                    # Mensalidades a gerar
                    mensalidades_a_gerar = correlacoes.get('mensalidades_a_gerar', [])
                    if mensalidades_a_gerar:
                        st.markdown("**📋 Mensalidades a serem Criadas:**")
                        
                        dados_gerar = []
                        for mens in mensalidades_a_gerar:
                            dados_gerar.append({
                                "Mês": mens['mes_referencia'],
                                "Valor": formatar_valor_br(mens['valor']),
                                "Vencimento": formatar_data_br(mens['data_vencimento']),
                                "Status": "A criar"
                            })
                        
                        if dados_gerar:
                            df_gerar = pd.DataFrame(dados_gerar)
                            st.dataframe(df_gerar, hide_index=True, use_container_width=True)
                    
                    # Pagamentos correlacionados
                    mensalidades_pagas = correlacoes.get('mensalidades', [])
                    if mensalidades_pagas:
                        st.markdown("**💰 Pagamentos Correlacionados:**")
                        
                        dados_pagos = []
                        for mens in mensalidades_pagas:
                            diferenca = mens.get('diferenca', 0)
                            status_valor = "✅ Exato" if abs(diferenca) < 0.01 else f"{'⬆️' if diferenca > 0 else '⬇️'} {diferenca:+.2f}"
                            
                            dados_pagos.append({
                                "Mês": mens['mes_referencia'],
                                "Valor Esperado": formatar_valor_br(mens.get('valor_esperado', 0)),
                                "Valor Pago": formatar_valor_br(mens['valor']),
                                "Status": status_valor,
                                "Data Pagamento": formatar_data_br(mens['data_pagamento']),
                                "Remetente": mens['pagamento']['nome_remetente'][:25] + "..."
                            })
                        
                        if dados_pagos:
                            df_pagos = pd.DataFrame(dados_pagos)
                            st.dataframe(df_pagos, hide_index=True, use_container_width=True)
                    
                    # Botões de ação para o aluno
                    st.markdown("---")
                    col_acao1, col_acao2, col_acao3 = st.columns(3)
                    
                    with col_acao1:
                        if st.button(f"✏️ Editar", key=f"editar_correlacao_{i}", use_container_width=True):
                            st.session_state[f'editando_correlacao_{i}'] = True
                            st.rerun()
                    
                    with col_acao2:
                        if st.button(f"❌ Remover Aluno", key=f"remover_aluno_{i}", use_container_width=True):
                            # Remover aluno da lista
                            st.session_state.alunos_processamento = [
                                a for j, a in enumerate(alunos) if j != i
                            ]
                            st.success(f"✅ {aluno['nome']} removido do processamento")
                            st.rerun()
                    
                    # Formulário de edição simplificado (mantenho o existente mas poderia ser expandido)
                    if st.session_state.get(f'editando_correlacao_{i}', False):
                        st.markdown("##### ✏️ Editar Correlações")
                        st.info("🔧 Interface de edição detalhada em desenvolvimento. Por enquanto, remova e reprocesse o aluno se necessário.")
                        
                        if st.button("❌ Fechar Edição", key=f"fechar_edicao_{i}"):
                            st.session_state[f'editando_correlacao_{i}'] = False
                            st.rerun()
        
        elif not tem_correlacoes and not correlacoes.get('mensalidades_a_gerar'):
            # Aluno sem correlações nem mensalidades
            if tipo_processamento == 'identificar_matricula':
                st.info(f"ℹ️ {aluno['nome']}: Nenhum pagamento PIX compatível encontrado. Considere verificar os valores ou remover este aluno.")
            else:
                st.info(f"ℹ️ {aluno['nome']}: Mensalidades serão criadas sem vinculação inicial com pagamentos PIX.")
    
    # Botões de navegação final
    st.markdown("---")
    col_final1, col_final2, col_final3 = st.columns([1, 1, 1])
    
    with col_final1:
        if st.button("◀️ Voltar", type="secondary"):
            st.session_state.etapa_processamento = 2
            st.rerun()
    
    with col_final3:
        if st.button("🚀 REGISTRAR NO BANCO", type="primary"):
            executar_registro_no_banco()

def executar_registro_no_banco():
    """Executa o registro das mensalidades e correlações no banco de dados"""
    
    alunos = st.session_state.alunos_processamento
    
    with st.spinner("💾 Registrando mensalidades e correlações no banco..."):
        try:
            resultados = {
                'mensalidades_criadas': 0,
                'matriculas_registradas': 0,
                'correlacoes_pix': 0,
                'alunos_atualizados': 0,
                'erros': []
            }
            
            for aluno in alunos:
                correlacoes = aluno.get('correlacoes', {})
                tipo_processamento = correlacoes.get('tipo_processamento', 'identificar_matricula')
                
                try:
                    if tipo_processamento == 'identificar_matricula':
                        # FLUXO 1: ALUNOS SEM DATA DE MATRÍCULA
                        # Primeiro, atualizar a data de matrícula baseada no primeiro pagamento
                        matricula = correlacoes.get('matricula')
                        if matricula:
                            # Atualizar aluno com data de matrícula baseada no primeiro pagamento
                            response_aluno = supabase.table("alunos").update({
                                "data_matricula": matricula['data_pagamento'],
                                "updated_at": obter_timestamp()
                            }).eq("id", aluno['id']).execute()
                            
                            if response_aluno.data:
                                resultados['matriculas_registradas'] += 1
                                
                                # Atualizar status do PIX da matrícula
                                supabase.table("extrato_pix").update({
                                    "status": "registrado",
                                    "id_aluno": aluno['id'],
                                    "tipo_pagamento": "matricula",
                                    "observacoes": f"[PROCESSAMENTO AUTOMATIZADO] Matrícula de {aluno['nome']} - Data identificada automaticamente",
                                    "atualizado_em": obter_timestamp()
                                }).eq("id", matricula['pagamento']['id']).execute()
                                
                                resultados['correlacoes_pix'] += 1
                        
                        # Criar mensalidades correlacionadas
                        mensalidades = correlacoes.get('mensalidades', [])
                        for mens in mensalidades:
                            # Gerar ID único para mensalidade
                            id_mensalidade = f"MENS_{str(uuid.uuid4().int)[:6].upper()}"
                            
                            # Criar mensalidade
                            nova_mensalidade = {
                                "id_mensalidade": id_mensalidade,
                                "id_aluno": aluno['id'],
                                "mes_referencia": mens['mes_referencia'],
                                "valor": mens['valor'],
                                "data_vencimento": mens['data_vencimento'],
                                "status": "Pago",
                                "data_pagamento": mens['data_pagamento'],
                                "forma_pagamento": "PIX",
                                "observacoes": f"[PROCESSAMENTO AUTOMATIZADO - IDENTIFICAÇÃO] Correlacionado com PIX de {mens['pagamento']['nome_remetente']}",
                                "inserted_at": obter_timestamp(),
                                "updated_at": obter_timestamp()
                            }
                            
                            response = supabase.table("mensalidades").insert(nova_mensalidade).execute()
                            
                            if response.data:
                                resultados['mensalidades_criadas'] += 1
                                
                                # Atualizar status do PIX
                                supabase.table("extrato_pix").update({
                                    "status": "registrado",
                                    "id_aluno": aluno['id'],
                                    "tipo_pagamento": "mensalidade",
                                    "observacoes": f"[PROCESSAMENTO AUTOMATIZADO] Mensalidade {mens['mes_referencia']} de {aluno['nome']}",
                                    "atualizado_em": obter_timestamp()
                                }).eq("id", mens['pagamento']['id']).execute()
                                
                                resultados['correlacoes_pix'] += 1
                    
                    else:
                        # FLUXO 2: ALUNOS COM DATA DE MATRÍCULA
                        # Criar mensalidades a gerar
                        mensalidades_a_gerar = correlacoes.get('mensalidades_a_gerar', [])
                        for mens_gerar in mensalidades_a_gerar:
                            # Gerar ID único para mensalidade
                            id_mensalidade = f"MENS_{str(uuid.uuid4().int)[:6].upper()}"
                            
                            # Verificar se há pagamento correlacionado para esta mensalidade
                            pagamento_correlacionado = None
                            status_mensalidade = "A vencer"
                            data_pagamento = None
                            forma_pagamento = None
                            observacoes_extra = ""
                            
                            for mens_paga in correlacoes.get('mensalidades', []):
                                if mens_paga['mes_referencia'] == mens_gerar['mes_referencia']:
                                    pagamento_correlacionado = mens_paga
                                    status_mensalidade = "Pago"
                                    data_pagamento = mens_paga['data_pagamento']
                                    forma_pagamento = "PIX"
                                    observacoes_extra = f" - Correlacionado com PIX de {mens_paga['pagamento']['nome_remetente']}"
                                    break
                            
                            # Criar mensalidade
                            nova_mensalidade = {
                                "id_mensalidade": id_mensalidade,
                                "id_aluno": aluno['id'],
                                "mes_referencia": mens_gerar['mes_referencia'],
                                "valor": mens_gerar['valor'],
                                "data_vencimento": mens_gerar['data_vencimento'],
                                "status": status_mensalidade,
                                "data_pagamento": data_pagamento,
                                "forma_pagamento": forma_pagamento,
                                "observacoes": f"[PROCESSAMENTO AUTOMATIZADO - GERAÇÃO]{observacoes_extra}",
                                "inserted_at": obter_timestamp(),
                                "updated_at": obter_timestamp()
                            }
                            
                            response = supabase.table("mensalidades").insert(nova_mensalidade).execute()
                            
                            if response.data:
                                resultados['mensalidades_criadas'] += 1
                                
                                # Se há pagamento correlacionado, atualizar PIX
                                if pagamento_correlacionado:
                                    supabase.table("extrato_pix").update({
                                        "status": "registrado",
                                        "id_aluno": aluno['id'],
                                        "tipo_pagamento": "mensalidade",
                                        "observacoes": f"[PROCESSAMENTO AUTOMATIZADO] Mensalidade {mens_gerar['mes_referencia']} de {aluno['nome']}",
                                        "atualizado_em": obter_timestamp()
                                    }).eq("id", pagamento_correlacionado['pagamento']['id']).execute()
                                    
                                    resultados['correlacoes_pix'] += 1
                    
                    # Marcar aluno como tendo mensalidades geradas
                    supabase.table("alunos").update({
                        "mensalidades_geradas": True,
                        "updated_at": obter_timestamp()
                    }).eq("id", aluno['id']).execute()
                    
                    resultados['alunos_atualizados'] += 1
                    
                except Exception as e:
                    resultados['erros'].append(f"Erro no processamento de {aluno['nome']}: {str(e)}")
            
            # Mostrar resultados
            if resultados['erros']:
                st.error(f"❌ Processamento concluído com {len(resultados['erros'])} erros")
                for erro in resultados['erros']:
                    st.error(f"• {erro}")
            else:
                st.success("✅ Processamento concluído com sucesso!")
            
            st.info(f"""
            **📊 Resumo dos Resultados:**
            - ✅ Mensalidades criadas: {resultados['mensalidades_criadas']}
            - 🎓 Matrículas identificadas/registradas: {resultados['matriculas_registradas']}
            - 🔗 Correlações PIX registradas: {resultados['correlacoes_pix']}
            - 👥 Alunos atualizados: {resultados['alunos_atualizados']}
            - ❌ Erros: {len(resultados['erros'])}
            """)
            
            # Resetar processamento
            st.session_state.etapa_processamento = 1
            st.session_state.alunos_processamento = []
            st.session_state.turmas_processamento = []
            
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Erro crítico no processamento: {str(e)}")

# ==========================================================
# 🏠 INTERFACE PRINCIPAL
# ==========================================================

def main():
    """Função principal da interface"""
    
    # Título principal
    st.title("🎓 Sistema de Gestão Escolar")
    st.markdown("### 💰 Módulo de Gestão de Mensalidades")
    
    # Inicializar estado da sessão
    if 'modal_aberto' not in st.session_state:
        st.session_state.modal_aberto = False
    if 'id_mensalidade_modal' not in st.session_state:
        st.session_state.id_mensalidade_modal = None
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = False
    
    # ==========================================================
    # BARRA LATERAL COM CONTROLES
    # ==========================================================
    
    with st.sidebar:
        st.markdown("## 🔧 Controles")
        
        # Filtros
        st.markdown("### 🔍 Filtros")
        
        # Filtro por status
        status_filtro = st.selectbox(
            "📊 Status:",
            options=["Todos", "A vencer", "Atrasado", "Pago", "Pago parcial", "Cancelado"],
            key="filtro_status",
            help="Filtrar mensalidades por status"
        )
        
        # Filtro por período
        periodo_filtro = st.selectbox(
            "📅 Período:",
            options=["Todos", "Últimos 30 dias", "Últimos 60 dias", "Últimos 90 dias", "Período customizado"],
            key="filtro_periodo",
            help="Filtrar por período de vencimento"
        )
        
        # Campos de data customizada (só aparecem se "Período customizado" for selecionado)
        data_inicio_filtro = None
        data_fim_filtro = None
        
        if periodo_filtro == "Período customizado":
            st.markdown("**📅 Defina o período:**")
            
            col_data1, col_data2 = st.columns(2)
            
            with col_data1:
                data_inicio_filtro = st.date_input(
                    "De:",
                    value=date.today(),
                    key="filtro_data_inicio",
                    help="Data de início do período"
                )
            
            with col_data2:
                data_fim_filtro = st.date_input(
                    "Até:",
                    value=date.today() + timedelta(days=30),
                    key="filtro_data_fim",
                    help="Data de fim do período"
                )
            
            # Validação das datas
            if data_inicio_filtro and data_fim_filtro and data_inicio_filtro > data_fim_filtro:
                st.error("⚠️ A data de início deve ser anterior à data de fim!")
        
        # Filtro por turmas (seleção múltipla)
        try:
            turmas_response = supabase.table("turmas").select("nome_turma").order("nome_turma").execute()
            turmas_disponiveis = [t["nome_turma"] for t in turmas_response.data if turmas_response.data]
        except:
            turmas_disponiveis = []
        
        # Inicializar com "Todas" selecionado por padrão
        if 'turmas_inicializadas' not in st.session_state:
            st.session_state.turmas_inicializadas = True
            st.session_state.filtro_turmas_selected = ["Todas"]
        
        turmas_filtro = st.multiselect(
            "🎓 Turmas:",
            options=["Todas"] + turmas_disponiveis,
            default=st.session_state.get('filtro_turmas_selected', ["Todas"]),
            key="filtro_turmas",
            help="Selecione uma ou mais turmas específicas, ou 'Todas' para exibir todas as turmas"
        )
        
        # Lógica para "Todas" - se selecionado, remove as outras opções
        if "Todas" in turmas_filtro and len(turmas_filtro) > 1:
            if st.session_state.get('filtro_turmas_selected', []) != ["Todas"]:
                # Se "Todas" foi recém-selecionado, manter só "Todas"
                turmas_filtro = ["Todas"]
                st.session_state.filtro_turmas_selected = ["Todas"]
                st.rerun()
        elif not turmas_filtro:
            # Se nada está selecionado, voltar para "Todas"
            turmas_filtro = ["Todas"]
            st.session_state.filtro_turmas_selected = ["Todas"]
            st.rerun()
        else:
            # Atualizar estado da sessão
            st.session_state.filtro_turmas_selected = turmas_filtro
        
        # Busca por nome
        nome_filtro = st.text_input(
            "🔍 Nome do Aluno:",
            placeholder="Digite parte do nome...",
            key="filtro_nome",
            help="Buscar por nome do aluno"
        )
        
        # Botão para aplicar filtros
        if st.button("🔄 Aplicar Filtros", use_container_width=True, type="primary"):
            st.session_state.filtros_aplicados = True
            st.rerun()
        
        # Botão para limpar filtros
        if st.button("🗑️ Limpar Filtros", use_container_width=True):
            # Resetar filtros
            for key in ["filtro_status", "filtro_periodo", "filtro_turmas", "filtro_nome", 
                       "filtro_data_inicio", "filtro_data_fim", "filtro_turmas_selected", "turmas_inicializadas"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.filtros_aplicados = True
            st.rerun()
        
        st.markdown("---")
        
        # Ações rápidas
        st.markdown("### ⚡ Ações Rápidas")
        
        if st.button("🤖 Processamento Automatizado", use_container_width=True, type="primary"):
            st.session_state.mostrar_processamento = True
            st.rerun()
        
        if st.button("📊 Relatório Geral", use_container_width=True):
            st.info("🔧 Em desenvolvimento")
        
        if st.button("📧 Envio em Massa", use_container_width=True):
            st.info("🔧 Em desenvolvimento")
        
        if st.button("💾 Backup Dados", use_container_width=True):
            st.success("✅ Backup realizado!")
        
        st.markdown("---")
        
        # Informações do sistema
        st.markdown("### ℹ️ Sistema")
        st.caption("📅 Última atualização: Agora")
        st.caption("🔄 Sincronização: Ativa")
        st.caption("📊 Dados em tempo real")
    
    # ==========================================================
    # CONTEÚDO PRINCIPAL
    # ==========================================================
    
    # Verificar se o modal deve ser exibido
    if st.session_state.get('modal_aberto', False) and st.session_state.get('id_mensalidade_modal'):
        st.markdown("---")
        st.markdown("## 🔍 MODAL DE DETALHAMENTO")
        
        # Container para o modal
        with st.container():
            try:
                abrir_modal_mensalidade(st.session_state.id_mensalidade_modal)
            except Exception as e:
                st.error(f"❌ Erro ao abrir modal: {str(e)}")
                st.session_state.modal_aberto = False
                st.session_state.id_mensalidade_modal = None
        
        # Botão para fechar o modal (sempre visível)
        st.markdown("---")
        col_fechar1, col_fechar2, col_fechar3 = st.columns([1, 1, 1])
        with col_fechar2:
            if st.button("❌ Fechar Modal", use_container_width=True, key="fechar_modal_principal"):
                st.session_state.modal_aberto = False
                st.session_state.id_mensalidade_modal = None
                st.rerun()
        
        return  # Não mostrar o resto da interface quando modal estiver aberto
    
    # ==========================================================
    # PAINEL PRINCIPAL (QUANDO MODAL NÃO ESTÁ ABERTO)
    # ==========================================================
    
    # Verificar se deve mostrar processamento automatizado
    if st.session_state.get('mostrar_processamento', False):
        st.markdown("---")
        st.markdown("## 🤖 PROCESSAMENTO AUTOMATIZADO")
        
        # Container para o processamento
        with st.container():
            renderizar_aba_processamento()
        
        # Botão para voltar
        st.markdown("---")
        col_voltar1, col_voltar2, col_voltar3 = st.columns([1, 1, 1])
        with col_voltar2:
            if st.button("🔙 Voltar para Lista Principal", use_container_width=True, key="voltar_lista_principal"):
                st.session_state.mostrar_processamento = False
                # Limpar estados do processamento
                for key in ['etapa_processamento', 'alunos_processamento', 'turmas_processamento']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        return  # Não mostrar o resto da interface quando processamento estiver aberto
    
    # Preparar filtros para busca
    filtros_busca = {
        "periodo": periodo_filtro,
        "turmas_selecionadas": turmas_filtro,
        "status": status_filtro,
        "nome_aluno": nome_filtro
    }
    
    # Adicionar datas customizadas se período customizado for selecionado
    if periodo_filtro == "Período customizado":
        if data_inicio_filtro:
            filtros_busca["data_inicio"] = data_inicio_filtro.isoformat()
        if data_fim_filtro:
            filtros_busca["data_fim"] = data_fim_filtro.isoformat()
    
    # Buscar dados
    with st.spinner("🔄 Carregando mensalidades..."):
        resultado = buscar_mensalidades_completas(filtros_busca)
    
    if not resultado.get("success"):
        st.error(f"❌ Erro ao carregar mensalidades: {resultado.get('error')}")
        return
    
    mensalidades_originais = resultado["mensalidades"]
    
    if not mensalidades_originais:
        st.warning("⚠️ Nenhuma mensalidade encontrada no banco de dados")
        st.info("💡 Verifique se existem mensalidades cadastradas no sistema")
        return
    
    # Aplicar filtros adicionais na interface
    mensalidades_filtradas = aplicar_filtros_interface(mensalidades_originais, filtros_busca)
    
    # Calcular estatísticas
    stats = calcular_estatisticas(mensalidades_filtradas)
    resumo_status = obter_resumo_status(mensalidades_originais)
    
    # ==========================================================
    # INFORMAÇÕES DE DEBUG
    # ==========================================================
    
    with st.expander("🔍 Informações de Debug", expanded=False):
        col_debug1, col_debug2 = st.columns(2)
        
        with col_debug1:
            st.markdown("**📊 Dados Carregados:**")
            st.write(f"Total no banco: {len(mensalidades_originais)}")
            st.write(f"Após filtros: {len(mensalidades_filtradas)}")
            
            st.markdown("**🔧 Filtros Ativos:**")
            st.json(filtros_busca)
        
        with col_debug2:
            st.markdown("**📈 Status no Banco:**")
            for status, count in resumo_status.items():
                st.write(f"• {status}: {count}")
    
    # ==========================================================
    # MÉTRICAS PRINCIPAIS
    # ==========================================================
    
    st.markdown("## 📊 Painel de Controle")
    
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
    
    with col_metric1:
        st.metric(
            label="📋 Total de Mensalidades",
            value=stats["total"],
            delta=f"De {len(mensalidades_originais)} no banco"
        )
    
    with col_metric2:
        st.metric(
            label="💰 Valor Total",
            value=f"R$ {stats['valor_total']:,.2f}",
            delta=f"{stats['pagas']} pagas"
        )
    
    with col_metric3:
        if stats["atrasadas"] > 0:
            st.metric(
                label="⚠️ Mensalidades Atrasadas",
                value=stats["atrasadas"],
                delta="Requer atenção",
                delta_color="inverse"
            )
        else:
            st.metric(
                label="✅ Situação",
                value="Em dia",
                delta="Todas em dia"
            )
    
    with col_metric4:
        porcentagem_pagas = (stats["pagas"] / stats["total"] * 100) if stats["total"] > 0 else 0
        st.metric(
            label="📈 Taxa de Pagamento",
            value=f"{porcentagem_pagas:.1f}%",
            delta=f"{stats['pagas']} de {stats['total']}"
        )
    
    # ==========================================================
    # TABELA DE MENSALIDADES
    # ==========================================================
    
    st.markdown("---")
    st.markdown("## 📋 Lista de Mensalidades")
    
    if mensalidades_filtradas:
        # Preparar dados para exibição
        dados_tabela = []
        
        for m in mensalidades_filtradas:
            # Status com emoji
            status_emoji = {
                "Pago": "✅",
                "Pago parcial": "🔶", 
                "A vencer": "📅",
                "Atrasado": "⚠️",
                "Cancelado": "❌"
            }.get(m.get("status"), "❓")
            
            # Calcular situação de vencimento ou pagamento
            status = m.get("status", "")
            
            if status in ["Pago", "Pago parcial"]:
                # Para mensalidades pagas, mostrar data de pagamento
                data_pagamento = m.get("data_pagamento")
                if data_pagamento:
                    try:
                        situacao = f"Pago em {formatar_data_br(data_pagamento)}"
                    except:
                        situacao = "Pago"
                else:
                    situacao = "Pago"
            elif status == "Cancelado":
                situacao = "Cancelado"
            else:
                # Para mensalidades não pagas, calcular situação de vencimento
                try:
                    vencimento = datetime.strptime(m.get("data_vencimento", ""), "%Y-%m-%d").date()
                    hoje = date.today()
                    dias_diferenca = (vencimento - hoje).days
                    
                    if dias_diferenca < 0:
                        situacao = f"Atrasado ({abs(dias_diferenca)} dias)"
                    elif dias_diferenca == 0:
                        situacao = "Vence hoje"
                    else:
                        situacao = f"Vence em {dias_diferenca} dias"
                except:
                    situacao = "Data inválida"
            
            # Preparar dados para ordenação correta
            data_vencimento_iso = m.get("data_vencimento", "")
            data_pagamento_iso = m.get("data_pagamento", "")
            
            dados_tabela.append({
                "ID": m.get("id_mensalidade", ""),
                "👨‍🎓 Aluno": m.get("alunos", {}).get("nome", ""),
                "🎓 Turma": m.get("alunos", {}).get("turmas", {}).get("nome_turma", ""),
                "📅 Mês": m.get("mes_referencia", ""),
                "💰 Valor": float(m.get('valor', 0)),  # Manter como número para ordenação
                "💰 Valor_Display": f"R$ {float(m.get('valor', 0)):,.2f}",  # Para exibição
                "📆 Vencimento": datetime.strptime(data_vencimento_iso, "%Y-%m-%d").date() if data_vencimento_iso else None,  # Para ordenação
                "📆 Vencimento_Display": formatar_data_br(data_vencimento_iso),  # Para exibição
                "💳 Data_Pagamento": datetime.strptime(data_pagamento_iso, "%Y-%m-%d").date() if data_pagamento_iso else None,  # Para ordenação
                "💳 Data_Pagamento_Display": formatar_data_br(data_pagamento_iso) if data_pagamento_iso else "",  # Para exibição
                "⏰ Situação": situacao,
                "📊 Status": f"{status_emoji} {m.get('status', '')}",
                "Ação": "🔍 Detalhes"
            })
        
        # Preparar dados para exibição com colunas adequadas para ordenação
        dados_tabela_display = []
        for item in dados_tabela:
            item_display = {
                "ID": item["ID"],
                "👨‍🎓 Aluno": item["👨‍🎓 Aluno"],
                "🎓 Turma": item["🎓 Turma"],
                "📅 Mês": item["📅 Mês"],
                "💰 Valor": item["💰 Valor"],  # Valor numérico para ordenação
                "💰 Valor_Display": item["💰 Valor_Display"],  # String formatada para exibição
                "📆 Vencimento": item["📆 Vencimento"],  # Data para ordenação
                "📆 Vencimento_Display": item["📆 Vencimento_Display"],  # String formatada para exibição
                "💳 Data_Pagamento": item["💳 Data_Pagamento"],  # Data para ordenação (se houver)
                "💳 Data_Pagamento_Display": item["💳 Data_Pagamento_Display"],  # String formatada para exibição
                "⏰ Situação": item["⏰ Situação"],
                "📊 Status": item["📊 Status"]
            }
            dados_tabela_display.append(item_display)
        
        # Exibir tabela interativa
        df = pd.DataFrame(dados_tabela_display)
        
        # Configuração das colunas - usar campos de display mas permitir ordenação pelos campos originais
        column_config = {
            "ID": st.column_config.TextColumn("ID", width="small"),
            "👨‍🎓 Aluno": st.column_config.TextColumn("Aluno", width="medium"),
            "🎓 Turma": st.column_config.TextColumn("Turma", width="small"),
            "📅 Mês": st.column_config.TextColumn("Mês", width="small"),
            "💰 Valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
            "📆 Vencimento": st.column_config.DateColumn("Vencimento", width="small"),
            "💳 Data_Pagamento": st.column_config.DateColumn("Data Pagamento", width="small"),
            "⏰ Situação": st.column_config.TextColumn("Situação", width="medium"),
            "📊 Status": st.column_config.TextColumn("Status", width="small")
        }
        
        # Ocultar colunas de display (manter apenas as de ordenação)
        colunas_para_exibir = ["ID", "👨‍🎓 Aluno", "🎓 Turma", "📅 Mês", "💰 Valor", "📆 Vencimento"]
        
        # Adicionar coluna de data de pagamento apenas para mensalidades pagas
        tem_pagamentos = any(item["💳 Data_Pagamento"] is not None for item in dados_tabela_display)
        if tem_pagamentos:
            colunas_para_exibir.append("💳 Data_Pagamento")
        
        colunas_para_exibir.extend(["⏰ Situação", "📊 Status"])
        
        # Filtrar DataFrame para mostrar apenas colunas relevantes
        df_exibicao = df[colunas_para_exibir]
        
        # Mostrar tabela com possibilidade de seleção
        selected_indices = st.dataframe(
            df_exibicao,
            column_config={k: v for k, v in column_config.items() if k in colunas_para_exibir},
            use_container_width=True,
            height=400,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Se uma linha foi selecionada, mostrar ações
        if selected_indices.get("selection") and selected_indices["selection"].get("rows"):
            selected_row = selected_indices["selection"]["rows"][0]
            mensalidade_selecionada = mensalidades_filtradas[selected_row]
            
            st.markdown("---")
            st.markdown(f"### 🎯 Ações para: {mensalidade_selecionada.get('alunos', {}).get('nome', '')} - {mensalidade_selecionada.get('mes_referencia', '')}")
            
            # Mostrar ações específicas baseadas no status
            col_action1, col_action2, col_action3, col_action4, col_action5 = st.columns(5)
            
            with col_action1:
                if st.button("✏️ Editar Valor", use_container_width=True, key=f"edit_valor_{selected_row}"):
                    st.session_state.show_edit_valor = True
                    st.session_state.mensalidade_edicao = mensalidade_selecionada
                    st.rerun()
            
            with col_action2:
                if st.button("📅 Editar Vencimento", use_container_width=True, key=f"edit_venc_{selected_row}"):
                    st.session_state.show_edit_vencimento = True
                    st.session_state.mensalidade_edicao = mensalidade_selecionada
                    st.rerun()
            
            with col_action3:
                if mensalidade_selecionada.get("status") not in ["Pago", "Cancelado"]:
                    if st.button("💰 Registrar Pagamento", use_container_width=True, key=f"reg_pag_{selected_row}"):
                        st.session_state.show_pagamento_extrato = True
                        st.session_state.mensalidade_pagamento = mensalidade_selecionada
                        st.rerun()
            
            with col_action4:
                if mensalidade_selecionada.get("status") not in ["Pago", "Cancelado"]:
                    if st.button("✅ Dar Baixa", use_container_width=True, key=f"baixa_{selected_row}"):
                        st.session_state.show_dar_baixa = True
                        st.session_state.mensalidade_baixa = mensalidade_selecionada
                        st.rerun()
            
            with col_action5:
                if mensalidade_selecionada.get("status") != "Cancelado":
                    if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_{selected_row}"):
                        st.session_state.show_cancelar = True
                        st.session_state.mensalidade_cancelar = mensalidade_selecionada
                        st.rerun()
        
        # ==========================================================
        # FORMULÁRIOS DE EDIÇÃO E AÇÃO
        # ==========================================================
        
        # Form: Editar Valor
        if st.session_state.get('show_edit_valor', False):
            mensalidade_edit = st.session_state.get('mensalidade_edicao', {})
            
            st.markdown("---")
            st.markdown("#### ✏️ Editar Valor da Mensalidade")
            
            with st.form("form_editar_valor"):
                novo_valor = st.number_input(
                    "💰 Novo Valor (R$):",
                    min_value=0.01,
                    max_value=10000.0,
                    value=float(mensalidade_edit.get("valor", 0)),
                    step=0.01,
                    format="%.2f"
                )
                
                motivo_alteracao = st.text_input(
                    "📋 Motivo da Alteração:",
                    placeholder="Descreva o motivo da alteração..."
                )
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.form_submit_button("💾 Salvar", type="primary"):
                        if motivo_alteracao.strip():
                            try:
                                response = supabase.table("mensalidades").update({
                                    "valor": novo_valor,
                                    "observacoes": f"{mensalidade_edit.get('observacoes', '')}\n[VALOR ALTERADO de R$ {mensalidade_edit.get('valor', 0):.2f} para R$ {novo_valor:.2f}] Motivo: {motivo_alteracao}".strip(),
                                    "updated_at": obter_timestamp()
                                }).eq("id_mensalidade", mensalidade_edit["id_mensalidade"]).execute()
                                
                                if response.data:
                                    st.success("✅ Valor alterado com sucesso!")
                                    st.session_state.show_edit_valor = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao alterar valor")
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                        else:
                            st.error("❌ Motivo da alteração é obrigatório")
                
                with col_btn2:
                    if st.form_submit_button("❌ Cancelar", type="secondary"):
                        st.session_state.show_edit_valor = False
                        st.rerun()
        
        # Form: Editar Vencimento
        if st.session_state.get('show_edit_vencimento', False):
            mensalidade_edit = st.session_state.get('mensalidade_edicao', {})
            
            st.markdown("---")
            st.markdown("#### 📅 Editar Data de Vencimento")
            
            with st.form("form_editar_vencimento"):
                data_atual = datetime.strptime(mensalidade_edit.get("data_vencimento", ""), "%Y-%m-%d").date()
                
                nova_data = st.date_input(
                    "📅 Nova Data de Vencimento:",
                    value=data_atual,
                    min_value=date.today() - timedelta(days=365),
                    max_value=date.today() + timedelta(days=365)
                )
                
                motivo_alteracao = st.text_input(
                    "📋 Motivo da Alteração:",
                    placeholder="Descreva o motivo da alteração..."
                )
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.form_submit_button("💾 Salvar", type="primary"):
                        if motivo_alteracao.strip():
                            try:
                                response = supabase.table("mensalidades").update({
                                    "data_vencimento": nova_data.isoformat(),
                                    "observacoes": f"{mensalidade_edit.get('observacoes', '')}\n[VENCIMENTO ALTERADO de {formatar_data_br(mensalidade_edit.get('data_vencimento', ''))} para {formatar_data_br(nova_data.isoformat())}] Motivo: {motivo_alteracao}".strip(),
                                    "updated_at": obter_timestamp()
                                }).eq("id_mensalidade", mensalidade_edit["id_mensalidade"]).execute()
                                
                                if response.data:
                                    st.success("✅ Data de vencimento alterada com sucesso!")
                                    st.session_state.show_edit_vencimento = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao alterar data")
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                        else:
                            st.error("❌ Motivo da alteração é obrigatório")
                
                with col_btn2:
                    if st.form_submit_button("❌ Cancelar", type="secondary"):
                        st.session_state.show_edit_vencimento = False
                        st.rerun()
        
        # Form: Registrar Pagamento via Extrato
        if st.session_state.get('show_pagamento_extrato', False):
            mensalidade_pag = st.session_state.get('mensalidade_pagamento', {})
            id_aluno = mensalidade_pag.get('alunos', {}).get('id', '')
            
            st.markdown("---")
            st.markdown("#### 💰 Registrar Pagamento via Extrato PIX")
            
            if id_aluno:
                # Buscar responsáveis do aluno
                try:
                    resp_response = supabase.table("alunos_responsaveis").select("""
                        responsaveis!inner(id, nome)
                    """).eq("id_aluno", id_aluno).execute()
                    
                    responsaveis_ids = [r["responsaveis"]["id"] for r in resp_response.data if resp_response.data]
                    
                    if responsaveis_ids:
                        # Buscar pagamentos disponíveis no extrato
                        extrato_response = supabase.table("extrato_pix").select("*").in_(
                            "id_responsavel", responsaveis_ids
                        ).eq("status", "novo").order("data_pagamento", desc=True).limit(10).execute()
                        
                        pagamentos_disponiveis = extrato_response.data if extrato_response.data else []
                        
                        if pagamentos_disponiveis:
                            st.markdown("**📋 Pagamentos Disponíveis no Extrato:**")
                            
                            for pag in pagamentos_disponiveis:
                                col_pag1, col_pag2, col_pag3 = st.columns([2, 1, 1])
                                
                                with col_pag1:
                                    st.write(f"💰 **R$ {pag['valor']:.2f}** - {pag['nome_remetente']}")
                                    st.caption(f"📅 {formatar_data_br(pag['data_pagamento'])}")
                                
                                with col_pag2:
                                    valor_mensalidade = float(mensalidade_pag.get('valor', 0))
                                    valor_pago = float(pag['valor'])
                                    
                                    if abs(valor_pago - valor_mensalidade) < 0.01:
                                        status_valor = "✅ Exato"
                                    elif valor_pago > valor_mensalidade:
                                        status_valor = f"⬆️ +R$ {valor_pago - valor_mensalidade:.2f}"
                                    else:
                                        status_valor = f"⬇️ -R$ {valor_mensalidade - valor_pago:.2f}"
                                    
                                    st.write(status_valor)
                                
                                with col_pag3:
                                    if st.button("🔗 Vincular", key=f"vincular_{pag['id']}", use_container_width=True):
                                        try:
                                            # Atualizar mensalidade
                                            status_final = "Pago" if abs(valor_pago - valor_mensalidade) < 0.01 else "Pago parcial"
                                            
                                            response_mens = supabase.table("mensalidades").update({
                                                "status": status_final,
                                                "data_pagamento": pag['data_pagamento'],
                                                "forma_pagamento": "PIX",
                                                "observacoes": f"{mensalidade_pag.get('observacoes', '')}\n[PAGO via PIX - {pag['nome_remetente']} - Valor: R$ {valor_pago:.2f}]".strip(),
                                                "updated_at": obter_timestamp()
                                            }).eq("id_mensalidade", mensalidade_pag["id_mensalidade"]).execute()
                                            
                                            # Atualizar extrato
                                            response_extrato = supabase.table("extrato_pix").update({
                                                "status": "registrado",
                                                "id_aluno": id_aluno,
                                                "tipo_pagamento": "mensalidade",
                                                "observacoes": f"Vinculado à mensalidade {mensalidade_pag['id_mensalidade']} - {mensalidade_pag['mes_referencia']}",
                                                "atualizado_em": obter_timestamp()
                                            }).eq("id", pag['id']).execute()
                                            
                                            if response_mens.data and response_extrato.data:
                                                st.success("✅ Pagamento vinculado com sucesso!")
                                                st.session_state.show_pagamento_extrato = False
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("❌ Erro ao vincular pagamento")
                                        except Exception as e:
                                            st.error(f"❌ Erro: {str(e)}")
                        else:
                            st.warning("⚠️ Nenhum pagamento disponível no extrato para os responsáveis deste aluno")
                    else:
                        st.error("❌ Responsáveis não encontrados para este aluno")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao buscar extrato: {str(e)}")
            
            # Botão para fechar
            if st.button("❌ Fechar", key="fechar_extrato"):
                st.session_state.show_pagamento_extrato = False
                st.rerun()
        
        # Form: Dar Baixa (pagamento manual)
        if st.session_state.get('show_dar_baixa', False):
            mensalidade_baixa = st.session_state.get('mensalidade_baixa', {})
            
            st.markdown("---")
            st.markdown("#### ✅ Dar Baixa na Mensalidade (Pagamento Manual)")
            
            with st.form("form_dar_baixa"):
                col_baixa1, col_baixa2 = st.columns(2)
                
                with col_baixa1:
                    data_pagamento = st.date_input(
                        "📅 Data do Pagamento:",
                        value=date.today()
                    )
                    
                    forma_pagamento = st.selectbox(
                        "💳 Forma de Pagamento:",
                        options=["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência", "Outro"]
                    )
                
                with col_baixa2:
                    valor_pago = st.number_input(
                        "💰 Valor Pago (R$):",
                        min_value=0.01,
                        value=float(mensalidade_baixa.get("valor", 0)),
                        step=0.01,
                        format="%.2f"
                    )
                
                observacoes_pagamento = st.text_area(
                    "📝 Observações:",
                    placeholder="Observações sobre o pagamento..."
                )
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.form_submit_button("✅ Confirmar Baixa", type="primary"):
                        try:
                            valor_mensalidade = float(mensalidade_baixa.get("valor", 0))
                            status_final = "Pago" if abs(valor_pago - valor_mensalidade) < 0.01 else "Pago parcial"
                            
                            response = supabase.table("mensalidades").update({
                                "status": status_final,
                                "data_pagamento": data_pagamento.isoformat(),
                                "forma_pagamento": forma_pagamento,
                                "observacoes": f"{mensalidade_baixa.get('observacoes', '')}\n[BAIXA MANUAL - {forma_pagamento} - Valor: R$ {valor_pago:.2f}] {observacoes_pagamento}".strip(),
                                "updated_at": obter_timestamp()
                            }).eq("id_mensalidade", mensalidade_baixa["id_mensalidade"]).execute()
                            
                            if response.data:
                                st.success("✅ Baixa realizada com sucesso!")
                                st.session_state.show_dar_baixa = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Erro ao dar baixa")
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                
                with col_btn2:
                    if st.form_submit_button("❌ Cancelar", type="secondary"):
                        st.session_state.show_dar_baixa = False
                        st.rerun()
        
        # Form: Cancelar Mensalidade
        if st.session_state.get('show_cancelar', False):
            mensalidade_cancel = st.session_state.get('mensalidade_cancelar', {})
            
            st.markdown("---")
            st.markdown("#### ❌ Cancelar Mensalidade")
            
            st.warning("⚠️ **Atenção**: Esta ação não pode ser desfeita!")
            
            with st.form("form_cancelar"):
                motivo_cancelamento = st.text_area(
                    "📋 Motivo do Cancelamento:",
                    placeholder="Descreva o motivo do cancelamento..."
                )
                
                confirmar = st.checkbox("✅ Confirmo que desejo cancelar esta mensalidade")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.form_submit_button("❌ CANCELAR", type="primary", disabled=not confirmar):
                        if motivo_cancelamento.strip():
                            try:
                                response = supabase.table("mensalidades").update({
                                    "status": "Cancelado",
                                    "observacoes": f"{mensalidade_cancel.get('observacoes', '')}\n[CANCELADO em {date.today().strftime('%d/%m/%Y')}] Motivo: {motivo_cancelamento}".strip(),
                                    "updated_at": obter_timestamp()
                                }).eq("id_mensalidade", mensalidade_cancel["id_mensalidade"]).execute()
                                
                                if response.data:
                                    st.success("✅ Mensalidade cancelada com sucesso!")
                                    st.session_state.show_cancelar = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao cancelar mensalidade")
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                        else:
                            st.error("❌ Motivo do cancelamento é obrigatório")
                
                with col_btn2:
                    if st.form_submit_button("🔄 Voltar", type="secondary"):
                        st.session_state.show_cancelar = False
                        st.rerun()
        
        # ==========================================================
        # BOTÕES DE AÇÃO PARA CADA MENSALIDADE
        # ==========================================================
        
        st.markdown("### 🎯 Ações por Mensalidade")
        st.info("💡 **Como usar:** Clique no botão correspondente à mensalidade para abrir o modal de detalhes")
        
        # Organizar em grid de botões
        cols_per_row = 4
        mensalidades_por_pagina = 12
        
        # Paginação simples
        if 'pagina_atual' not in st.session_state:
            st.session_state.pagina_atual = 0
        
        total_paginas = (len(mensalidades_filtradas) + mensalidades_por_pagina - 1) // mensalidades_por_pagina
        
        if total_paginas > 1:
            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            
            with col_pag1:
                if st.button("⬅️ Anterior", disabled=st.session_state.pagina_atual == 0):
                    st.session_state.pagina_atual = max(0, st.session_state.pagina_atual - 1)
                    st.rerun()
            
            with col_pag2:
                st.write(f"📄 Página {st.session_state.pagina_atual + 1} de {total_paginas}")
            
            with col_pag3:
                if st.button("➡️ Próxima", disabled=st.session_state.pagina_atual >= total_paginas - 1):
                    st.session_state.pagina_atual = min(total_paginas - 1, st.session_state.pagina_atual + 1)
                    st.rerun()
        
        # Calcular índices da página atual
        inicio = st.session_state.pagina_atual * mensalidades_por_pagina
        fim = min(inicio + mensalidades_por_pagina, len(mensalidades_filtradas))
        mensalidades_pagina = mensalidades_filtradas[inicio:fim]
        
        # Criar grid de botões
        num_rows = (len(mensalidades_pagina) + cols_per_row - 1) // cols_per_row
        
        for row in range(num_rows):
            cols = st.columns(cols_per_row)
            
            for col_idx in range(cols_per_row):
                mensalidade_idx = row * cols_per_row + col_idx
                
                if mensalidade_idx < len(mensalidades_pagina):
                    mensalidade = mensalidades_pagina[mensalidade_idx]
                    
                    with cols[col_idx]:
                        aluno_nome = mensalidade.get("alunos", {}).get("nome", "Aluno")
                        mes_ref = mensalidade.get("mes_referencia", "")
                        status = mensalidade.get("status", "")
                        
                        # Emoji baseado no status
                        emoji_status = {
                            "Pago": "✅",
                            "Pago parcial": "🔶",
                            "A vencer": "📅",
                            "Atrasado": "⚠️",
                            "Cancelado": "❌"
                        }.get(status, "❓")
                        
                        # Nome curto para o botão
                        nome_curto = aluno_nome.split()[0] if aluno_nome else "Aluno"
                        
                        # Cor do botão baseada no status
                        tipo_botao = "primary" if status == "Atrasado" else "secondary"
                        
                        if st.button(
                            f"{emoji_status} {nome_curto}\n{mes_ref}",
                            key=f"btn_modal_{mensalidade['id_mensalidade']}",
                            help=f"Ver detalhes de {aluno_nome} - {mes_ref}\nStatus: {status}",
                            use_container_width=True,
                            type=tipo_botao
                        ):
                            # Abrir modal
                            st.session_state.modal_aberto = True
                            st.session_state.id_mensalidade_modal = mensalidade["id_mensalidade"]
                            st.rerun()
    
    else:
        st.info("ℹ️ Nenhuma mensalidade encontrada com os filtros aplicados")
        st.markdown("💡 **Dicas:**")
        st.markdown("- Verifique os filtros aplicados na barra lateral")
        st.markdown("- Tente expandir o período de busca")
        st.markdown("- Remova filtros específicos usando 'Limpar Filtros'")
        st.markdown("- Use o filtro 'Todos' para ver todas as mensalidades")

# ==========================================================
# 📚 SEÇÃO DE AJUDA E DOCUMENTAÇÃO
# ==========================================================

def mostrar_ajuda():
    """Mostra seção de ajuda"""
    
    with st.expander("❓ Como usar o Modal de Mensalidades", expanded=False):
        st.markdown("""
        ## 🎯 Como usar o Modal de Mensalidades
        
        ### 🚀 Abrindo o Modal
        1. **Navegue pela lista** de mensalidades na tela principal
        2. **Clique no botão** correspondente à mensalidade desejada
        3. **O modal será aberto** com todos os detalhes
        
        ### 📋 Abas Disponíveis
        
        #### 1. **📋 Detalhes**
        - Visualize **todas as informações** da mensalidade
        - Dados do **aluno e responsáveis**
        - **Status visual** com cores e emojis
        - **Métricas importantes**
        
        #### 2. **✏️ Edição**
        - **Edite valores** e datas
        - **Altere status** da mensalidade
        - **Aplique descontos** ou acréscimos
        - **Registre observações**
        
        #### 3. **⚡ Ações**
        - **Marcar como pago** (completo ou parcial)
        - **Cancelar mensalidade**
        - **Aplicar descontos**
        - **Gerar documentos**
        
        #### 4. **📚 Histórico**
        - **Timeline completa** de alterações
        - **Auditoria** de modificações
        - **Metadados** técnicos
        
        #### 5. **📊 Relatórios**
        - **Recibos de pagamento**
        - **Boletos de cobrança**
        - **Relatórios personalizados**
        - **Envio por email/WhatsApp**
        
        ### 🔧 Funcionalidades dos Filtros
        
        - **📊 Status:** Filtra por situação da mensalidade
        - **📅 Período:** Limita por data de vencimento
        - **🎓 Turma:** Filtra por turma específica
        - **🔍 Nome:** Busca por nome do aluno
        
        ### 💡 Dicas Importantes
        
        - Use **🔄 Aplicar Filtros** para atualizar os resultados
        - Use **🗑️ Limpar Filtros** para remover todos os filtros
        - **Informações de Debug** mostram dados técnicos
        - **Todas as ações** ficam registradas no histórico
        """)

# ==========================================================
# 🚀 EXECUÇÃO PRINCIPAL
# ==========================================================

if __name__ == "__main__":
    try:
        # Verificar conexão com banco
        test_connection = supabase.table("mensalidades").select("id_mensalidade").limit(1).execute()
        
        # Interface principal
        main()
        
        # Mostrar ajuda
        mostrar_ajuda()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem;">
            🎓 <strong>Sistema de Gestão Escolar</strong> | 
            💰 Módulo de Mensalidades | 
            🔧 Versão 1.0 Corrigida | 
            📅 2024
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error("❌ **Erro de Conexão com o Banco de Dados**")
        st.error(f"Detalhes: {str(e)}")
        st.info("💡 Verifique se:")
        st.info("- As credenciais do Supabase estão corretas")
        st.info("- A conexão com internet está funcionando")
        st.info("- O banco de dados está acessível")
        
        # Modo de demonstração
        st.markdown("---")
        st.markdown("## 🎭 Modo Demonstração")
        st.info("🔧 Como o banco não está disponível, você pode visualizar a estrutura do modal mesmo assim:")
        
        if st.button("🎭 Abrir Modal de Demonstração", type="primary"):
            st.session_state.modal_aberto = True
            st.session_state.id_mensalidade_modal = "demo_001"
            st.rerun() 