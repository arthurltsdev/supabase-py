#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💰 MODELO FINANCEIRO - Gestão de Pagamentos e Mensalidades
==========================================================

Contém todas as funções relacionadas ao domínio financeiro:
- Processamento de pagamentos
- Gestão de mensalidades
- Extrato PIX e cobranças
- Relatórios financeiros
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base import (
    supabase, PagamentoSchema, MensalidadeSchema, ExtratoPIXSchema,
    gerar_id_pagamento, gerar_id_mensalidade,
    tratar_valores_none, obter_timestamp, formatar_data_br, formatar_valor_br,
    TIPOS_PAGAMENTO, FORMAS_PAGAMENTO, STATUS_VALIDOS
)

# ==========================================================
# 💳 GESTÃO DE PAGAMENTOS
# ==========================================================

def registrar_pagamento_do_extrato(id_extrato: str,
                                  id_responsavel: str,
                                  id_aluno: str,
                                  tipo_pagamento: str,
                                  descricao: Optional[str] = None,
                                  id_mensalidade: Optional[str] = None) -> Dict:
    """
    Registra pagamento baseado em registro do extrato PIX
    
    Args:
        id_extrato: ID do registro no extrato_pix
        id_responsavel: ID do responsável pagador
        id_aluno: ID do aluno beneficiário
        tipo_pagamento: Tipo (matricula, fardamento, outro, etc.)
        descricao: Descrição adicional
        id_mensalidade: ID da mensalidade (se tipo_pagamento = 'mensalidade')
        
    Returns:
        Dict: {"success": bool, "id_pagamento": str, "message": str}
    """
    try:
        # 1. Buscar dados do extrato
        extrato_response = supabase.table("extrato_pix").select("*").eq("id", id_extrato).execute()
        
        if not extrato_response.data:
            return {"success": False, "error": "Registro do extrato não encontrado"}
        
        extrato = extrato_response.data[0]
        
        # 2. Verificar se já foi processado
        if extrato.get("status") == "registrado":
            return {"success": False, "error": "Este registro já foi processado"}
        
        # 3. Registrar pagamento
        id_pagamento = gerar_id_pagamento()
        
        dados_pagamento = {
            "id_pagamento": id_pagamento,
            "id_responsavel": id_responsavel,
            "id_aluno": id_aluno,
            "data_pagamento": extrato["data_pagamento"],
            "valor": extrato["valor"],
            "tipo_pagamento": tipo_pagamento,
            "forma_pagamento": "PIX",
            "descricao": descricao or f"Importado do extrato PIX - {extrato.get('observacoes', '')}",
            "origem_extrato": True,
            "id_extrato": id_extrato,
            "inserted_at": obter_timestamp(),
            "updated_at": obter_timestamp()
        }
        
        pag_response = supabase.table("pagamentos").insert(dados_pagamento).execute()
        
        if not pag_response.data:
            return {"success": False, "error": "Erro ao registrar pagamento"}
        
        # 4. Atualizar mensalidade se aplicável
        mensalidade_atualizada = False
        if tipo_pagamento.lower() == "mensalidade" and id_mensalidade:
            resultado_mens = atualizar_status_mensalidade(id_mensalidade, id_pagamento, extrato["data_pagamento"], float(extrato["valor"]))
            mensalidade_atualizada = resultado_mens.get("success", False)
        
        # 5. Atualizar data de matrícula se aplicável
        matricula_atualizada = False
        if tipo_pagamento.lower() == "matricula":
            aluno_update = supabase.table("alunos").update({
                "data_matricula": extrato["data_pagamento"],
                "updated_at": obter_timestamp()
            }).eq("id", id_aluno).execute()
            matricula_atualizada = bool(aluno_update.data)
        
        # 6. Atualizar status do extrato para "registrado"
        dados_update_extrato = {
            "status": "registrado",
            "id_responsavel": id_responsavel,
            "id_aluno": id_aluno,
            "tipo_pagamento": tipo_pagamento,
            "atualizado_em": obter_timestamp()
        }
        
        extrato_update = supabase.table("extrato_pix").update(dados_update_extrato).eq("id", id_extrato).execute()
        
        return {
            "success": True,
            "id_pagamento": id_pagamento,
            "extrato_atualizado": bool(extrato_update.data),
            "matricula_atualizada": matricula_atualizada,
            "mensalidade_atualizada": mensalidade_atualizada,
            "message": f"Pagamento registrado como {tipo_pagamento}"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def registrar_pagamentos_multiplos_do_extrato(id_extrato: str,
                                              id_responsavel: str,
                                              pagamentos_detalhados: List[Dict],
                                              descricao: Optional[str] = None) -> Dict:
    """
    Registra múltiplos pagamentos baseado em um registro do extrato PIX
    
    Args:
        id_extrato: ID do registro no extrato_pix
        id_responsavel: ID do responsável pagador
        pagamentos_detalhados: Lista de dicts com dados dos pagamentos
        descricao: Descrição adicional
        
    Returns:
        Dict: {"success": bool, "total_pagamentos_criados": int, "message": str}
    """
    try:
        # 1. Buscar dados do extrato
        extrato_response = supabase.table("extrato_pix").select("*").eq("id", id_extrato).execute()
        
        if not extrato_response.data:
            return {"success": False, "error": "Registro do extrato não encontrado"}
        
        extrato = extrato_response.data[0]
        valor_total_extrato = float(extrato.get('valor', 0))
        
        # 2. Verificar se já foi processado
        if extrato.get("status") == "registrado":
            return {"success": False, "error": "Este registro já foi processado"}
        
        # 3. Validar valores
        valor_total_pagamentos = sum(float(pag.get('valor', 0)) for pag in pagamentos_detalhados)
        
        if abs(valor_total_extrato - valor_total_pagamentos) > 0.01:  # Tolerância de 1 centavo
            return {
                "success": False,
                "error": f"Soma dos pagamentos (R$ {valor_total_pagamentos:.2f}) não confere com valor do extrato (R$ {valor_total_extrato:.2f})"
            }
        
        # 4. Validar alunos
        alunos_ids = [pag.get('id_aluno') for pag in pagamentos_detalhados]
        alunos_response = supabase.table("alunos").select("id, nome").in_("id", alunos_ids).execute()
        
        if len(alunos_response.data) != len(set(alunos_ids)):
            return {"success": False, "error": "Um ou mais alunos não foram encontrados"}
        
        # 5. Registrar cada pagamento
        pagamentos_criados = []
        matriculas_atualizadas = []
        
        for i, pag_detalhe in enumerate(pagamentos_detalhados):
            id_pagamento = gerar_id_pagamento()
            
            dados_pagamento = {
                "id_pagamento": id_pagamento,
                "id_responsavel": id_responsavel,
                "id_aluno": pag_detalhe.get('id_aluno'),
                "data_pagamento": extrato["data_pagamento"],
                "valor": float(pag_detalhe.get('valor')),
                "tipo_pagamento": pag_detalhe.get('tipo_pagamento'),
                "forma_pagamento": "PIX",
                "descricao": pag_detalhe.get('observacoes') or descricao or f"Importado do extrato PIX (pagamento {i+1}/{len(pagamentos_detalhados)}) - {extrato.get('observacoes', '')}",
                "origem_extrato": True,
                "id_extrato": id_extrato,
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }
            
            # Inserir pagamento
            pag_response = supabase.table("pagamentos").insert(dados_pagamento).execute()
            
            if not pag_response.data:
                return {
                    "success": False,
                    "error": f"Erro ao registrar pagamento {i+1}",
                    "pagamentos_criados": pagamentos_criados
                }
            
            pagamentos_criados.append(pag_response.data[0])
            
            # Atualizar mensalidade se aplicável
            if pag_detalhe.get('tipo_pagamento') == 'mensalidade' and pag_detalhe.get('id_mensalidade'):
                atualizar_status_mensalidade(
                    pag_detalhe.get('id_mensalidade'), 
                    id_pagamento, 
                    extrato["data_pagamento"], 
                    float(pag_detalhe.get('valor'))
                )
            
            # Se for matrícula, atualizar data_matricula do aluno
            if pag_detalhe.get('tipo_pagamento', '').lower() == 'matricula':
                aluno_update = supabase.table("alunos").update({
                    "data_matricula": extrato["data_pagamento"],
                    "updated_at": obter_timestamp()
                }).eq("id", pag_detalhe.get('id_aluno')).execute()
                
                if aluno_update.data:
                    matriculas_atualizadas.append(pag_detalhe.get('id_aluno'))
        
        # 6. Atualizar status do extrato
        tipos_resumo = ", ".join(set(pag.get('tipo_pagamento', '') for pag in pagamentos_detalhados))
        
        dados_update_extrato = {
            "status": "registrado",
            "id_responsavel": id_responsavel,
            "tipo_pagamento": tipos_resumo,
            "atualizado_em": obter_timestamp()
        }
        
        # Se todos os pagamentos são para o mesmo aluno, preencher id_aluno no extrato
        alunos_unicos = set(pag.get('id_aluno', '') for pag in pagamentos_detalhados)
        if len(alunos_unicos) == 1 and list(alunos_unicos)[0]:
            dados_update_extrato["id_aluno"] = list(alunos_unicos)[0]
        
        extrato_update = supabase.table("extrato_pix").update(dados_update_extrato).eq("id", id_extrato).execute()
        
        return {
            "success": True,
            "total_pagamentos_criados": len(pagamentos_criados),
            "pagamentos_criados": pagamentos_criados,
            "matriculas_atualizadas": matriculas_atualizadas,
            "extrato_atualizado": bool(extrato_update.data),
            "valor_total_processado": valor_total_pagamentos,
            "tipos_pagamento": [pag.get('tipo_pagamento') for pag in pagamentos_detalhados],
            "alunos_beneficiarios": [pag.get('id_aluno') for pag in pagamentos_detalhados],
            "message": f"{len(pagamentos_criados)} pagamentos registrados: {tipos_resumo}"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_pagamentos_aluno(id_aluno: str, data_inicio: Optional[str] = None, data_fim: Optional[str] = None) -> Dict:
    """
    Lista pagamentos de um aluno específico
    
    Args:
        id_aluno: ID do aluno
        data_inicio: Data início (YYYY-MM-DD)
        data_fim: Data fim (YYYY-MM-DD)
        
    Returns:
        Dict: {"success": bool, "pagamentos": List[Dict], "total_valor": float}
    """
    try:
        query = supabase.table("pagamentos").select("""
            id_pagamento, data_pagamento, valor, tipo_pagamento, 
            forma_pagamento, descricao, origem_extrato,
            responsaveis!inner(nome)
        """).eq("id_aluno", id_aluno)
        
        if data_inicio:
            query = query.gte("data_pagamento", data_inicio)
        if data_fim:
            query = query.lte("data_pagamento", data_fim)
            
        response = query.order("data_pagamento", desc=True).execute()
        
        pagamentos = []
        total_valor = 0
        
        for pagamento in response.data:
            pag_formatado = {
                "id_pagamento": pagamento["id_pagamento"],
                "data_pagamento": pagamento["data_pagamento"],
                "data_pagamento_fmt": formatar_data_br(pagamento["data_pagamento"]),
                "valor": float(pagamento["valor"]),
                "valor_fmt": formatar_valor_br(float(pagamento["valor"])),
                "tipo_pagamento": pagamento["tipo_pagamento"],
                "forma_pagamento": pagamento.get("forma_pagamento", "N/A"),
                "descricao": pagamento.get("descricao", ""),
                "origem_extrato": pagamento.get("origem_extrato", False),
                "nome_responsavel": pagamento["responsaveis"]["nome"] if pagamento.get("responsaveis") else "N/A"
            }
            pagamentos.append(pag_formatado)
            total_valor += pag_formatado["valor"]
        
        return {
            "success": True,
            "pagamentos": pagamentos,
            "count": len(pagamentos),
            "total_valor": total_valor,
            "total_valor_fmt": formatar_valor_br(total_valor)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 📅 GESTÃO DE MENSALIDADES
# ==========================================================

def listar_mensalidades_disponiveis_aluno(id_aluno: str) -> Dict:
    """
    Lista mensalidades disponíveis para pagamento de um aluno específico
    (status "A vencer" ou "Vencida")
    
    Args:
        id_aluno: ID do aluno
        
    Returns:
        Dict: {"success": bool, "mensalidades": List[Dict], "count": int}
    """
    try:
        # Buscar mensalidades pendentes (A vencer, Atrasado)
        response = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status, observacoes
        """).eq("id_aluno", id_aluno).in_("status", ["A vencer", "Atrasado"]).order("data_vencimento").execute()
        
        if not response.data:
            return {
                "success": True,
                "mensalidades": [],
                "count": 0,
                "message": "Nenhuma mensalidade pendente encontrada para este aluno"
            }
        
        # Formatear mensalidades para exibição
        data_hoje = datetime.now().date()
        
        mensalidades_formatadas = []
        for mensalidade in response.data:
            data_vencimento = datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d").date()
            
            # Calcular status real e dias de atraso/antecedência
            if data_vencimento < data_hoje:
                status_real = "Atrasado"
                dias_diferenca = (data_hoje - data_vencimento).days
                status_texto = f"Atrasado há {dias_diferenca} dias"
            else:
                status_real = "A vencer"
                dias_diferenca = (data_vencimento - data_hoje).days
                if dias_diferenca == 0:
                    status_texto = "Vence hoje"
                else:
                    status_texto = f"Vence em {dias_diferenca} dias"
            
            # Formatar para exibição
            mes_ref = mensalidade["mes_referencia"]
            valor = mensalidade["valor"]
            data_venc_fmt = data_vencimento.strftime("%d/%m/%Y")
            
            # Label para dropdown/seleção
            label = f"{mes_ref} - R$ {valor:.2f} - {data_venc_fmt} ({status_texto})"
            
            mensalidade_formatada = {
                "id_mensalidade": mensalidade["id_mensalidade"],
                "mes_referencia": mes_ref,
                "valor": valor,
                "data_vencimento": mensalidade["data_vencimento"],
                "data_vencimento_fmt": data_venc_fmt,
                "status": mensalidade["status"],
                "status_real": status_real,
                "status_texto": status_texto,
                "dias_diferenca": dias_diferenca,
                "observacoes": mensalidade.get("observacoes"),
                "label": label
            }
            
            mensalidades_formatadas.append(mensalidade_formatada)
        
        return {
            "success": True,
            "mensalidades": mensalidades_formatadas,
            "count": len(mensalidades_formatadas),
            "message": f"Encontradas {len(mensalidades_formatadas)} mensalidades pendentes"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_status_mensalidade(id_mensalidade: str, id_pagamento: str, 
                                data_pagamento: str, valor_pago: float) -> Dict:
    """
    Atualiza status de uma mensalidade após pagamento
    
    Args:
        id_mensalidade: ID da mensalidade
        id_pagamento: ID do pagamento
        data_pagamento: Data do pagamento
        valor_pago: Valor pago
        
    Returns:
        Dict: {"success": bool, "status_atualizado": str}
    """
    try:
        # Buscar valor original da mensalidade
        mens_response = supabase.table("mensalidades").select("valor").eq("id_mensalidade", id_mensalidade).execute()
        
        if not mens_response.data:
            return {"success": False, "error": f"Mensalidade {id_mensalidade} não encontrada"}
        
        valor_original = float(mens_response.data[0]["valor"])
        novo_status = "Pago" if valor_pago >= valor_original else "Pago parcial"
        
        # Atualizar mensalidade
        dados_update = {
            "status": novo_status,
            "id_pagamento": id_pagamento,
            "data_pagamento": data_pagamento,
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("mensalidades").update(dados_update).eq("id_mensalidade", id_mensalidade).execute()
        
        if response.data:
            return {
                "success": True,
                "status_atualizado": novo_status,
                "valor_original": valor_original,
                "valor_pago": valor_pago
            }
        else:
            return {"success": False, "error": "Erro ao atualizar mensalidade"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def gerar_mensalidades_aluno(id_aluno: str, ano_letivo: str, valor_mensalidade: float, 
                            dia_vencimento: int = 5) -> Dict:
    """
    Gera mensalidades para um aluno em um ano letivo
    
    Args:
        id_aluno: ID do aluno
        ano_letivo: Ano letivo (ex: "2024")
        valor_mensalidade: Valor da mensalidade
        dia_vencimento: Dia do vencimento (1-31)
        
    Returns:
        Dict: {"success": bool, "mensalidades_geradas": int}
    """
    try:
        # Verificar se aluno existe
        aluno_response = supabase.table("alunos").select("id, nome").eq("id", id_aluno).execute()
        if not aluno_response.data:
            return {"success": False, "error": f"Aluno {id_aluno} não encontrado"}
        
        # Verificar se já existem mensalidades para este ano
        check_response = supabase.table("mensalidades").select("id_mensalidade").eq("id_aluno", id_aluno).like("mes_referencia", f"%/{ano_letivo}").execute()
        
        if check_response.data:
            return {"success": False, "error": f"Mensalidades já existem para o ano {ano_letivo}"}
        
        # Gerar mensalidades (março a dezembro = 10 meses)
        meses = [
            ("03", "Março"), ("04", "Abril"), ("05", "Maio"), ("06", "Junho"),
            ("07", "Julho"), ("08", "Agosto"), ("09", "Setembro"), ("10", "Outubro"),
            ("11", "Novembro"), ("12", "Dezembro")
        ]
        
        mensalidades_criadas = []
        
        for mes_num, mes_nome in meses:
            id_mensalidade = gerar_id_mensalidade()
            
            dados_mensalidade = {
                "id_mensalidade": id_mensalidade,
                "id_aluno": id_aluno,
                "mes_referencia": f"{mes_nome}/{ano_letivo}",
                "valor": valor_mensalidade,
                "data_vencimento": f"{ano_letivo}-{mes_num}-{dia_vencimento:02d}",
                "status": "A vencer",
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }
            
            response = supabase.table("mensalidades").insert(dados_mensalidade).execute()
            
            if response.data:
                mensalidades_criadas.append(response.data[0])
        
        # Atualizar flag no aluno
        supabase.table("alunos").update({
            "mensalidades_geradas": True,
            "updated_at": obter_timestamp()
        }).eq("id", id_aluno).execute()
        
        return {
            "success": True,
            "mensalidades_geradas": len(mensalidades_criadas),
            "ano_letivo": ano_letivo,
            "valor_mensalidade": valor_mensalidade,
            "mensalidades": mensalidades_criadas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 📊 EXTRATO PIX
# ==========================================================

def listar_extrato_com_sem_responsavel(data_inicio: Optional[str] = None,
                                      data_fim: Optional[str] = None,
                                      filtro_turma: Optional[str] = None) -> Dict:
    """
    Lista registros do extrato PIX separando COM e SEM responsável cadastrado
    
    Args:
        data_inicio: Data início (YYYY-MM-DD)
        data_fim: Data fim (YYYY-MM-DD)
        filtro_turma: Nome da turma para filtrar
        
    Returns:
        Dict: {"success": bool, "com_responsavel": List, "sem_responsavel": List}
    """
    try:
        # Base query
        base_query = supabase.table("extrato_pix").select("""
            *,
            responsaveis(id, nome)
        """).eq("status", "novo")
        
        if data_inicio:
            base_query = base_query.gte("data_pagamento", data_inicio)
        if data_fim:
            base_query = base_query.lte("data_pagamento", data_fim)
            
        response = base_query.execute()
        
        com_responsavel = []
        sem_responsavel = []
        
        for registro in response.data:
            # Verificar filtro de turma se especificado
            if filtro_turma:
                id_responsavel = registro.get("id_responsavel")
                if id_responsavel:
                    # Buscar alunos vinculados ao responsável
                    alunos_resp = supabase.table("alunos_responsaveis").select("""
                        alunos!inner(
                            turmas!inner(nome_turma)
                        )
                    """).eq("id_responsavel", id_responsavel).execute()
                    
                    # Verificar se algum aluno está na turma filtrada
                    tem_aluno_na_turma = False
                    if alunos_resp.data:
                        for vinculo in alunos_resp.data:
                            turma_aluno = vinculo["alunos"]["turmas"]["nome_turma"]
                            if turma_aluno == filtro_turma:
                                tem_aluno_na_turma = True
                                break
                    
                    if not tem_aluno_na_turma:
                        continue
            
            if registro.get("id_responsavel") and registro.get("responsaveis"):
                com_responsavel.append(registro)
            else:
                sem_responsavel.append(registro)
        
        return {
            "success": True,
            "com_responsavel": com_responsavel,
            "sem_responsavel": sem_responsavel,
            "total_com": len(com_responsavel),
            "total_sem": len(sem_responsavel),
            "total_geral": len(response.data),
            "filtro_turma": filtro_turma
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def obter_estatisticas_extrato(data_inicio: Optional[str] = None,
                              data_fim: Optional[str] = None) -> Dict:
    """
    Obtém estatísticas do extrato PIX
    
    Args:
        data_inicio: Data início (YYYY-MM-DD)
        data_fim: Data fim (YYYY-MM-DD)
        
    Returns:
        Dict: {"success": bool, "estatisticas": Dict}
    """
    try:
        # Query base
        query = supabase.table("extrato_pix").select("status, valor")
        
        if data_inicio:
            query = query.gte("data_pagamento", data_inicio)
        if data_fim:
            query = query.lte("data_pagamento", data_fim)
            
        response = query.execute()
        
        stats = {
            "total_registros": len(response.data),
            "novos": 0,
            "registrados": 0,
            "ignorados": 0,
            "valor_total": 0,
            "valor_novos": 0,
            "valor_registrados": 0,
            "valor_ignorados": 0
        }
        
        for registro in response.data:
            status = registro.get("status", "novo")
            valor = float(registro.get("valor", 0))
            
            stats["valor_total"] += valor
            
            if status == "novo":
                stats["novos"] += 1
                stats["valor_novos"] += valor
            elif status == "registrado":
                stats["registrados"] += 1
                stats["valor_registrados"] += valor
            elif status == "ignorado":
                stats["ignorados"] += 1
                stats["valor_ignorados"] += valor
        
        # Calcular percentuais
        if stats["total_registros"] > 0:
            stats["percentual_processado"] = round((stats["registrados"] / stats["total_registros"]) * 100, 2)
        else:
            stats["percentual_processado"] = 0
        
        return {
            "success": True,
            "estatisticas": stats
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def ignorar_registro_extrato(id_extrato: str) -> Dict:
    """
    Marca um registro do extrato PIX como ignorado
    
    Args:
        id_extrato: ID do registro no extrato
        
    Returns:
        Dict: {"success": bool, "message": str}
    """
    try:
        response = supabase.table("extrato_pix").update({
            "status": "ignorado",
            "atualizado_em": obter_timestamp()
        }).eq("id", id_extrato).execute()
        
        if response.data:
            return {"success": True, "message": "Registro marcado como ignorado"}
        else:
            return {"success": False, "error": "Registro não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 📈 RELATÓRIOS FINANCEIROS
# ==========================================================

def relatorio_pagamentos_periodo(data_inicio: str, data_fim: str, 
                                 tipo_pagamento: Optional[str] = None) -> Dict:
    """
    Gera relatório de pagamentos por período
    
    Args:
        data_inicio: Data início (YYYY-MM-DD)
        data_fim: Data fim (YYYY-MM-DD)
        tipo_pagamento: Filtro por tipo (opcional)
        
    Returns:
        Dict: {"success": bool, "relatorio": Dict}
    """
    try:
        query = supabase.table("pagamentos").select("""
            id_pagamento, data_pagamento, valor, tipo_pagamento, forma_pagamento,
            alunos!inner(nome, turmas!inner(nome_turma)),
            responsaveis!inner(nome)
        """).gte("data_pagamento", data_inicio).lte("data_pagamento", data_fim)
        
        if tipo_pagamento:
            query = query.eq("tipo_pagamento", tipo_pagamento)
            
        response = query.order("data_pagamento", desc=True).execute()
        
        # Processar dados
        total_valor = 0
        pagamentos_por_tipo = {}
        pagamentos_por_forma = {}
        pagamentos_por_turma = {}
        
        for pagamento in response.data:
            valor = float(pagamento["valor"])
            total_valor += valor
            
            # Por tipo
            tipo = pagamento["tipo_pagamento"]
            if tipo not in pagamentos_por_tipo:
                pagamentos_por_tipo[tipo] = {"count": 0, "valor": 0}
            pagamentos_por_tipo[tipo]["count"] += 1
            pagamentos_por_tipo[tipo]["valor"] += valor
            
            # Por forma
            forma = pagamento.get("forma_pagamento", "N/A")
            if forma not in pagamentos_por_forma:
                pagamentos_por_forma[forma] = {"count": 0, "valor": 0}
            pagamentos_por_forma[forma]["count"] += 1
            pagamentos_por_forma[forma]["valor"] += valor
            
            # Por turma
            turma = pagamento["alunos"]["turmas"]["nome_turma"]
            if turma not in pagamentos_por_turma:
                pagamentos_por_turma[turma] = {"count": 0, "valor": 0}
            pagamentos_por_turma[turma]["count"] += 1
            pagamentos_por_turma[turma]["valor"] += valor
        
        relatorio = {
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "resumo": {
                "total_pagamentos": len(response.data),
                "total_valor": total_valor,
                "total_valor_fmt": formatar_valor_br(total_valor),
                "valor_medio": total_valor / len(response.data) if response.data else 0
            },
            "por_tipo": pagamentos_por_tipo,
            "por_forma": pagamentos_por_forma,
            "por_turma": pagamentos_por_turma,
            "pagamentos_detalhados": response.data
        }
        
        return {
            "success": True,
            "relatorio": relatorio
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def relatorio_mensalidades_vencidas(turma: Optional[str] = None) -> Dict:
    """
    Gera relatório de mensalidades vencidas
    
    Args:
        turma: Filtro por turma (opcional)
        
    Returns:
        Dict: {"success": bool, "relatorio": Dict}
    """
    try:
        # Data atual
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        
        query = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status,
            alunos!inner(
                id, nome,
                turmas!inner(nome_turma)
            )
        """).lt("data_vencimento", data_hoje).in_("status", ["A vencer", "Vencida"])
        
        response = query.order("data_vencimento").execute()
        
        # Filtrar por turma se especificado
        if turma:
            response.data = [
                mens for mens in response.data 
                if mens["alunos"]["turmas"]["nome_turma"] == turma
            ]
        
        # Processar dados
        total_valor_vencido = 0
        vencidas_por_turma = {}
        
        for mensalidade in response.data:
            valor = float(mensalidade["valor"])
            total_valor_vencido += valor
            
            turma_nome = mensalidade["alunos"]["turmas"]["nome_turma"]
            if turma_nome not in vencidas_por_turma:
                vencidas_por_turma[turma_nome] = {"count": 0, "valor": 0, "alunos": set()}
            
            vencidas_por_turma[turma_nome]["count"] += 1
            vencidas_por_turma[turma_nome]["valor"] += valor
            vencidas_por_turma[turma_nome]["alunos"].add(mensalidade["alunos"]["nome"])
        
        # Converter sets para listas
        for turma_data in vencidas_por_turma.values():
            turma_data["alunos"] = list(turma_data["alunos"])
            turma_data["total_alunos"] = len(turma_data["alunos"])
        
        relatorio = {
            "data_referencia": data_hoje,
            "resumo": {
                "total_mensalidades_vencidas": len(response.data),
                "total_valor_vencido": total_valor_vencido,
                "total_valor_vencido_fmt": formatar_valor_br(total_valor_vencido),
                "total_turmas_afetadas": len(vencidas_por_turma)
            },
            "por_turma": vencidas_por_turma,
            "mensalidades_detalhadas": response.data
        }
        
        return {
            "success": True,
            "relatorio": relatorio
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}