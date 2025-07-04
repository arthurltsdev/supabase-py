#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏢 MODELO ORGANIZACIONAL - Validações, Relatórios e Configurações
================================================================

Contém todas as funções relacionadas ao domínio organizacional:
- Validações e consistência de dados
- Relatórios gerenciais
- Configurações do sistema
- Manutenção e correções automáticas
"""

from typing import Dict, List, Optional
from datetime import datetime
import difflib
from .base import (
    supabase, obter_timestamp, formatar_data_br, formatar_valor_br
)

# ==========================================================
# 🔍 VALIDAÇÕES E CONSISTÊNCIA
# ==========================================================

def verificar_consistencia_extrato_pagamentos(data_inicio: Optional[str] = None,
                                            data_fim: Optional[str] = None) -> Dict:
    """
    Verifica a consistência entre registros do extrato e pagamentos
    Retorna relatório detalhado de possíveis inconsistências
    
    Args:
        data_inicio: Data início para análise (YYYY-MM-DD)
        data_fim: Data fim para análise (YYYY-MM-DD)
        
    Returns:
        Dict: {"success": bool, "relatorio": Dict}
    """
    try:
        # Query base para extrato
        query_extrato = supabase.table("extrato_pix").select("*")
        if data_inicio:
            query_extrato = query_extrato.gte("data_pagamento", data_inicio)
        if data_fim:
            query_extrato = query_extrato.lte("data_pagamento", data_fim)
        
        response_extrato = query_extrato.execute()
        
        # Query base para pagamentos
        query_pagamentos = supabase.table("pagamentos").select("*").eq("origem_extrato", True)
        if data_inicio:
            query_pagamentos = query_pagamentos.gte("data_pagamento", data_inicio)
        if data_fim:
            query_pagamentos = query_pagamentos.lte("data_pagamento", data_fim)
            
        response_pagamentos = query_pagamentos.execute()
        
        relatorio = {
            "total_extrato": len(response_extrato.data),
            "total_pagamentos_origem_extrato": len(response_pagamentos.data),
            "status_extrato": {},
            "inconsistencias": [],
            "recomendacoes": []
        }
        
        # Análise por status
        for registro in response_extrato.data:
            status = registro.get("status", "desconhecido")
            if status not in relatorio["status_extrato"]:
                relatorio["status_extrato"][status] = 0
            relatorio["status_extrato"][status] += 1
        
        # Buscar inconsistências
        for extrato in response_extrato.data:
            if extrato.get("status") == "novo":
                # Buscar pagamentos correspondentes
                pagamentos_correspondentes = [
                    p for p in response_pagamentos.data
                    if (float(p.get("valor", 0)) == float(extrato.get("valor", 0)) and
                        p.get("data_pagamento") == extrato.get("data_pagamento") and
                        p.get("id_responsavel") == extrato.get("id_responsavel"))
                ]
                
                if pagamentos_correspondentes:
                    relatorio["inconsistencias"].append({
                        "tipo": "extrato_novo_com_pagamento_existente",
                        "id_extrato": extrato["id"],
                        "nome_remetente": extrato.get("nome_remetente"),
                        "valor": extrato.get("valor"),
                        "data": extrato.get("data_pagamento"),
                        "pagamentos_encontrados": [p["id_pagamento"] for p in pagamentos_correspondentes]
                    })
        
        # Gerar recomendações
        if relatorio["inconsistencias"]:
            relatorio["recomendacoes"].append(
                f"Execute verificar_e_corrigir_extrato_duplicado() para corrigir {len(relatorio['inconsistencias'])} inconsistências"
            )
        
        return {
            "success": True,
            "relatorio": relatorio
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def verificar_e_corrigir_extrato_duplicado() -> Dict:
    """
    Verifica registros do extrato_pix que já foram processados mas ainda 
    aparecem como 'novo' e corrige o status para 'registrado'
    
    Returns:
        Dict: {"success": bool, "corrigidos": int, "detalhes": List}
    """
    try:
        # 1. Buscar todos os registros do extrato com status 'novo'
        response_extrato = supabase.table("extrato_pix").select(
            "id, nome_remetente, valor, data_pagamento, id_responsavel"
        ).eq("status", "novo").execute()
        
        if not response_extrato.data:
            return {
                "success": True,
                "message": "Nenhum registro 'novo' encontrado no extrato",
                "corrigidos": 0,
                "detalhes": []
            }
        
        registros_extrato = response_extrato.data
        corrigidos = []
        
        # 2. Para cada registro do extrato, verificar se já existe pagamento
        for registro in registros_extrato:
            # Buscar pagamentos com mesmos dados básicos
            response_pagamentos = supabase.table("pagamentos").select(
                "id_pagamento, id_responsavel, valor, data_pagamento, origem_extrato, id_extrato"
            ).eq("valor", registro["valor"]).eq("data_pagamento", registro["data_pagamento"]).execute()
            
            if response_pagamentos.data:
                # Verificar se algum pagamento corresponde ao registro do extrato
                for pagamento in response_pagamentos.data:
                    # Critério 1: Mesmo responsável, valor e data
                    if (pagamento.get("id_responsavel") == registro.get("id_responsavel") and
                        float(pagamento.get("valor", 0)) == float(registro.get("valor", 0)) and
                        pagamento.get("data_pagamento") == registro.get("data_pagamento")):
                        
                        # Critério 2: Se tem origem_extrato=True, é quase certeza que é duplicado
                        eh_duplicado = pagamento.get("origem_extrato", False)
                        
                        # Critério 3: Se id_extrato bate, é definitivamente duplicado
                        if pagamento.get("id_extrato") == registro["id"]:
                            eh_duplicado = True
                        
                        if eh_duplicado:
                            # Atualizar status do extrato para 'registrado'
                            update_response = supabase.table("extrato_pix").update({
                                "status": "registrado",
                                "atualizado_em": obter_timestamp(),
                                "observacoes_sistema": f"Corrigido automaticamente - já processado (pagamento {pagamento['id_pagamento']})"
                            }).eq("id", registro["id"]).execute()
                            
                            if update_response.data:
                                corrigidos.append({
                                    "id_extrato": registro["id"],
                                    "nome_remetente": registro["nome_remetente"],
                                    "valor": registro["valor"],
                                    "data_pagamento": registro["data_pagamento"],
                                    "id_pagamento_encontrado": pagamento["id_pagamento"],
                                    "motivo": "Origem extrato confirmada" if pagamento.get("origem_extrato") else "Dados coincidentes"
                                })
                            break
        
        return {
            "success": True,
            "message": f"{len(corrigidos)} registros corrigidos",
            "corrigidos": len(corrigidos),
            "detalhes": corrigidos,
            "total_verificados": len(registros_extrato)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "corrigidos": 0
        }

def corrigir_status_extrato_com_pagamentos() -> Dict:
    """
    Corrige o status de registros do extrato_pix que já possuem pagamentos vinculados
    mas ainda estão com status "novo". Atualiza para "registrado".
    
    Returns:
        Dict: {"success": bool, "corrigidos": int, "detalhes": List}
    """
    try:
        # 1. Buscar registros do extrato com status "novo"
        response_extrato = supabase.table("extrato_pix").select(
            "id, nome_remetente, data_pagamento, valor, status"
        ).eq("status", "novo").execute()
        
        if not response_extrato.data:
            return {
                "success": True,
                "message": "Nenhum registro com status 'novo' encontrado",
                "corrigidos": 0
            }
        
        # 2. Para cada registro, verificar se já existe pagamento vinculado
        corrigidos = 0
        detalhes_correcoes = []
        
        for registro_extrato in response_extrato.data:
            # Buscar pagamentos que referenciam este extrato
            response_pagamentos = supabase.table("pagamentos").select(
                "id_pagamento, id_extrato, id_responsavel, id_aluno, data_pagamento, valor"
            ).eq("id_extrato", registro_extrato["id"]).execute()
            
            if response_pagamentos.data:
                # Há pagamentos vinculados - corrigir status
                primeiro_pagamento = response_pagamentos.data[0]
                
                dados_update = {
                    "status": "registrado",
                    "id_responsavel": primeiro_pagamento.get("id_responsavel"),
                    "atualizado_em": obter_timestamp()
                }
                
                # Se há apenas um pagamento e tem id_aluno, usar no extrato
                if len(response_pagamentos.data) == 1 and primeiro_pagamento.get("id_aluno"):
                    dados_update["id_aluno"] = primeiro_pagamento["id_aluno"]
                
                # Atualizar o registro
                supabase.table("extrato_pix").update(dados_update).eq("id", registro_extrato["id"]).execute()
                
                corrigidos += 1
                detalhes_correcoes.append({
                    "id_extrato": registro_extrato["id"],
                    "nome_remetente": registro_extrato["nome_remetente"],
                    "valor": registro_extrato["valor"],
                    "data_pagamento": registro_extrato["data_pagamento"],
                    "pagamentos_vinculados": len(response_pagamentos.data),
                    "id_responsavel": primeiro_pagamento.get("id_responsavel"),
                    "id_aluno": primeiro_pagamento.get("id_aluno") if len(response_pagamentos.data) == 1 else None
                })
        
        return {
            "success": True,
            "message": f"{corrigidos} registros corrigidos de 'novo' para 'registrado'",
            "corrigidos": corrigidos,
            "total_analisados": len(response_extrato.data),
            "detalhes_correcoes": detalhes_correcoes
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao corrigir status do extrato: {str(e)}"
        }

def atualizar_responsaveis_extrato_pix() -> Dict:
    """
    Identifica registros do extrato_pix sem id_responsavel e tenta fazer correspondência
    com a tabela responsaveis usando similaridade de nomes (>90%).
    Para responsáveis com apenas 1 aluno, também preenche id_aluno.
    
    Returns:
        Dict: {"success": bool, "atualizados": int, "correspondencias": List}
    """
    try:
        # 1. Buscar registros do extrato_pix sem id_responsavel
        response_extrato = supabase.table("extrato_pix").select(
            "id, nome_remetente, data_pagamento, valor"
        ).is_("id_responsavel", "null").execute()
        
        if not response_extrato.data:
            return {
                "success": True,
                "message": "Nenhum registro sem id_responsavel encontrado",
                "atualizados": 0
            }
        
        # 2. Buscar todos os responsáveis
        try:
            response_responsaveis = supabase.table("responsaveis").select("id, nome, nome_norm").execute()
            usar_nome_norm = True
        except:
            # Se nome_norm não existe, usar nome normal
            response_responsaveis = supabase.table("responsaveis").select("id, nome").execute()
            usar_nome_norm = False
        
        if not response_responsaveis.data:
            return {
                "success": False,
                "error": "Nenhum responsável encontrado na tabela responsaveis"
            }
        
        # 3. Para cada registro do extrato, tentar encontrar correspondência
        atualizados = 0
        correspondencias = []
        
        for registro_extrato in response_extrato.data:
            nome_remetente = registro_extrato.get("nome_remetente", "")
            
            # Buscar melhor correspondência
            melhor_responsavel = None
            melhor_similaridade = 0
            
            for responsavel in response_responsaveis.data:
                # Usar nome_norm se disponível, senão usar nome
                if usar_nome_norm and responsavel.get("nome_norm"):
                    nome_comparacao = responsavel["nome_norm"]
                else:
                    nome_comparacao = responsavel["nome"]
                
                # Usar a função de similaridade
                similaridade = calcular_similaridade_nomes(nome_remetente, nome_comparacao)
                
                if similaridade > melhor_similaridade and similaridade >= 90:
                    melhor_similaridade = similaridade
                    melhor_responsavel = responsavel
            
            if melhor_responsavel:
                # Verificar quantos alunos o responsável tem
                response_alunos = supabase.table("alunos_responsaveis").select(
                    "id_aluno, alunos!inner(nome)"
                ).eq("id_responsavel", melhor_responsavel["id"]).execute()
                
                dados_update = {
                    "id_responsavel": melhor_responsavel["id"]
                }
                
                # Se tem apenas 1 aluno, preencher id_aluno também
                if len(response_alunos.data) == 1:
                    dados_update["id_aluno"] = response_alunos.data[0]["id_aluno"]
                
                # Atualizar o registro
                supabase.table("extrato_pix").update(dados_update).eq("id", registro_extrato["id"]).execute()
                
                atualizados += 1
                correspondencias.append({
                    "id_extrato": registro_extrato["id"],
                    "nome_remetente": nome_remetente,
                    "nome_responsavel": melhor_responsavel["nome"],
                    "nome_usado_comparacao": nome_comparacao if usar_nome_norm and melhor_responsavel.get("nome_norm") else melhor_responsavel["nome"],
                    "similaridade": melhor_similaridade,
                    "id_responsavel": melhor_responsavel["id"],
                    "alunos_vinculados": len(response_alunos.data),
                    "id_aluno_preenchido": dados_update.get("id_aluno") is not None,
                    "usado_nome_norm": usar_nome_norm and melhor_responsavel.get("nome_norm") is not None
                })
        
        return {
            "success": True,
            "message": f"{atualizados} registros atualizados com responsáveis",
            "atualizados": atualizados,
            "total_analisados": len(response_extrato.data),
            "correspondencias": correspondencias,
            "usou_nome_norm": usar_nome_norm
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao atualizar responsáveis: {str(e)}"
        }

def calcular_similaridade_nomes(nome1: str, nome2: str) -> float:
    """
    Calcula a similaridade entre dois nomes usando difflib
    
    Args:
        nome1: Primeiro nome
        nome2: Segundo nome
        
    Returns:
        float: Similaridade em porcentagem (0-100)
    """
    if not nome1 or not nome2:
        return 0.0
    
    # Normalizar nomes
    nome1_limpo = nome1.lower().strip().replace("  ", " ")
    nome2_limpo = nome2.lower().strip().replace("  ", " ")
    
    return difflib.SequenceMatcher(None, nome1_limpo, nome2_limpo).ratio() * 100

# ==========================================================
# 📊 RELATÓRIOS GERENCIAIS
# ==========================================================

def relatorio_geral_sistema(data_referencia: Optional[str] = None) -> Dict:
    """
    Gera relatório geral do sistema com estatísticas principais
    
    Args:
        data_referencia: Data de referência (YYYY-MM-DD). Se None, usa data atual
        
    Returns:
        Dict: {"success": bool, "relatorio": Dict}
    """
    try:
        if not data_referencia:
            data_referencia = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Estatísticas de alunos
        alunos_response = supabase.table("alunos").select("""
            id, nome, valor_mensalidade, mensalidades_geradas,
            turmas!inner(nome_turma)
        """).execute()
        
        total_alunos = len(alunos_response.data)
        alunos_por_turma = {}
        valor_total_mensalidades = 0
        alunos_com_mensalidades_geradas = 0
        
        for aluno in alunos_response.data:
            turma = aluno["turmas"]["nome_turma"]
            if turma not in alunos_por_turma:
                alunos_por_turma[turma] = 0
            alunos_por_turma[turma] += 1
            
            valor_mensalidade = aluno.get("valor_mensalidade") or 0
            valor_total_mensalidades += float(valor_mensalidade)
            
            if aluno.get("mensalidades_geradas"):
                alunos_com_mensalidades_geradas += 1
        
        # 2. Estatísticas de responsáveis
        responsaveis_response = supabase.table("responsaveis").select("id").execute()
        total_responsaveis = len(responsaveis_response.data)
        
        # 3. Estatísticas financeiras
        pagamentos_response = supabase.table("pagamentos").select("valor, tipo_pagamento").execute()
        total_pagamentos = len(pagamentos_response.data)
        valor_total_recebido = sum(float(p["valor"]) for p in pagamentos_response.data)
        
        pagamentos_por_tipo = {}
        for pagamento in pagamentos_response.data:
            tipo = pagamento["tipo_pagamento"]
            if tipo not in pagamentos_por_tipo:
                pagamentos_por_tipo[tipo] = {"count": 0, "valor": 0}
            pagamentos_por_tipo[tipo]["count"] += 1
            pagamentos_por_tipo[tipo]["valor"] += float(pagamento["valor"])
        
        # 4. Mensalidades vencidas
        mensalidades_vencidas = supabase.table("mensalidades").select("valor").lt(
            "data_vencimento", data_referencia
        ).in_("status", ["A vencer", "Vencida"]).execute()
        
        total_mensalidades_vencidas = len(mensalidades_vencidas.data)
        valor_mensalidades_vencidas = sum(float(m["valor"]) for m in mensalidades_vencidas.data)
        
        # 5. Extrato PIX
        extrato_response = supabase.table("extrato_pix").select("status, valor").execute()
        extrato_stats = {"novo": 0, "registrado": 0, "ignorado": 0}
        extrato_valores = {"novo": 0, "registrado": 0, "ignorado": 0}
        
        for registro in extrato_response.data:
            status = registro.get("status", "novo")
            valor = float(registro.get("valor", 0))
            
            if status in extrato_stats:
                extrato_stats[status] += 1
                extrato_valores[status] += valor
        
        # Montar relatório
        relatorio = {
            "data_referencia": data_referencia,
            "resumo_geral": {
                "total_alunos": total_alunos,
                "total_responsaveis": total_responsaveis,
                "total_turmas": len(alunos_por_turma),
                "total_pagamentos": total_pagamentos,
                "valor_total_recebido": valor_total_recebido,
                "valor_total_recebido_fmt": formatar_valor_br(valor_total_recebido)
            },
            "alunos": {
                "total": total_alunos,
                "por_turma": alunos_por_turma,
                "valor_total_mensalidades": valor_total_mensalidades,
                "valor_total_mensalidades_fmt": formatar_valor_br(valor_total_mensalidades),
                "com_mensalidades_geradas": alunos_com_mensalidades_geradas,
                "percentual_com_mensalidades": round((alunos_com_mensalidades_geradas / total_alunos * 100), 2) if total_alunos > 0 else 0
            },
            "financeiro": {
                "total_pagamentos": total_pagamentos,
                "valor_total_recebido": valor_total_recebido,
                "valor_medio_pagamento": valor_total_recebido / total_pagamentos if total_pagamentos > 0 else 0,
                "pagamentos_por_tipo": pagamentos_por_tipo,
                "mensalidades_vencidas": {
                    "count": total_mensalidades_vencidas,
                    "valor": valor_mensalidades_vencidas,
                    "valor_fmt": formatar_valor_br(valor_mensalidades_vencidas)
                }
            },
            "extrato_pix": {
                "estatisticas": extrato_stats,
                "valores": extrato_valores,
                "total_registros": sum(extrato_stats.values()),
                "percentual_processado": round((extrato_stats["registrado"] / sum(extrato_stats.values()) * 100), 2) if sum(extrato_stats.values()) > 0 else 0
            }
        }
        
        return {
            "success": True,
            "relatorio": relatorio
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def relatorio_inadimplencia(data_referencia: Optional[str] = None) -> Dict:
    """
    Gera relatório de inadimplência com detalhes por aluno e turma
    
    Args:
        data_referencia: Data de referência (YYYY-MM-DD). Se None, usa data atual
        
    Returns:
        Dict: {"success": bool, "relatorio": Dict}
    """
    try:
        if not data_referencia:
            data_referencia = datetime.now().strftime("%Y-%m-%d")
        
        # Buscar mensalidades vencidas
        mensalidades_vencidas = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status,
            alunos!inner(
                id, nome,
                turmas!inner(nome_turma)
            )
        """).lt("data_vencimento", data_referencia).in_("status", ["A vencer", "Vencida"]).execute()
        
        # Processar dados
        inadimplencia_por_turma = {}
        inadimplencia_por_aluno = {}
        total_valor_vencido = 0
        
        for mensalidade in mensalidades_vencidas.data:
            aluno_id = mensalidade["alunos"]["id"]
            aluno_nome = mensalidade["alunos"]["nome"]
            turma_nome = mensalidade["alunos"]["turmas"]["nome_turma"]
            valor = float(mensalidade["valor"])
            
            total_valor_vencido += valor
            
            # Por turma
            if turma_nome not in inadimplencia_por_turma:
                inadimplencia_por_turma[turma_nome] = {
                    "alunos_inadimplentes": set(),
                    "mensalidades_vencidas": 0,
                    "valor_total": 0
                }
            
            inadimplencia_por_turma[turma_nome]["alunos_inadimplentes"].add(aluno_nome)
            inadimplencia_por_turma[turma_nome]["mensalidades_vencidas"] += 1
            inadimplencia_por_turma[turma_nome]["valor_total"] += valor
            
            # Por aluno
            if aluno_id not in inadimplencia_por_aluno:
                inadimplencia_por_aluno[aluno_id] = {
                    "nome": aluno_nome,
                    "turma": turma_nome,
                    "mensalidades_vencidas": [],
                    "total_valor": 0,
                    "count_mensalidades": 0
                }
            
            inadimplencia_por_aluno[aluno_id]["mensalidades_vencidas"].append({
                "mes_referencia": mensalidade["mes_referencia"],
                "valor": valor,
                "data_vencimento": mensalidade["data_vencimento"],
                "dias_vencido": (datetime.strptime(data_referencia, "%Y-%m-%d") - 
                               datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d")).days
            })
            inadimplencia_por_aluno[aluno_id]["total_valor"] += valor
            inadimplencia_por_aluno[aluno_id]["count_mensalidades"] += 1
        
        # Converter sets para listas e calcular totais
        for turma_data in inadimplencia_por_turma.values():
            turma_data["alunos_inadimplentes"] = list(turma_data["alunos_inadimplentes"])
            turma_data["total_alunos_inadimplentes"] = len(turma_data["alunos_inadimplentes"])
        
        # Ordenar alunos por valor devido (maior primeiro)
        alunos_ordenados = sorted(
            inadimplencia_por_aluno.values(),
            key=lambda x: x["total_valor"],
            reverse=True
        )
        
        relatorio = {
            "data_referencia": data_referencia,
            "resumo": {
                "total_alunos_inadimplentes": len(inadimplencia_por_aluno),
                "total_mensalidades_vencidas": len(mensalidades_vencidas.data),
                "total_valor_vencido": total_valor_vencido,
                "total_valor_vencido_fmt": formatar_valor_br(total_valor_vencido),
                "turmas_afetadas": len(inadimplencia_por_turma)
            },
            "por_turma": inadimplencia_por_turma,
            "por_aluno": alunos_ordenados,
            "detalhes_mensalidades": mensalidades_vencidas.data
        }
        
        return {
            "success": True,
            "relatorio": relatorio
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# ⚙️ CONFIGURAÇÕES E MANUTENÇÃO
# ==========================================================

def executar_manutencao_completa() -> Dict:
    """
    Executa rotina completa de manutenção do sistema
    
    Returns:
        Dict: {"success": bool, "resultados": Dict}
    """
    try:
        resultados = {
            "inicio": obter_timestamp(),
            "operacoes": [],
            "sucessos": 0,
            "erros": 0
        }
        
        # 1. Verificar e corrigir extrato duplicado
        resultado_duplicados = verificar_e_corrigir_extrato_duplicado()
        resultados["operacoes"].append({
            "operacao": "Correção de extratos duplicados",
            "sucesso": resultado_duplicados.get("success", False),
            "detalhes": resultado_duplicados
        })
        
        if resultado_duplicados.get("success"):
            resultados["sucessos"] += 1
        else:
            resultados["erros"] += 1
        
        # 2. Corrigir status do extrato com pagamentos
        resultado_status = corrigir_status_extrato_com_pagamentos()
        resultados["operacoes"].append({
            "operacao": "Correção de status do extrato",
            "sucesso": resultado_status.get("success", False),
            "detalhes": resultado_status
        })
        
        if resultado_status.get("success"):
            resultados["sucessos"] += 1
        else:
            resultados["erros"] += 1
        
        # 3. Atualizar responsáveis do extrato PIX
        resultado_responsaveis = atualizar_responsaveis_extrato_pix()
        resultados["operacoes"].append({
            "operacao": "Atualização de responsáveis no extrato",
            "sucesso": resultado_responsaveis.get("success", False),
            "detalhes": resultado_responsaveis
        })
        
        if resultado_responsaveis.get("success"):
            resultados["sucessos"] += 1
        else:
            resultados["erros"] += 1
        
        # 4. Verificar consistência final
        resultado_consistencia = verificar_consistencia_extrato_pagamentos()
        resultados["operacoes"].append({
            "operacao": "Verificação de consistência",
            "sucesso": resultado_consistencia.get("success", False),
            "detalhes": resultado_consistencia
        })
        
        if resultado_consistencia.get("success"):
            resultados["sucessos"] += 1
        else:
            resultados["erros"] += 1
        
        resultados["fim"] = obter_timestamp()
        resultados["duracao"] = "Concluída"
        
        return {
            "success": True,
            "resultados": resultados,
            "message": f"Manutenção concluída: {resultados['sucessos']} sucessos, {resultados['erros']} erros"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def obter_configuracoes_sistema() -> Dict:
    """
    Obtém configurações e metadados do sistema
    
    Returns:
        Dict: {"success": bool, "configuracoes": Dict}
    """
    try:
        # Contar registros em cada tabela
        tabelas = ["alunos", "responsaveis", "turmas", "alunos_responsaveis", 
                  "pagamentos", "mensalidades", "extrato_pix"]
        
        contadores = {}
        for tabela in tabelas:
            try:
                response = supabase.table(tabela).select("id", count="exact").execute()
                contadores[tabela] = response.count if hasattr(response, 'count') else len(response.data)
            except:
                contadores[tabela] = "Erro ao contar"
        
        # Última atualização de cada tabela (aproximada)
        ultimas_atualizacoes = {}
        for tabela in ["alunos", "responsaveis", "pagamentos", "mensalidades"]:
            try:
                if tabela in ["alunos", "responsaveis"]:
                    campo_data = "updated_at"
                else:
                    campo_data = "updated_at"
                
                response = supabase.table(tabela).select(campo_data).order(campo_data, desc=True).limit(1).execute()
                if response.data and response.data[0].get(campo_data):
                    ultimas_atualizacoes[tabela] = response.data[0][campo_data]
                else:
                    ultimas_atualizacoes[tabela] = "Não disponível"
            except:
                ultimas_atualizacoes[tabela] = "Erro ao obter"
        
        configuracoes = {
            "sistema": {
                "nome": "Sistema de Gestão Escolar",
                "versao": "1.0.0",
                "data_consulta": obter_timestamp()
            },
            "banco_dados": {
                "total_tabelas": len(tabelas),
                "contadores_registros": contadores,
                "ultimas_atualizacoes": ultimas_atualizacoes
            },
            "estatisticas_rapidas": {
                "total_alunos": contadores.get("alunos", 0),
                "total_responsaveis": contadores.get("responsaveis", 0),
                "total_pagamentos": contadores.get("pagamentos", 0),
                "total_mensalidades": contadores.get("mensalidades", 0)
            }
        }
        
        return {
            "success": True,
            "configuracoes": configuracoes
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)} 