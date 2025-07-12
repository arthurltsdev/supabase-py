#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💰 SISTEMA INTEGRADO DE GESTÃO DE MENSALIDADES
===============================================

Módulo centralizado para gerenciar mensalidades de forma completa e profissional.
Consolida todas as funcionalidades do sistema em uma interface unificada.

Autor: Sistema de Gestão Escolar
Versão: 2.0 - Integração Completa
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import json
import uuid

# Importações do sistema
from models.base import (
    supabase, formatar_data_br, formatar_valor_br, obter_timestamp,
    gerar_id_mensalidade, MensalidadeSchema
)

# ==========================================================
# 🔧 FUNÇÕES PRINCIPAIS DE MENSALIDADES
# ==========================================================

def buscar_mensalidade_completa(id_mensalidade: str) -> Dict:
    """
    Busca dados completos de uma mensalidade incluindo aluno e responsáveis
    
    Args:
        id_mensalidade: ID da mensalidade
        
    Returns:
        Dict: Dados completos ou erro
    """
    try:
        response = supabase.table("mensalidades").select("""
            *,
            alunos!inner(
                id, nome, turno, valor_mensalidade, data_matricula,
                turmas!inner(nome_turma)
            )
        """).eq("id_mensalidade", id_mensalidade).execute()
        
        if not response.data:
            return {"success": False, "error": "Mensalidade não encontrada"}
        
        mensalidade = response.data[0]
        
        # Buscar responsáveis do aluno
        id_aluno = mensalidade["alunos"]["id"]
        resp_response = supabase.table("alunos_responsaveis").select("""
            responsaveis!inner(id, nome, telefone, email, cpf),
            tipo_relacao, responsavel_financeiro
        """).eq("id_aluno", id_aluno).execute()
        
        responsaveis = []
        responsavel_financeiro = None
        
        for vinculo in resp_response.data:
            resp_data = vinculo["responsaveis"]
            resp_data["tipo_relacao"] = vinculo["tipo_relacao"]
            resp_data["responsavel_financeiro"] = vinculo["responsavel_financeiro"]
            responsaveis.append(resp_data)
            
            if vinculo["responsavel_financeiro"]:
                responsavel_financeiro = resp_data
        
        # Buscar pagamentos relacionados
        pag_response = supabase.table("pagamentos").select("""
            id_pagamento, data_pagamento, valor, forma_pagamento, descricao,
            responsaveis(nome)
        """).eq("id_aluno", id_aluno).eq("tipo_pagamento", "mensalidade").execute()
        
        pagamentos = pag_response.data if pag_response.data else []
        
        # Calcular status real
        status_info = calcular_status_mensalidade(
            mensalidade["data_vencimento"], 
            mensalidade["status"],
            mensalidade.get("data_pagamento")
        )
        
        return {
            "success": True,
            "mensalidade": {**mensalidade, **status_info},
            "responsaveis": responsaveis,
            "responsavel_financeiro": responsavel_financeiro,
            "pagamentos": pagamentos
        }
        
    except Exception as e:
        return {"success": False, "error": f"Erro ao buscar mensalidade: {str(e)}"}

def calcular_status_mensalidade(data_vencimento: str, status_atual: str, data_pagamento: str = None) -> Dict:
    """
    Calcula status real da mensalidade baseado na data atual
    
    Args:
        data_vencimento: Data de vencimento (YYYY-MM-DD)
        status_atual: Status atual no banco
        data_pagamento: Data de pagamento se houver
        
    Returns:
        Dict: Status calculado com cores e emojis
    """
    try:
        data_hoje = date.today()
        vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
        
        if status_atual in ["Pago", "Pago parcial"]:
            return {
                "status_real": status_atual,
                "cor_status": "success" if status_atual == "Pago" else "warning",
                "emoji_status": "✅" if status_atual == "Pago" else "🔶",
                "dias_situacao": 0,
                "situacao_texto": "Pagamento realizado"
            }
        elif status_atual == "Cancelado":
            return {
                "status_real": "Cancelado",
                "cor_status": "secondary",
                "emoji_status": "❌",
                "dias_situacao": 0,
                "situacao_texto": "Mensalidade cancelada"
            }
        elif vencimento < data_hoje:
            dias_atraso = (data_hoje - vencimento).days
            return {
                "status_real": "Atrasado",
                "cor_status": "error",
                "emoji_status": "⚠️",
                "dias_situacao": dias_atraso,
                "situacao_texto": f"Atrasado há {dias_atraso} dia{'s' if dias_atraso > 1 else ''}"
            }
        else:
            dias_restantes = (vencimento - data_hoje).days
            if dias_restantes == 0:
                return {
                    "status_real": "Vence hoje",
                    "cor_status": "warning",
                    "emoji_status": "🔥",
                    "dias_situacao": 0,
                    "situacao_texto": "Vence hoje"
                }
            else:
                return {
                    "status_real": "A vencer",
                    "cor_status": "info",
                    "emoji_status": "📅",
                    "dias_situacao": dias_restantes,
                    "situacao_texto": f"Vence em {dias_restantes} dia{'s' if dias_restantes > 1 else ''}"
                }
                
    except Exception:
        return {
            "status_real": status_atual,
            "cor_status": "secondary",
            "emoji_status": "❓",
            "dias_situacao": 0,
            "situacao_texto": "Status indefinido"
        }

def listar_mensalidades_aluno_completas(id_aluno: str, incluir_canceladas: bool = False) -> Dict:
    """
    Lista mensalidades de um aluno com informações completas
    
    Args:
        id_aluno: ID do aluno
        incluir_canceladas: Se deve incluir mensalidades canceladas
        
    Returns:
        Dict: Lista de mensalidades com estatísticas
    """
    try:
        # Query base
        query = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, 
            status, data_pagamento, observacoes
        """).eq("id_aluno", id_aluno)
        
        if not incluir_canceladas:
            query = query.neq("status", "Cancelado")
        
        response = query.order("data_vencimento", desc=True).execute()
        
        mensalidades = []
        estatisticas = {
            "total": 0,
            "pagas": 0,
            "pendentes": 0,
            "atrasadas": 0,
            "canceladas": 0,
            "valor_total": 0,
            "valor_pago": 0,
            "valor_pendente": 0
        }
        
        for mens in response.data:
            # Calcular status
            status_info = calcular_status_mensalidade(
                mens["data_vencimento"], 
                mens["status"],
                mens.get("data_pagamento")
            )
            
            # Adicionar informações calculadas
            mensalidade_completa = {
                **mens,
                **status_info,
                "valor_formatado": formatar_valor_br(mens["valor"]),
                "data_vencimento_formatada": formatar_data_br(mens["data_vencimento"])
            }
            
            mensalidades.append(mensalidade_completa)
            
            # Atualizar estatísticas
            estatisticas["total"] += 1
            estatisticas["valor_total"] += mens["valor"]
            
            if mens["status"] in ["Pago", "Pago parcial"]:
                estatisticas["pagas"] += 1
                estatisticas["valor_pago"] += mens["valor"]
            elif mens["status"] == "Cancelado":
                estatisticas["canceladas"] += 1
            elif status_info["status_real"] == "Atrasado":
                estatisticas["atrasadas"] += 1
                estatisticas["valor_pendente"] += mens["valor"]
            else:
                estatisticas["pendentes"] += 1
                estatisticas["valor_pendente"] += mens["valor"]
        
        return {
            "success": True,
            "mensalidades": mensalidades,
            "estatisticas": estatisticas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def gerar_mensalidades_aluno_avancado(
    id_aluno: str, 
    tipo_geracao: str = "automatico",
    **kwargs
) -> Dict:
    """
    Gera mensalidades para um aluno com opções avançadas
    
    Args:
        id_aluno: ID do aluno
        tipo_geracao: "automatico", "manual" ou "personalizado"
        **kwargs: Parâmetros específicos para cada tipo
        
    Returns:
        Dict: Resultado da geração
    """
    try:
        # Buscar dados do aluno
        aluno_response = supabase.table("alunos").select("""
            id, nome, data_matricula, dia_vencimento, valor_mensalidade, 
            mensalidades_geradas, turmas(nome_turma)
        """).eq("id", id_aluno).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": "Aluno não encontrado"}
        
        aluno = aluno_response.data[0]
        
        # Validações básicas
        if aluno.get("mensalidades_geradas"):
            return {"success": False, "error": "Aluno já possui mensalidades geradas"}
        
        if not aluno.get("valor_mensalidade") or float(aluno["valor_mensalidade"]) <= 0:
            return {"success": False, "error": "Valor da mensalidade não configurado"}
        
        if not aluno.get("dia_vencimento"):
            return {"success": False, "error": "Dia de vencimento não configurado"}
        
        # Buscar responsável financeiro
        resp_response = supabase.table("alunos_responsaveis").select("""
            responsaveis(id, nome)
        """).eq("id_aluno", id_aluno).eq("responsavel_financeiro", True).execute()
        
        id_responsavel_financeiro = None
        if resp_response.data:
            id_responsavel_financeiro = resp_response.data[0]["responsaveis"]["id"]
        
        # Gerar mensalidades baseado no tipo
        mensalidades_para_criar = []
        
        if tipo_geracao == "automatico":
            mensalidades_para_criar = _gerar_mensalidades_automatico(aluno)
        elif tipo_geracao == "manual":
            mensalidades_para_criar = _gerar_mensalidades_manual(aluno, kwargs)
        elif tipo_geracao == "personalizado":
            mensalidades_para_criar = _gerar_mensalidades_personalizado(aluno, kwargs)
        
        if not mensalidades_para_criar:
            return {"success": False, "error": "Nenhuma mensalidade foi gerada"}
        
        # Criar mensalidades no banco
        mensalidades_criadas = []
        
        for mens_data in mensalidades_para_criar:
            id_mensalidade = gerar_id_mensalidade()
            
            dados_mensalidade = {
                "id_mensalidade": id_mensalidade,
                "id_aluno": id_aluno,
                "id_responsavel": id_responsavel_financeiro,
                "mes_referencia": mens_data["mes_referencia"],
                "valor": float(mens_data["valor"]),
                "data_vencimento": mens_data["data_vencimento"],
                "status": "A vencer",
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }
            
            response = supabase.table("mensalidades").insert(dados_mensalidade).execute()
            
            if response.data:
                mensalidades_criadas.append(response.data[0])
            else:
                # Reverter criações em caso de erro
                for mens_criada in mensalidades_criadas:
                    supabase.table("mensalidades").delete().eq(
                        "id_mensalidade", mens_criada["id_mensalidade"]
                    ).execute()
                
                return {
                    "success": False, 
                    "error": f"Erro ao criar mensalidade {mens_data['mes_referencia']}"
                }
        
        # Marcar aluno como tendo mensalidades geradas
        supabase.table("alunos").update({
            "mensalidades_geradas": True,
            "updated_at": obter_timestamp()
        }).eq("id", id_aluno).execute()
        
        return {
            "success": True,
            "mensalidades_criadas": len(mensalidades_criadas),
            "tipo_geracao": tipo_geracao,
            "valor_total": sum(m["valor"] for m in mensalidades_para_criar),
            "periodo": f"{mensalidades_para_criar[0]['mes_referencia']} a {mensalidades_para_criar[-1]['mes_referencia']}",
            "mensalidades": mensalidades_criadas
        }
        
    except Exception as e:
        return {"success": False, "error": f"Erro na geração: {str(e)}"}

# ==========================================================
# 🔧 FUNÇÕES AUXILIARES DE GERAÇÃO
# ==========================================================

def _gerar_mensalidades_automatico(aluno: Dict) -> List[Dict]:
    """Gera mensalidades automaticamente baseado na data de matrícula"""
    mensalidades = []
    
    if not aluno.get("data_matricula"):
        return mensalidades
    
    try:
        from datetime import datetime
        
        data_matricula = datetime.strptime(aluno["data_matricula"], "%Y-%m-%d").date()
        dia_vencimento = int(aluno["dia_vencimento"])
        valor = float(aluno["valor_mensalidade"])
        
        # Determinar período de geração (do mês seguinte à matrícula até dezembro)
        ano_matricula = data_matricula.year
        mes_inicio = data_matricula.month + 1
        
        # Se matrícula foi em dezembro, começar em fevereiro do próximo ano
        if mes_inicio > 12:
            mes_inicio = 2
            ano_matricula += 1
        
        # Gerar até dezembro
        nomes_meses = [
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        for mes in range(mes_inicio, 13):
            try:
                data_vencimento = datetime(ano_matricula, mes, dia_vencimento)
                
                mensalidades.append({
                    "mes_referencia": f"{nomes_meses[mes]}/{ano_matricula}",
                    "valor": valor,
                    "data_vencimento": data_vencimento.strftime("%Y-%m-%d")
                })
            except ValueError:
                # Dia inválido (ex: 31 de fevereiro), usar último dia do mês
                import calendar
                ultimo_dia = calendar.monthrange(ano_matricula, mes)[1]
                data_vencimento = datetime(ano_matricula, mes, min(dia_vencimento, ultimo_dia))
                
                mensalidades.append({
                    "mes_referencia": f"{nomes_meses[mes]}/{ano_matricula}",
                    "valor": valor,
                    "data_vencimento": data_vencimento.strftime("%Y-%m-%d")
                })
        
        return mensalidades
        
    except Exception:
        return []

def _gerar_mensalidades_manual(aluno: Dict, params: Dict) -> List[Dict]:
    """Gera mensalidades com parâmetros manuais"""
    mensalidades = []
    
    try:
        numero_parcelas = params.get("numero_parcelas", 10)
        data_primeira_parcela = params.get("data_primeira_parcela")
        valor_personalizado = params.get("valor_personalizado")
        
        if not data_primeira_parcela:
            return mensalidades
        
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        data_inicio = datetime.strptime(data_primeira_parcela, "%Y-%m-%d").date()
        valor = float(valor_personalizado or aluno["valor_mensalidade"])
        
        nomes_meses = [
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        for i in range(numero_parcelas):
            data_vencimento = data_inicio + relativedelta(months=i)
            
            mensalidades.append({
                "mes_referencia": f"{nomes_meses[data_vencimento.month]}/{data_vencimento.year}",
                "valor": valor,
                "data_vencimento": data_vencimento.strftime("%Y-%m-%d")
            })
        
        return mensalidades
        
    except Exception:
        return []

def _gerar_mensalidades_personalizado(aluno: Dict, params: Dict) -> List[Dict]:
    """Gera mensalidades com lista personalizada"""
    mensalidades = []
    
    try:
        lista_mensalidades = params.get("lista_mensalidades", [])
        
        for item in lista_mensalidades:
            if all(k in item for k in ["mes_referencia", "valor", "data_vencimento"]):
                mensalidades.append({
                    "mes_referencia": item["mes_referencia"],
                    "valor": float(item["valor"]),
                    "data_vencimento": item["data_vencimento"]
                })
        
        return mensalidades
        
    except Exception:
        return []

# ==========================================================
# 💰 FUNÇÕES DE OPERAÇÕES FINANCEIRAS
# ==========================================================

def marcar_mensalidade_como_paga(
    id_mensalidade: str, 
    data_pagamento: str,
    valor_pago: float,
    forma_pagamento: str = "PIX",
    id_pagamento: str = None,
    observacoes: str = ""
) -> Dict:
    """
    Marca uma mensalidade como paga (total ou parcialmente)
    
    Args:
        id_mensalidade: ID da mensalidade
        data_pagamento: Data do pagamento (YYYY-MM-DD)
        valor_pago: Valor que foi pago
        forma_pagamento: Forma de pagamento
        id_pagamento: ID do pagamento relacionado (opcional)
        observacoes: Observações adicionais
        
    Returns:
        Dict: Resultado da operação
    """
    try:
        # Buscar mensalidade
        mens_response = supabase.table("mensalidades").select(
            "valor, status, id_aluno"
        ).eq("id_mensalidade", id_mensalidade).execute()
        
        if not mens_response.data:
            return {"success": False, "error": "Mensalidade não encontrada"}
        
        mensalidade = mens_response.data[0]
        valor_original = float(mensalidade["valor"])
        
        # Determinar status
        if valor_pago >= valor_original:
            novo_status = "Pago"
        else:
            novo_status = "Pago parcial"
        
        # Atualizar mensalidade
        dados_update = {
            "status": novo_status,
            "data_pagamento": data_pagamento,
            "id_pagamento": id_pagamento,
            "observacoes": observacoes,
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("mensalidades").update(dados_update).eq(
            "id_mensalidade", id_mensalidade
        ).execute()
        
        if response.data:
            return {
                "success": True,
                "status_atualizado": novo_status,
                "valor_original": valor_original,
                "valor_pago": valor_pago,
                "diferenca": valor_original - valor_pago,
                "pagamento_completo": valor_pago >= valor_original
            }
        else:
            return {"success": False, "error": "Erro ao atualizar mensalidade"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def cancelar_mensalidade_com_motivo(
    id_mensalidade: str, 
    motivo: str,
    usuario: str = "Sistema"
) -> Dict:
    """
    Cancela uma mensalidade com motivo registrado
    
    Args:
        id_mensalidade: ID da mensalidade
        motivo: Motivo do cancelamento
        usuario: Usuário responsável
        
    Returns:
        Dict: Resultado da operação
    """
    try:
        observacoes = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] Cancelada por {usuario}: {motivo}"
        
        dados_cancelamento = {
            "status": "Cancelado",
            "observacoes": observacoes,
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("mensalidades").update(dados_cancelamento).eq(
            "id_mensalidade", id_mensalidade
        ).execute()
        
        if response.data:
            return {
                "success": True,
                "message": "Mensalidade cancelada com sucesso",
                "motivo": motivo,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "Erro ao cancelar mensalidade"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def aplicar_desconto_mensalidade(
    id_mensalidade: str,
    valor_desconto: float,
    motivo_desconto: str,
    tipo_desconto: str = "valor"  # "valor" ou "percentual"
) -> Dict:
    """
    Aplica desconto em uma mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade
        valor_desconto: Valor ou percentual do desconto
        motivo_desconto: Motivo do desconto
        tipo_desconto: "valor" para R$ ou "percentual" para %
        
    Returns:
        Dict: Resultado da operação
    """
    try:
        # Buscar mensalidade
        mens_response = supabase.table("mensalidades").select(
            "valor, observacoes"
        ).eq("id_mensalidade", id_mensalidade).execute()
        
        if not mens_response.data:
            return {"success": False, "error": "Mensalidade não encontrada"}
        
        mensalidade = mens_response.data[0]
        valor_original = float(mensalidade["valor"])
        
        # Calcular novo valor
        if tipo_desconto == "percentual":
            desconto_real = (valor_original * valor_desconto) / 100
            novo_valor = valor_original - desconto_real
        else:
            desconto_real = valor_desconto
            novo_valor = valor_original - desconto_real
        
        if novo_valor < 0:
            return {"success": False, "error": "Desconto não pode ser maior que o valor da mensalidade"}
        
        # Preparar observações
        observacoes_atual = mensalidade.get("observacoes", "")
        nova_observacao = f"[{datetime.now().strftime('%d/%m/%Y')}] Desconto aplicado: R$ {desconto_real:.2f} ({motivo_desconto})"
        
        if observacoes_atual:
            observacoes_final = f"{observacoes_atual}\n{nova_observacao}"
        else:
            observacoes_final = nova_observacao
        
        # Atualizar mensalidade
        dados_update = {
            "valor": novo_valor,
            "observacoes": observacoes_final,
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("mensalidades").update(dados_update).eq(
            "id_mensalidade", id_mensalidade
        ).execute()
        
        if response.data:
            return {
                "success": True,
                "valor_original": valor_original,
                "valor_desconto": desconto_real,
                "novo_valor": novo_valor,
                "tipo_desconto": tipo_desconto,
                "motivo": motivo_desconto
            }
        else:
            return {"success": False, "error": "Erro ao aplicar desconto"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 📊 FUNÇÕES DE RELATÓRIOS E ESTATÍSTICAS
# ==========================================================

def gerar_relatorio_mensalidades_resumido(
    filtros: Dict = None
) -> Dict:
    """
    Gera relatório resumido de mensalidades com filtros
    
    Args:
        filtros: Dicionário com filtros opcionais
        
    Returns:
        Dict: Relatório com estatísticas
    """
    try:
        # Query base
        query = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status,
            alunos!inner(nome, turmas!inner(nome_turma))
        """)
        
        # Aplicar filtros se fornecidos
        if filtros:
            if filtros.get("turma"):
                query = query.eq("alunos.turmas.nome_turma", filtros["turma"])
            
            if filtros.get("status"):
                if isinstance(filtros["status"], list):
                    query = query.in_("status", filtros["status"])
                else:
                    query = query.eq("status", filtros["status"])
            
            if filtros.get("data_inicio"):
                query = query.gte("data_vencimento", filtros["data_inicio"])
            
            if filtros.get("data_fim"):
                query = query.lte("data_vencimento", filtros["data_fim"])
        
        response = query.execute()
        
        # Processar dados
        mensalidades = response.data
        
        relatorio = {
            "total_mensalidades": len(mensalidades),
            "resumo_por_status": {},
            "resumo_por_turma": {},
            "valor_total": 0,
            "valor_por_status": {},
            "mensalidades_vencidas": 0,
            "valor_em_atraso": 0
        }
        
        data_hoje = date.today()
        
        for mens in mensalidades:
            status = mens["status"]
            turma = mens["alunos"]["turmas"]["nome_turma"]
            valor = float(mens["valor"])
            data_vencimento = datetime.strptime(mens["data_vencimento"], "%Y-%m-%d").date()
            
            # Resumo por status
            if status not in relatorio["resumo_por_status"]:
                relatorio["resumo_por_status"][status] = 0
                relatorio["valor_por_status"][status] = 0
            
            relatorio["resumo_por_status"][status] += 1
            relatorio["valor_por_status"][status] += valor
            
            # Resumo por turma
            if turma not in relatorio["resumo_por_turma"]:
                relatorio["resumo_por_turma"][turma] = {"count": 0, "valor": 0}
            
            relatorio["resumo_por_turma"][turma]["count"] += 1
            relatorio["resumo_por_turma"][turma]["valor"] += valor
            
            # Totais
            relatorio["valor_total"] += valor
            
            # Mensalidades vencidas
            if status not in ["Pago", "Pago parcial", "Cancelado"] and data_vencimento < data_hoje:
                relatorio["mensalidades_vencidas"] += 1
                relatorio["valor_em_atraso"] += valor
        
        return {
            "success": True,
            "relatorio": relatorio,
            "filtros_aplicados": filtros or {}
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_mensalidades_por_status(status: str, limite: int = 50) -> Dict:
    """
    Lista mensalidades por status específico
    
    Args:
        status: Status desejado
        limite: Número máximo de registros
        
    Returns:
        Dict: Lista de mensalidades
    """
    try:
        response = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status,
            alunos!inner(id, nome, turmas!inner(nome_turma))
        """).eq("status", status).order("data_vencimento").limit(limite).execute()
        
        mensalidades = []
        
        for mens in response.data:
            # Calcular informações adicionais
            status_info = calcular_status_mensalidade(
                mens["data_vencimento"], 
                mens["status"]
            )
            
            mensalidade_formatada = {
                **mens,
                **status_info,
                "nome_aluno": mens["alunos"]["nome"],
                "nome_turma": mens["alunos"]["turmas"]["nome_turma"],
                "valor_formatado": formatar_valor_br(mens["valor"]),
                "data_vencimento_formatada": formatar_data_br(mens["data_vencimento"])
            }
            
            mensalidades.append(mensalidade_formatada)
        
        return {
            "success": True,
            "mensalidades": mensalidades,
            "status_filtrado": status,
            "total_encontrado": len(mensalidades)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🎨 FUNÇÕES DE INTERFACE
# ==========================================================

def exibir_card_mensalidade(mensalidade: Dict) -> None:
    """
    Exibe um card bonito para uma mensalidade
    
    Args:
        mensalidade: Dados da mensalidade
    """
    # CSS para o card
    st.markdown(f"""
    <div style="
        border: 2px solid #{_get_color_by_status(mensalidade.get('status_real', 'A vencer'))};
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #2c3e50;">
                {mensalidade.get('emoji_status', '📅')} {mensalidade.get('mes_referencia', 'N/A')}
            </h4>
            <span style="
                background-color: #{_get_color_by_status(mensalidade.get('status_real', 'A vencer'))};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            ">
                {mensalidade.get('status_real', 'A vencer')}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div>
                <strong>💰 Valor:</strong> {mensalidade.get('valor_formatado', formatar_valor_br(mensalidade.get('valor', 0)))}<br>
                <strong>📅 Vencimento:</strong> {mensalidade.get('data_vencimento_formatada', formatar_data_br(mensalidade.get('data_vencimento', '')))}
            </div>
            <div>
                <strong>📊 Situação:</strong> {mensalidade.get('situacao_texto', 'N/A')}<br>
                {f"<strong>💳 Pago em:</strong> {formatar_data_br(mensalidade['data_pagamento'])}" if mensalidade.get('data_pagamento') else ""}
            </div>
        </div>
        
        {f"<div style='margin-top: 10px; font-size: 12px; color: #6c757d;'><strong>📝 Obs:</strong> {mensalidade['observacoes']}</div>" if mensalidade.get('observacoes') else ""}
    </div>
    """, unsafe_allow_html=True)

def _get_color_by_status(status: str) -> str:
    """Retorna cor hexadecimal baseada no status"""
    cores = {
        "Pago": "28a745",
        "Pago parcial": "ffc107", 
        "A vencer": "17a2b8",
        "Atrasado": "dc3545",
        "Vence hoje": "fd7e14",
        "Cancelado": "6c757d"
    }
    return cores.get(status, "6c757d")

# ==========================================================
# 🚀 FUNÇÃO PRINCIPAL DE INTEGRAÇÃO
# ==========================================================

def inicializar_sistema_mensalidades():
    """
    Inicializa o sistema de mensalidades na sessão do Streamlit
    """
    if 'sistema_mensalidades_iniciado' not in st.session_state:
        st.session_state.sistema_mensalidades_iniciado = True
        st.session_state.mensalidade_selecionada = None
        st.session_state.modo_edicao_mensalidade = False
        st.session_state.filtros_mensalidades = {}
        
        # CSS global para mensalidades
        st.markdown("""
        <style>
        .mensalidade-card {
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .mensalidade-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
        .mensalidade-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True) 