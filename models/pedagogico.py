#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 MODELO PEDAGÓGICO - Gestão de Alunos, Responsáveis e Turmas
==============================================================

Contém todas as funções relacionadas ao domínio pedagógico:
- Gestão de alunos e responsáveis
- Vínculos e relacionamentos
- Consultas e filtros educacionais
- Cadastros e atualizações
"""

from typing import Dict, List, Optional
from .base import (
    supabase, AlunoSchema, ResponsavelSchema, TurmaSchema, AlunoResponsavelSchema,
    gerar_id_aluno, gerar_id_responsavel, gerar_id_vinculo,
    tratar_valores_none, obter_timestamp, formatar_data_br, formatar_valor_br,
    TIPOS_RELACAO, TURNOS_VALIDOS, gerar_id_cobranca, gerar_grupo_cobranca,
    TIPOS_COBRANCA, TIPOS_COBRANCA_DISPLAY, PRIORIDADES_COBRANCA
)

# ==========================================================
# 🎓 GESTÃO DE TURMAS
# ==========================================================

def listar_turmas_disponiveis() -> Dict:
    """
    Lista todas as turmas disponíveis no sistema
    
    Returns:
        Dict: {"success": bool, "turmas": List[str], "count": int}
    """
    try:
        response = supabase.table("turmas").select("nome_turma").order("nome_turma").execute()
        
        turmas = [turma["nome_turma"] for turma in response.data]
        
        return {
            "success": True,
            "turmas": turmas,
            "count": len(turmas)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def obter_turma_por_id(id_turma: str) -> Dict:
    """
    Obtém dados completos de uma turma pelo ID
    
    Args:
        id_turma: ID da turma
        
    Returns:
        Dict: {"success": bool, "turma": Dict, "total_alunos": int}
    """
    try:
        # Buscar dados da turma
        turma_response = supabase.table("turmas").select("*").eq("id", id_turma).execute()
        
        if not turma_response.data:
            return {"success": False, "error": f"Turma {id_turma} não encontrada"}
        
        turma = turma_response.data[0]
        
        # Contar alunos da turma
        alunos_response = supabase.table("alunos").select("id").eq("id_turma", id_turma).execute()
        total_alunos = len(alunos_response.data)
        
        return {
            "success": True,
            "turma": turma,
            "total_alunos": total_alunos
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def obter_mapeamento_turmas() -> Dict:
    """
    Obtém mapeamento completo de turmas (nome -> id)
    
    Returns:
        Dict: {"success": bool, "mapeamento": Dict[str, str]}
    """
    try:
        response = supabase.table("turmas").select("id, nome_turma").order("nome_turma").execute()
        
        mapeamento = {turma["nome_turma"]: turma["id"] for turma in response.data}
        
        return {
            "success": True,
            "mapeamento": mapeamento,
            "total_turmas": len(mapeamento)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 👨‍🎓 GESTÃO DE ALUNOS
# ==========================================================

def buscar_alunos_para_dropdown(termo_busca: str = "") -> Dict:
    """
    Busca alunos para exibição em dropdown com filtro incremental
    
    Args:
        termo_busca: Termo para filtrar por nome (mínimo 2 caracteres)
        
    Returns:
        Dict: {"success": bool, "opcoes": List[Dict], "count": int}
    """
    try:
        query = supabase.table("alunos").select("""
            id, nome, 
            turmas!inner(nome_turma)
        """)
        
        if termo_busca and len(termo_busca) >= 2:
            query = query.ilike("nome", f"%{termo_busca}%")
        
        query = query.limit(20).order("nome")
        response = query.execute()
        
        # Formatar para dropdown
        opcoes = []
        for aluno in response.data:
            opcao = {
                "id": aluno["id"],
                "nome": aluno["nome"],
                "turma": aluno["turmas"]["nome_turma"],
                "label": f"{aluno['nome']} - {aluno['turmas']['nome_turma']}"
            }
            opcoes.append(opcao)
        
        return {
            "success": True,
            "opcoes": opcoes,
            "count": len(opcoes)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_mensalidades_para_cancelamento(id_aluno: str, data_saida: str) -> Dict:
    """
    Lista mensalidades que serão canceladas ao trancar matrícula
    
    Args:
        id_aluno: ID do aluno
        data_saida: Data de saída no formato YYYY-MM-DD
        
    Returns:
        Dict: {"success": bool, "mensalidades": List[Dict], "count": int}
    """
    try:
        from datetime import datetime, timedelta
        from calendar import monthrange
        
        # Buscar dados do aluno
        aluno_response = supabase.table("alunos").select("""
            id, nome, dia_vencimento, valor_mensalidade
        """).eq("id", id_aluno).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": "Aluno não encontrado"}
        
        aluno = aluno_response.data[0]
        
        if not aluno.get("dia_vencimento"):
            return {"success": False, "error": "Aluno não possui dia de vencimento configurado"}
        
        # Calcular data de corte (primeiro dia do mês seguinte à data de saída)
        data_saida_obj = datetime.strptime(data_saida, "%Y-%m-%d")
        
        # Primeiro dia do mês seguinte
        if data_saida_obj.month == 12:
            data_corte = datetime(data_saida_obj.year + 1, 1, 1)
        else:
            data_corte = datetime(data_saida_obj.year, data_saida_obj.month + 1, 1)
        
        # Buscar mensalidades do aluno que não foram pagas
        mensalidades_response = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status, observacoes
        """).eq("id_aluno", id_aluno).not_.in_("status", ["Pago", "Pago parcial", "Cancelado"]).execute()
        
        # Filtrar mensalidades que serão canceladas
        mensalidades_cancelar = []
        for mensalidade in mensalidades_response.data:
            data_vencimento = datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d")
            
            # Se a data de vencimento é igual ou posterior à data de corte, será cancelada
            if data_vencimento >= data_corte:
                mensalidades_cancelar.append({
                    "id_mensalidade": mensalidade["id_mensalidade"],
                    "mes_referencia": mensalidade["mes_referencia"],
                    "valor": float(mensalidade["valor"]),
                    "data_vencimento": mensalidade["data_vencimento"],
                    "status": mensalidade["status"],
                    "observacoes": mensalidade.get("observacoes", "")
                })
        
        # Ordenar por data de vencimento
        mensalidades_cancelar.sort(key=lambda x: x["data_vencimento"])
        
        return {
            "success": True,
            "mensalidades": mensalidades_cancelar,
            "count": len(mensalidades_cancelar),
            "data_corte": data_corte.strftime("%Y-%m-%d"),
            "aluno_nome": aluno["nome"]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def trancar_matricula_aluno(id_aluno: str, data_saida: str, motivo_saida: str = "trancamento") -> Dict:
    """
    Tranca matrícula do aluno e cancela mensalidades futuras
    
    Args:
        id_aluno: ID do aluno
        data_saida: Data de saída no formato YYYY-MM-DD
        motivo_saida: Motivo do trancamento
        
    Returns:
        Dict: {"success": bool, "mensalidades_canceladas": int, "data": Dict}
    """
    try:
        # 1. Verificar se aluno existe e não está já trancado
        aluno_response = supabase.table("alunos").select("""
            id, nome, situacao, data_saida
        """).eq("id", id_aluno).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": "Aluno não encontrado"}
        
        aluno = aluno_response.data[0]
        
        if aluno.get("situacao") == "trancado":
            return {"success": False, "error": "Aluno já está com matrícula trancada"}
        
        # 2. Listar mensalidades que serão canceladas
        mensalidades_resultado = listar_mensalidades_para_cancelamento(id_aluno, data_saida)
        
        if not mensalidades_resultado.get("success"):
            return {"success": False, "error": f"Erro ao listar mensalidades: {mensalidades_resultado.get('error')}"}
        
        mensalidades_cancelar = mensalidades_resultado["mensalidades"]
        
        # 3. Atualizar situação do aluno
        dados_update_aluno = {
            "situacao": "trancado",
            "data_saida": data_saida,
            "motivo_saida": motivo_saida,
            "updated_at": obter_timestamp()
        }
        
        aluno_update_response = supabase.table("alunos").update(dados_update_aluno).eq("id", id_aluno).execute()
        
        if not aluno_update_response.data:
            return {"success": False, "error": "Erro ao atualizar situação do aluno"}
        
        # 4. Cancelar mensalidades futuras
        mensalidades_canceladas = 0
        erros_cancelamento = []
        
        for mensalidade in mensalidades_cancelar:
            try:
                observacoes_original = mensalidade.get("observacoes", "")
                nova_observacao = f"Cancelada por trancamento de matrícula em {formatar_data_br(data_saida)}"
                
                if observacoes_original:
                    observacoes_final = f"{observacoes_original} | {nova_observacao}"
                else:
                    observacoes_final = nova_observacao
                
                dados_update_mensalidade = {
                    "status": "Cancelado",
                    "observacoes": observacoes_final,
                    "updated_at": obter_timestamp()
                }
                
                mens_update_response = supabase.table("mensalidades").update(dados_update_mensalidade).eq(
                    "id_mensalidade", mensalidade["id_mensalidade"]
                ).execute()
                
                if mens_update_response.data:
                    mensalidades_canceladas += 1
                else:
                    erros_cancelamento.append(f"Erro ao cancelar mensalidade {mensalidade['mes_referencia']}")
                    
            except Exception as e:
                erros_cancelamento.append(f"Erro ao cancelar mensalidade {mensalidade['mes_referencia']}: {str(e)}")
        
        # 5. Preparar resposta
        resultado = {
            "success": True,
            "aluno_nome": aluno["nome"],
            "data_saida": data_saida,
            "motivo_saida": motivo_saida,
            "mensalidades_canceladas": mensalidades_canceladas,
            "total_mensalidades": len(mensalidades_cancelar),
            "data": aluno_update_response.data[0],
            "mensalidades_afetadas": mensalidades_cancelar
        }
        
        # Adicionar erros se houver
        if erros_cancelamento:
            resultado["erros_cancelamento"] = erros_cancelamento
            resultado["aviso"] = f"Matrícula trancada, mas {len(erros_cancelamento)} mensalidades não puderam ser canceladas"
        
        return resultado
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_alunos_por_turmas(ids_turmas: List[str]) -> Dict:
    """
    Busca alunos por uma lista de IDs de turmas com informações completas dos responsáveis
    
    Args:
        ids_turmas: Lista de IDs das turmas para filtrar
        
    Returns:
        Dict: {"success": bool, "alunos_por_turma": Dict, "total_alunos": int}
    """
    try:
        if not ids_turmas:
            return {
                "success": True,
                "alunos": [],
                "count": 0,
                "message": "Nenhuma turma selecionada"
            }
        
        # Buscar alunos das turmas selecionadas
        response = supabase.table("alunos").select("""
            id, nome, turno, data_nascimento, dia_vencimento, 
            data_matricula, valor_mensalidade, id_turma,
            turmas!inner(id, nome_turma)
        """).in_("id_turma", ids_turmas).order("nome").execute()
        
        if not response.data:
            return {
                "success": True,
                "alunos": [],
                "count": 0,
                "message": f"Nenhum aluno encontrado nas {len(ids_turmas)} turmas selecionadas"
            }
        
        # Agrupar por turma e buscar responsáveis
        alunos_por_turma = {}
        total_alunos = 0
        
        for aluno in response.data:
            turma_nome = aluno["turmas"]["nome_turma"]
            turma_id = aluno["turmas"]["id"]
            
            if turma_nome not in alunos_por_turma:
                alunos_por_turma[turma_nome] = {
                    "id_turma": turma_id,
                    "nome_turma": turma_nome,
                    "alunos": []
                }
            
            # Buscar responsáveis do aluno com todos os campos
            responsaveis_response = supabase.table("alunos_responsaveis").select("""
                tipo_relacao, responsavel_financeiro,
                responsaveis!inner(id, nome, cpf, telefone, email, endereco)
            """).eq("id_aluno", aluno["id"]).execute()
            
            # Organizar responsáveis
            responsaveis_info = []
            responsavel_financeiro_nome = "Não informado"
            
            for vinculo in responsaveis_response.data:
                resp_info = {
                    "id": vinculo["responsaveis"]["id"],
                    "nome": vinculo["responsaveis"]["nome"],
                    "cpf": vinculo["responsaveis"].get("cpf"),
                    "telefone": vinculo["responsaveis"].get("telefone"), 
                    "email": vinculo["responsaveis"].get("email"),
                    "endereco": vinculo["responsaveis"].get("endereco"),
                    "tipo_relacao": vinculo.get("tipo_relacao", "responsável"),
                    "responsavel_financeiro": vinculo.get("responsavel_financeiro", False)
                }
                responsaveis_info.append(resp_info)
                
                # Identificar responsável financeiro
                if vinculo.get("responsavel_financeiro", False):
                    responsavel_financeiro_nome = vinculo["responsaveis"]["nome"]
            
            # Se não há responsável financeiro marcado, usar o primeiro
            if responsavel_financeiro_nome == "Não informado" and responsaveis_info:
                responsavel_financeiro_nome = responsaveis_info[0]["nome"]
            
            # Formatar dados do aluno com tratamento de valores None
            aluno_formatado = {
                "id": aluno["id"],
                "nome": aluno["nome"] or "Nome não informado",
                "turno": aluno.get("turno") or "Não informado",
                "data_nascimento": aluno.get("data_nascimento") or "Não informado",
                "dia_vencimento": aluno.get("dia_vencimento") or "Não definido",
                "data_matricula": aluno.get("data_matricula") or "Não informado",
                "valor_mensalidade": float(aluno.get("valor_mensalidade") or 0),
                "label": f"{aluno['nome'] or 'Nome não informado'} - {turma_nome}",
                "turma_nome": turma_nome,
                "responsaveis": responsaveis_info,
                "responsavel_financeiro_nome": responsavel_financeiro_nome,
                "total_responsaveis": len(responsaveis_info)
            }
            
            alunos_por_turma[turma_nome]["alunos"].append(aluno_formatado)
            total_alunos += 1
        
        return {
            "success": True,
            "alunos_por_turma": alunos_por_turma,
            "total_alunos": total_alunos,
            "total_turmas": len(alunos_por_turma),
            "count": total_alunos
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_informacoes_completas_aluno(id_aluno: str) -> Dict:
    """
    Busca todas as informações de um aluno: dados pessoais, responsáveis e pagamentos
    
    Args:
        id_aluno: ID do aluno
        
    Returns:
        Dict: {"success": bool, "aluno": Dict, "responsaveis": List, "pagamentos": List, "mensalidades": List}
    """
    try:
        # 1. Buscar dados básicos do aluno
        aluno_response = supabase.table("alunos").select("""
            id, nome, turno, data_nascimento, dia_vencimento, 
            data_matricula, valor_mensalidade, mensalidades_geradas,
            situacao, data_saida, motivo_saida,
            turmas!inner(id, nome_turma)
        """).eq("id", id_aluno).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": f"Aluno com ID {id_aluno} não encontrado"}
        
        aluno = aluno_response.data[0]
        
        # 2. Buscar responsáveis vinculados
        responsaveis_response = supabase.table("alunos_responsaveis").select("""
            id, tipo_relacao, responsavel_financeiro,
            responsaveis!inner(
                id, nome, cpf, telefone, email, endereco
            )
        """).eq("id_aluno", id_aluno).execute()
        
        responsaveis = []
        for vinculo in responsaveis_response.data:
            resp_data = vinculo["responsaveis"].copy()
            resp_data["tipo_relacao"] = vinculo.get("tipo_relacao")
            resp_data["responsavel_financeiro"] = vinculo.get("responsavel_financeiro", False)
            resp_data["id_vinculo"] = vinculo.get("id")
            responsaveis.append(resp_data)
        
        # 3. Buscar pagamentos do aluno
        pagamentos_response = supabase.table("pagamentos").select("""
            id_pagamento, data_pagamento, valor, tipo_pagamento, 
            forma_pagamento, descricao, origem_extrato,
            responsaveis!inner(nome)
        """).eq("id_aluno", id_aluno).order("data_pagamento", desc=True).execute()
        
        pagamentos = []
        total_pago = 0
        for pagamento in pagamentos_response.data:
            pag_formatado = {
                "id_pagamento": pagamento["id_pagamento"],
                "data_pagamento": pagamento["data_pagamento"],
                "valor": float(pagamento["valor"]),
                "tipo_pagamento": pagamento["tipo_pagamento"],
                "forma_pagamento": pagamento.get("forma_pagamento", "N/A"),
                "descricao": pagamento.get("descricao", ""),
                "origem_extrato": pagamento.get("origem_extrato", False),
                "nome_responsavel": pagamento["responsaveis"]["nome"] if pagamento.get("responsaveis") else "N/A"
            }
            pagamentos.append(pag_formatado)
            total_pago += pag_formatado["valor"]
        
        # 4. Buscar mensalidades do aluno
        mensalidades_response = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, 
            status, observacoes, data_pagamento
        """).eq("id_aluno", id_aluno).order("data_vencimento", desc=True).execute()
        
        mensalidades = []
        for mensalidade in mensalidades_response.data:
            # Calcular status real baseado na data e status do banco
            from datetime import datetime
            data_hoje = datetime.now().date()
            data_vencimento = datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d").date()
            
            if mensalidade["status"] == "Cancelado":
                status_real = "Cancelado"
                status_cor = "secondary"
            elif mensalidade["status"] in ["Pago", "Pago parcial"]:
                status_real = mensalidade["status"]
                status_cor = "success" if status_real == "Pago" else "warning"
            elif data_vencimento < data_hoje:
                status_real = "Atrasado"
                status_cor = "error"
            else:
                status_real = "A vencer"
                status_cor = "info"
            
            mens_formatada = {
                "id_mensalidade": mensalidade["id_mensalidade"],
                "mes_referencia": mensalidade["mes_referencia"],
                "valor": float(mensalidade["valor"]),
                "data_vencimento": mensalidade["data_vencimento"],
                "status": mensalidade["status"],
                "status_real": status_real,
                "status_cor": status_cor,
                "observacoes": mensalidade.get("observacoes"),
                "data_pagamento": mensalidade.get("data_pagamento")
            }
            mensalidades.append(mens_formatada)
        
        # 5. Calcular estatísticas
        mensalidades_pagas = len([m for m in mensalidades if m["status"] in ["Pago", "Pago parcial"]])
        mensalidades_canceladas = len([m for m in mensalidades if m["status_real"] == "Cancelado"])
        mensalidades_pendentes = len([m for m in mensalidades if m["status_real"] in ["A vencer", "Atrasado"]])
        mensalidades_vencidas = len([m for m in mensalidades if m["status_real"] == "Atrasado"])
        
        # Formatar dados do aluno
        aluno_formatado = {
            "id": aluno["id"],
            "nome": aluno["nome"],
            "turma_nome": aluno["turmas"]["nome_turma"],
            "turma_id": aluno["turmas"]["id"],
            "turno": aluno.get("turno", "N/A"),
            "data_nascimento": aluno.get("data_nascimento"),
            "dia_vencimento": aluno.get("dia_vencimento"),
            "data_matricula": aluno.get("data_matricula"),
            "valor_mensalidade": float(aluno.get("valor_mensalidade", 0)),
            "mensalidades_geradas": aluno.get("mensalidades_geradas", False),
            "situacao": aluno.get("situacao", "ativo"),
            "data_saida": aluno.get("data_saida"),
            "motivo_saida": aluno.get("motivo_saida")
        }
        
        # Estatísticas financeiras
        estatisticas = {
            "total_responsaveis": len(responsaveis),
            "total_pagamentos": len(pagamentos),
            "total_pago": total_pago,
            "total_mensalidades": len(mensalidades),
            "mensalidades_pagas": mensalidades_pagas,
            "mensalidades_canceladas": mensalidades_canceladas,
            "mensalidades_pendentes": mensalidades_pendentes,
            "mensalidades_vencidas": mensalidades_vencidas,
            "valor_mensalidade": aluno_formatado["valor_mensalidade"]
        }
        
        return {
            "success": True,
            "aluno": aluno_formatado,
            "responsaveis": responsaveis,
            "pagamentos": pagamentos,
            "mensalidades": mensalidades,
            "estatisticas": estatisticas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_aluno_campos(id_aluno: str, campos: Dict) -> Dict:
    """
    Atualiza campos específicos de um aluno
    
    Args:
        id_aluno: ID do aluno
        campos: Dict com campos a atualizar
        
    Returns:
        Dict: {"success": bool, "campos_atualizados": List, "data": Dict}
    """
    try:
        # Campos permitidos
        campos_permitidos = [
            "nome", "turno", "data_nascimento", "dia_vencimento", 
            "data_matricula", "valor_mensalidade", "mensalidades_geradas",
            "situacao", "data_saida", "motivo_saida"
        ]
        
        # Filtrar apenas campos permitidos
        dados_update = {k: v for k, v in campos.items() if k in campos_permitidos}
        
        if not dados_update:
            return {"success": False, "error": "Nenhum campo válido para atualizar"}
        
        dados_update["updated_at"] = obter_timestamp()
        
        response = supabase.table("alunos").update(dados_update).eq("id", id_aluno).execute()
        
        if response.data:
            return {
                "success": True,
                "campos_atualizados": list(dados_update.keys()),
                "data": response.data[0]
            }
        else:
            return {"success": False, "error": "Aluno não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_aluno_e_vincular(dados_aluno: Dict, 
                               dados_responsavel: Optional[Dict] = None,
                               id_responsavel: Optional[str] = None,
                               tipo_relacao: str = "responsavel",
                               responsavel_financeiro: bool = True) -> Dict:
    """
    Cadastra novo aluno com vínculo a responsável (novo ou existente)
    
    Args:
        dados_aluno: Dict com dados completos do aluno
        dados_responsavel: Dict com dados do novo responsável (opcional)
        id_responsavel: ID do responsável existente (opcional)
        tipo_relacao: Tipo de relação com o responsável
        responsavel_financeiro: Se o responsável é financeiro
        
    Returns:
        Dict: {"success": bool, "id_aluno": str, "id_responsavel": str, "vinculo_criado": bool}
    """
    try:
        # Validação: deve ter responsável novo OU existente, não ambos
        if dados_responsavel and id_responsavel:
            return {"success": False, "error": "Especifique apenas dados_responsavel OU id_responsavel, não ambos"}
        
        if not dados_responsavel and not id_responsavel:
            return {"success": False, "error": "Deve especificar dados_responsavel ou id_responsavel"}
        
        # 1. Validar turma existe
        if dados_aluno.get('id_turma'):
            turma_check = supabase.table("turmas").select("id, nome_turma").eq("id", dados_aluno.get('id_turma')).execute()
            if not turma_check.data:
                return {"success": False, "error": f"Turma com ID {dados_aluno.get('id_turma')} não encontrada"}
        
        # 2. Se responsável novo, cadastrar primeiro
        if dados_responsavel:
            id_responsavel_final = gerar_id_responsavel()
            
            dados_cadastro_resp = {
                "id": id_responsavel_final,
                "nome": dados_responsavel.get("nome"),
                "cpf": dados_responsavel.get("cpf"),
                "telefone": dados_responsavel.get("telefone"),
                "email": dados_responsavel.get("email"),
                "endereco": dados_responsavel.get("endereco"),
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }
            
            # Remover campos None/vazios
            dados_cadastro_resp = {k: v for k, v in dados_cadastro_resp.items() if v is not None and v != ""}
            
            resp_response = supabase.table("responsaveis").insert(dados_cadastro_resp).execute()
            
            if not resp_response.data:
                return {"success": False, "error": "Erro ao cadastrar responsável"}
            
            id_responsavel_final = resp_response.data[0]["id"]
        else:
            # Validar responsável existente
            resp_check = supabase.table("responsaveis").select("id, nome").eq("id", id_responsavel).execute()
            if not resp_check.data:
                return {"success": False, "error": f"Responsável com ID {id_responsavel} não encontrado"}
            id_responsavel_final = id_responsavel
        
        # 3. Cadastrar aluno
        id_aluno = gerar_id_aluno()
        
        dados_cadastro_aluno = {
            "id": id_aluno,
            "nome": dados_aluno.get("nome"),
            "id_turma": dados_aluno.get("id_turma"),
            "turno": dados_aluno.get("turno"),
            "data_nascimento": dados_aluno.get("data_nascimento"),
            "dia_vencimento": dados_aluno.get("dia_vencimento"),
            "valor_mensalidade": dados_aluno.get("valor_mensalidade"),
            "data_matricula": dados_aluno.get("data_matricula"),
            "mensalidades_geradas": False,  # Default para novo aluno
            "inserted_at": obter_timestamp(),
            "updated_at": obter_timestamp()
        }
        
        # Remover campos None/vazios
        dados_cadastro_aluno = {k: v for k, v in dados_cadastro_aluno.items() if v is not None and v != ""}
        
        aluno_response = supabase.table("alunos").insert(dados_cadastro_aluno).execute()
        
        if not aluno_response.data:
            # Se falhar aluno e responsável foi criado, remover responsável
            if dados_responsavel:
                supabase.table("responsaveis").delete().eq("id", id_responsavel_final).execute()
            return {"success": False, "error": "Erro ao cadastrar aluno"}
        
        # 4. Criar vínculo
        id_vinculo = gerar_id_vinculo()
        
        dados_vinculo = {
            "id": id_vinculo,
            "id_aluno": id_aluno,
            "id_responsavel": id_responsavel_final,
            "tipo_relacao": tipo_relacao,
            "responsavel_financeiro": responsavel_financeiro,
            "created_at": obter_timestamp(),
            "updated_at": obter_timestamp()
        }
        
        vinculo_response = supabase.table("alunos_responsaveis").insert(dados_vinculo).execute()
        
        if not vinculo_response.data:
            # Se falhar vínculo, remover aluno e responsável (se foi criado)
            supabase.table("alunos").delete().eq("id", id_aluno).execute()
            if dados_responsavel:
                supabase.table("responsaveis").delete().eq("id", id_responsavel_final).execute()
            return {"success": False, "error": "Erro ao criar vínculo"}
        
        resultado = {
            "success": True,
            "id_aluno": id_aluno,
            "id_responsavel": id_responsavel_final,
            "id_vinculo": id_vinculo,
            "vinculo_criado": True,
            "nome_aluno": dados_aluno.get("nome"),
            "aluno_data": aluno_response.data[0]
        }
        
        # Adicionar informações do responsável
        if dados_responsavel:
            resultado["responsavel_criado"] = True
            resultado["nome_responsavel"] = dados_responsavel.get("nome")
        else:
            resultado["responsavel_criado"] = False
            resp_info = supabase.table("responsaveis").select("nome").eq("id", id_responsavel_final).execute()
            resultado["nome_responsavel"] = resp_info.data[0]["nome"] if resp_info.data else "N/A"
        
        return resultado
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 👨‍👩‍👧‍👦 GESTÃO DE RESPONSÁVEIS
# ==========================================================

def buscar_responsaveis_para_dropdown(termo_busca: str = "") -> Dict:
    """
    Busca responsáveis para exibir em dropdown com filtro
    
    Args:
        termo_busca: Termo para filtrar responsáveis por nome
        
    Returns:
        Dict: {"success": bool, "opcoes": List[Dict], "total": int}
    """
    try:
        # Query base
        query = supabase.table("responsaveis").select("id, nome, telefone, email")
        
        # Aplicar filtro se fornecido
        if termo_busca and len(termo_busca.strip()) > 0:
            # Filtrar por nome (case insensitive)
            query = query.ilike("nome", f"%{termo_busca.strip()}%")
        
        # Executar query com limite
        response = query.limit(50).execute()
        
        if not response.data:
            return {
                "success": True,
                "opcoes": [],
                "total": 0
            }
        
        # Formatar opções para dropdown
        opcoes = []
        for resp in response.data:
            label = f"{resp['nome']}"
            
            # Adicionar informações adicionais se disponíveis
            detalhes = []
            if resp.get('telefone'):
                detalhes.append(f"Tel: {resp['telefone']}")
            if resp.get('email'):
                detalhes.append(f"Email: {resp['email']}")
            
            if detalhes:
                label += f" ({', '.join(detalhes)})"
            
            opcoes.append({
                "id": resp["id"],
                "nome": resp["nome"],
                "label": label,
                "telefone": resp.get("telefone"),
                "email": resp.get("email")
            })
        
        return {
            "success": True,
            "opcoes": opcoes,
            "total": len(opcoes),
            "termo_busca": termo_busca
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "opcoes": [],
            "total": 0
        }

def listar_responsaveis_aluno(id_aluno: str) -> Dict:
    """
    Lista todos os responsáveis vinculados a um aluno
    
    Args:
        id_aluno: ID do aluno
        
    Returns:
        Dict: {"success": bool, "responsaveis": List[Dict], "count": int}
    """
    try:
        response = supabase.table("alunos_responsaveis").select("""
            *,
            responsaveis!inner(*)
        """).eq("id_aluno", id_aluno).execute()
        
        responsaveis = []
        for vinculo in response.data:
            resp_data = vinculo["responsaveis"].copy()
            resp_data["tipo_relacao"] = vinculo.get("tipo_relacao")
            resp_data["responsavel_financeiro"] = vinculo.get("responsavel_financeiro", False)
            resp_data["id_vinculo"] = vinculo.get("id")
            responsaveis.append(resp_data)
        
        return {
            "success": True,
            "responsaveis": responsaveis,
            "count": len(responsaveis)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_alunos_vinculados_responsavel(id_responsavel: str) -> Dict:
    """
    Lista todos os alunos vinculados a um responsável específico
    
    Args:
        id_responsavel: ID do responsável
        
    Returns:
        Dict: {"success": bool, "alunos": List[Dict], "count": int}
    """
    try:
        response = supabase.table("alunos_responsaveis").select("""
            *,
            alunos!inner(
                id, nome, id_turma, dia_vencimento, valor_mensalidade,
                turmas!inner(nome_turma)
            )
        """).eq("id_responsavel", id_responsavel).execute()
        
        alunos = []
        for vinculo in response.data:
            aluno_data = vinculo["alunos"].copy()
            aluno_data["tipo_relacao"] = vinculo.get("tipo_relacao")
            aluno_data["responsavel_financeiro"] = vinculo.get("responsavel_financeiro", False)
            aluno_data["id_vinculo"] = vinculo.get("id")
            
            # Formatar nome completo para exibição
            turma_nome = aluno_data.get("turmas", {}).get("nome_turma", "N/A")
            aluno_data["label"] = f"{aluno_data['nome']} - {turma_nome}"
            
            alunos.append(aluno_data)
        
        return {
            "success": True,
            "alunos": alunos,
            "count": len(alunos),
            "tem_multiplos_alunos": len(alunos) > 1
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_responsavel_e_vincular(dados_responsavel: Dict, 
                                    id_aluno: str,
                                    tipo_relacao: str = "responsavel",
                                    responsavel_financeiro: bool = True) -> Dict:
    """
    Cadastra responsável e vincula ao aluno em uma operação
    
    Args:
        dados_responsavel: Dict com nome, cpf, telefone, email, endereco
        id_aluno: ID do aluno para vincular
        tipo_relacao: Tipo de relação (pai, mãe, etc.)
        responsavel_financeiro: Se é responsável financeiro
        
    Returns:
        Dict: {"success": bool, "id_responsavel": str, "id_vinculo": str}
    """
    try:
        # 1. Validar aluno existe
        aluno_check = supabase.table("alunos").select("id, nome").eq("id", id_aluno).execute()
        if not aluno_check.data:
            return {"success": False, "error": f"Aluno com ID {id_aluno} não encontrado"}
        
        # 2. Cadastrar responsável
        id_responsavel = gerar_id_responsavel()
        
        dados_cadastro = {
            "id": id_responsavel,
            "nome": dados_responsavel.get("nome"),
            "cpf": dados_responsavel.get("cpf"),
            "telefone": dados_responsavel.get("telefone"),
            "email": dados_responsavel.get("email"),
            "endereco": dados_responsavel.get("endereco"),
            "tipo_relacao": tipo_relacao,
            "responsavel_financeiro": responsavel_financeiro,
            "inserted_at": obter_timestamp(),
            "updated_at": obter_timestamp()
        }
        
        # Remover campos None/vazios
        dados_cadastro = {k: v for k, v in dados_cadastro.items() if v is not None and v != ""}
        
        resp_response = supabase.table("responsaveis").insert(dados_cadastro).execute()
        
        if not resp_response.data:
            return {"success": False, "error": "Erro ao cadastrar responsável"}
        
        # 3. Criar vínculo
        vinculo_resultado = vincular_aluno_responsavel(id_aluno, id_responsavel, tipo_relacao, responsavel_financeiro)
        
        if not vinculo_resultado.get("success"):
            # Se falhar vínculo, remover responsável
            supabase.table("responsaveis").delete().eq("id", id_responsavel).execute()
            return {"success": False, "error": f"Erro ao criar vínculo: {vinculo_resultado.get('error')}"}
        
        return {
            "success": True,
            "id_responsavel": id_responsavel,
            "id_vinculo": vinculo_resultado["id_vinculo"],
            "nome_responsavel": dados_responsavel.get("nome"),
            "nome_aluno": aluno_check.data[0]["nome"]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def verificar_responsavel_existe(nome: str) -> Dict:
    """
    Verifica se responsável já existe pelo nome
    
    Args:
        nome: Nome do responsável
        
    Returns:
        Dict: {"success": bool, "existe": bool, "responsaveis_similares": List}
    """
    try:
        response = supabase.table("responsaveis").select("id, nome").ilike("nome", f"%{nome}%").execute()
        
        return {
            "success": True,
            "existe": len(response.data) > 0,
            "responsaveis_similares": response.data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🔗 GESTÃO DE VÍNCULOS
# ==========================================================

def vincular_aluno_responsavel(id_aluno: str, id_responsavel: str, 
                              tipo_relacao: str, responsavel_financeiro: bool = False) -> Dict:
    """
    Vincula um aluno a um responsável
    
    Args:
        id_aluno: ID do aluno
        id_responsavel: ID do responsável
        tipo_relacao: Tipo de relação
        responsavel_financeiro: Se é responsável financeiro
        
    Returns:
        Dict: {"success": bool, "id_vinculo": str}
    """
    try:
        # Verificar se vínculo já existe
        check_vinculo = supabase.table("alunos_responsaveis").select("id").eq(
            "id_aluno", id_aluno
        ).eq("id_responsavel", id_responsavel).execute()
        
        if check_vinculo.data:
            return {"success": False, "error": "Vínculo já existe entre este responsável e aluno"}
        
        # Criar vínculo
        id_vinculo = gerar_id_vinculo()
        
        dados_vinculo = {
            "id": id_vinculo,
            "id_aluno": id_aluno,
            "id_responsavel": id_responsavel,
            "tipo_relacao": tipo_relacao,
            "responsavel_financeiro": responsavel_financeiro,
            "created_at": obter_timestamp(),
            "updated_at": obter_timestamp()
        }
        
        response = supabase.table("alunos_responsaveis").insert(dados_vinculo).execute()
        
        if response.data:
            return {
                "success": True,
                "id_vinculo": id_vinculo,
                "message": "Responsável vinculado ao aluno com sucesso"
            }
        else:
            return {"success": False, "error": "Erro ao criar vínculo"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_vinculo_responsavel(id_vinculo: str, 
                                tipo_relacao: Optional[str] = None,
                                responsavel_financeiro: Optional[bool] = None) -> Dict:
    """
    Atualiza vínculo entre aluno e responsável
    
    Args:
        id_vinculo: ID do vínculo
        tipo_relacao: Novo tipo de relação (opcional)
        responsavel_financeiro: Novo status financeiro (opcional)
        
    Returns:
        Dict: {"success": bool, "data": Dict}
    """
    try:
        dados_update = {"updated_at": obter_timestamp()}
        
        if tipo_relacao is not None:
            dados_update["tipo_relacao"] = tipo_relacao
        if responsavel_financeiro is not None:
            dados_update["responsavel_financeiro"] = responsavel_financeiro
        
        response = supabase.table("alunos_responsaveis").update(dados_update).eq("id", id_vinculo).execute()
        
        if response.data:
            return {"success": True, "data": response.data[0]}
        else:
            return {"success": False, "error": "Vínculo não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def remover_vinculo_responsavel(id_vinculo: str) -> Dict:
    """
    Remove vínculo entre aluno e responsável
    
    Args:
        id_vinculo: ID do vínculo
        
    Returns:
        Dict: {"success": bool, "message": str}
    """
    try:
        response = supabase.table("alunos_responsaveis").delete().eq("id", id_vinculo).execute()
        
        if response.data:
            return {"success": True, "message": "Vínculo removido com sucesso"}
        else:
            return {"success": False, "error": "Vínculo não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_dados_completos_alunos_responsavel(id_responsavel: str) -> Dict:
    """
    Busca dados completos dos alunos vinculados ao responsável
    Incluindo informações financeiras e da turma
    
    Args:
        id_responsavel: ID do responsável
        
    Returns:
        Dict: {"success": bool, "alunos": List[Dict], "count": int}
    """
    try:
        response = supabase.table("alunos_responsaveis").select("""
            *,
            alunos!inner(
                id, nome, turno, data_nascimento, dia_vencimento, 
                data_matricula, valor_mensalidade,
                turmas!inner(nome_turma)
            )
        """).eq("id_responsavel", id_responsavel).execute()
        
        alunos = []
        for vinculo in response.data:
            aluno_data = vinculo["alunos"].copy()
            aluno_data["tipo_relacao"] = vinculo.get("tipo_relacao")
            aluno_data["responsavel_financeiro"] = vinculo.get("responsavel_financeiro", False)
            aluno_data["id_vinculo"] = vinculo.get("id")
            
            # Formatar informações adicionais
            aluno_data["turma_nome"] = aluno_data.get("turmas", {}).get("nome_turma", "N/A")
            aluno_data["valor_mensalidade_fmt"] = formatar_valor_br(aluno_data.get('valor_mensalidade', 0))
            aluno_data["dia_vencimento_fmt"] = f"Dia {aluno_data.get('dia_vencimento', 'N/A')}"
            
            alunos.append(aluno_data)
        
        return {
            "success": True,
            "alunos": alunos,
            "count": len(alunos),
            "tem_multiplos_alunos": len(alunos) > 1
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)} 

def filtrar_alunos_por_campos_vazios(campos_vazios: List[str], 
                                    ids_turmas: Optional[List[str]] = None) -> Dict:
    """
    Filtra alunos que possuem os campos especificados vazios
    
    Args:
        campos_vazios: Lista de campos para verificar se estão vazios
        ids_turmas: Lista opcional de IDs de turmas para filtrar
        
    Returns:
        Dict: {"success": bool, "alunos": List[Dict], "count": int}
    """
    try:
        query = supabase.table("alunos").select("""
            id, nome, turno, data_nascimento, dia_vencimento, 
            data_matricula, valor_mensalidade, id_turma,
            turmas!inner(id, nome_turma)
        """)
        
        # Aplicar filtros para campos vazios
        campos_validos = ["turno", "data_nascimento", "dia_vencimento", "data_matricula", "valor_mensalidade"]
        for campo in campos_vazios:
            if campo in campos_validos:
                query = query.is_(campo, "null")
        
        # Filtrar por turmas se especificado
        if ids_turmas:
            query = query.in_("id_turma", ids_turmas)
        
        response = query.execute()
        
        if not response.data:
            return {
                "success": True,
                "alunos": [],
                "count": 0,
                "message": "Nenhum aluno encontrado com os campos vazios especificados"
            }
        
        # Para cada aluno, buscar responsáveis e identificar campos vazios
        alunos_com_detalhes = []
        for aluno in response.data:
            # Buscar responsáveis vinculados
            resp_response = supabase.table("alunos_responsaveis").select("""
                tipo_relacao, responsavel_financeiro,
                responsaveis!inner(id, nome, telefone, email, cpf, endereco)
            """).eq("id_aluno", aluno["id"]).execute()
            
            # Organizar dados dos responsáveis
            responsaveis_info = []
            responsavel_financeiro_nome = "Não informado"
            
            for vinculo in resp_response.data:
                resp_info = vinculo["responsaveis"].copy()
                resp_info["tipo_relacao"] = vinculo.get("tipo_relacao")
                resp_info["responsavel_financeiro"] = vinculo.get("responsavel_financeiro", False)
                
                # Identificar campos vazios do responsável
                campos_vazios_resp = []
                for campo_resp in ["telefone", "email", "cpf", "endereco"]:
                    if not resp_info.get(campo_resp):
                        campos_vazios_resp.append(campo_resp)
                resp_info["campos_vazios"] = campos_vazios_resp
                
                responsaveis_info.append(resp_info)
                
                # Identificar responsável financeiro
                if vinculo.get("responsavel_financeiro", False):
                    responsavel_financeiro_nome = vinculo["responsaveis"]["nome"]
            
            # Se não há responsável financeiro marcado, usar o primeiro
            if responsavel_financeiro_nome == "Não informado" and responsaveis_info:
                responsavel_financeiro_nome = responsaveis_info[0]["nome"]
            
            # Identificar campos vazios do aluno
            campos_vazios_encontrados = []
            for campo in campos_validos:
                if aluno.get(campo) is None:
                    campos_vazios_encontrados.append(campo)
            
            # Formatar dados do aluno
            aluno_completo = {
                "id": aluno["id"],
                "nome": aluno["nome"] or "Nome não informado",
                "turma_nome": aluno["turmas"]["nome_turma"],
                "turno": aluno.get("turno"),
                "data_nascimento": aluno.get("data_nascimento"),
                "dia_vencimento": aluno.get("dia_vencimento"),
                "data_matricula": aluno.get("data_matricula"),
                "valor_mensalidade": float(aluno.get("valor_mensalidade") or 0),
                "responsaveis": responsaveis_info,
                "total_responsaveis": len(responsaveis_info),
                "responsavel_financeiro_nome": responsavel_financeiro_nome,
                "campos_vazios_aluno": campos_vazios_encontrados,
                "total_campos_vazios": len(campos_vazios_encontrados),
                "label": f"{aluno['nome'] or 'Nome não informado'} - {aluno['turmas']['nome_turma']}"
            }
            
            alunos_com_detalhes.append(aluno_completo)
        
        return {
            "success": True,
            "alunos": alunos_com_detalhes,
            "count": len(alunos_com_detalhes),
            "campos_filtrados": campos_vazios,
            "turmas_filtradas": ids_turmas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_responsavel_campos(id_responsavel: str, campos: Dict) -> Dict:
    """
    Atualiza campos específicos de um responsável
    
    Args:
        id_responsavel: ID do responsável
        campos: Dict com campos a atualizar
        
    Returns:
        Dict: {"success": bool, "campos_atualizados": List[str], "data": Dict}
    """
    try:
        campos_permitidos = [
            "nome", "cpf", "telefone", "email", "endereco"
        ]
        
        dados_update = {k: v for k, v in campos.items() if k in campos_permitidos}
        
        if not dados_update:
            return {"success": False, "error": "Nenhum campo válido para atualizar"}
        
        dados_update["updated_at"] = obter_timestamp()
        
        response = supabase.table("responsaveis").update(dados_update).eq("id", id_responsavel).execute()
        
        if response.data:
            return {
                "success": True,
                "campos_atualizados": list(dados_update.keys()),
                "data": response.data[0]
            }
        else:
            return {"success": False, "error": "Responsável não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 💰 GESTÃO DE COBRANÇAS
# ==========================================================

def listar_cobrancas_aluno(id_aluno: str, incluir_pagas: bool = True) -> Dict:
    """
    Lista todas as cobranças de um aluno
    
    Args:
        id_aluno: ID do aluno
        incluir_pagas: Se deve incluir cobranças já pagas
        
    Returns:
        Dict: {"success": bool, "cobrancas": List[Dict], "count": int, "estatisticas": Dict}
    """
    try:
        query = supabase.table("cobrancas").select("""
            id_cobranca, titulo, descricao, valor, data_vencimento, data_pagamento,
            status, tipo_cobranca, grupo_cobranca, parcela_numero, parcela_total,
            observacoes, prioridade, inserted_at, updated_at,
            responsaveis!inner(id, nome)
        """).eq("id_aluno", id_aluno)
        
        if not incluir_pagas:
            query = query.neq("status", "Pago")
        
        query = query.order("data_vencimento", desc=False)
        response = query.execute()
        
        if not response.data:
            return {
                "success": True,
                "cobrancas": [],
                "count": 0,
                "estatisticas": {
                    "total_pendente": 0,
                    "valor_pendente": 0.0,
                    "total_vencido": 0,
                    "valor_vencido": 0.0,
                    "total_pago": 0,
                    "valor_pago": 0.0
                }
            }
        
        # Processar cobranças e calcular estatísticas
        cobrancas_formatadas = []
        estatisticas = {
            "total_pendente": 0,
            "valor_pendente": 0.0,
            "total_vencido": 0,
            "valor_vencido": 0.0,
            "total_pago": 0,
            "valor_pago": 0.0
        }
        
        from datetime import datetime
        data_hoje = datetime.now().date()
        
        for cobranca in response.data:
            # Calcular status real baseado na data
            status_original = cobranca["status"]
            data_vencimento = datetime.strptime(cobranca["data_vencimento"], "%Y-%m-%d").date()
            
            if status_original == "Pago":
                status_real = "Pago"
                status_cor = "success"
                emoji = "✅"
                estatisticas["total_pago"] += 1
                estatisticas["valor_pago"] += float(cobranca["valor"])
            elif status_original == "Cancelado":
                status_real = "Cancelado"
                status_cor = "secondary"
                emoji = "❌"
            elif data_vencimento < data_hoje:
                status_real = "Vencido"
                status_cor = "error"
                emoji = "⚠️"
                estatisticas["total_vencido"] += 1
                estatisticas["valor_vencido"] += float(cobranca["valor"])
            else:
                status_real = "Pendente"
                status_cor = "warning"
                emoji = "⏳"
                estatisticas["total_pendente"] += 1
                estatisticas["valor_pendente"] += float(cobranca["valor"])
            
            # Formatar cobrança
            cobranca_formatada = {
                "id_cobranca": cobranca["id_cobranca"],
                "titulo": cobranca["titulo"],
                "descricao": cobranca.get("descricao"),
                "valor": float(cobranca["valor"]),
                "data_vencimento": cobranca["data_vencimento"],
                "data_pagamento": cobranca.get("data_pagamento"),
                "status": status_original,
                "status_real": status_real,
                "status_cor": status_cor,
                "emoji": emoji,
                "tipo_cobranca": cobranca["tipo_cobranca"],
                "tipo_display": TIPOS_COBRANCA_DISPLAY.get(cobranca["tipo_cobranca"], "📝 Outros"),
                "grupo_cobranca": cobranca.get("grupo_cobranca"),
                "parcela_numero": cobranca.get("parcela_numero", 1),
                "parcela_total": cobranca.get("parcela_total", 1),
                "observacoes": cobranca.get("observacoes"),
                "prioridade": cobranca.get("prioridade", 1),
                "prioridade_display": PRIORIDADES_COBRANCA.get(cobranca.get("prioridade", 1), "🔸 Normal"),
                "responsavel_nome": cobranca["responsaveis"]["nome"] if cobranca.get("responsaveis") else "N/A",
                "data_vencimento_br": formatar_data_br(cobranca["data_vencimento"]),
                "data_pagamento_br": formatar_data_br(cobranca.get("data_pagamento")) if cobranca.get("data_pagamento") else None,
                "valor_br": formatar_valor_br(cobranca["valor"])
            }
            
            # Adicionar informações de parcela se aplicável
            if cobranca.get("grupo_cobranca") and cobranca.get("parcela_total", 1) > 1:
                cobranca_formatada["titulo_completo"] = f"{cobranca['titulo']} ({cobranca.get('parcela_numero', 1)}/{cobranca.get('parcela_total', 1)})"
            else:
                cobranca_formatada["titulo_completo"] = cobranca["titulo"]
            
            cobrancas_formatadas.append(cobranca_formatada)
        
        return {
            "success": True,
            "cobrancas": cobrancas_formatadas,
            "count": len(cobrancas_formatadas),
            "estatisticas": estatisticas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_cobranca_individual(id_aluno: str, id_responsavel: str, dados_cobranca: Dict) -> Dict:
    """
    Cadastra uma cobrança individual
    
    Args:
        id_aluno: ID do aluno
        id_responsavel: ID do responsável
        dados_cobranca: Dict com dados da cobrança
        
    Returns:
        Dict: {"success": bool, "id_cobranca": str, "data": Dict}
    """
    try:
        # Validar aluno e responsável existem
        aluno_check = supabase.table("alunos").select("id, nome").eq("id", id_aluno).execute()
        if not aluno_check.data:
            return {"success": False, "error": f"Aluno com ID {id_aluno} não encontrado"}
        
        resp_check = supabase.table("responsaveis").select("id, nome").eq("id", id_responsavel).execute()
        if not resp_check.data:
            return {"success": False, "error": f"Responsável com ID {id_responsavel} não encontrado"}
        
        # Gerar ID da cobrança
        id_cobranca = gerar_id_cobranca()
        
        # Preparar dados da cobrança
        dados_cadastro = {
            "id_cobranca": id_cobranca,
            "id_aluno": id_aluno,
            "id_responsavel": id_responsavel,
            "titulo": dados_cobranca.get("titulo"),
            "descricao": dados_cobranca.get("descricao"),
            "valor": float(dados_cobranca.get("valor", 0)),
            "data_vencimento": dados_cobranca.get("data_vencimento"),
            "status": "Pendente",
            "tipo_cobranca": dados_cobranca.get("tipo_cobranca", "outros"),
            "grupo_cobranca": dados_cobranca.get("grupo_cobranca"),
            "parcela_numero": int(dados_cobranca.get("parcela_numero", 1)),
            "parcela_total": int(dados_cobranca.get("parcela_total", 1)),
            "observacoes": dados_cobranca.get("observacoes"),
            "prioridade": int(dados_cobranca.get("prioridade", 2)),
            "inserted_at": obter_timestamp(),
            "updated_at": obter_timestamp()
        }
        
        # Remover campos None/vazios
        dados_cadastro = {k: v for k, v in dados_cadastro.items() if v is not None and v != ""}
        
        # Inserir no banco
        response = supabase.table("cobrancas").insert(dados_cadastro).execute()
        
        if not response.data:
            return {"success": False, "error": "Erro ao cadastrar cobrança"}
        
        return {
            "success": True,
            "id_cobranca": id_cobranca,
            "titulo": dados_cadastro["titulo"],
            "valor": dados_cadastro["valor"],
            "data": response.data[0]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_cobranca_parcelada(id_aluno: str, id_responsavel: str, dados_cobranca: Dict) -> Dict:
    """
    Cadastra uma cobrança parcelada (ex: formatura em 6x)
    
    Args:
        id_aluno: ID do aluno
        id_responsavel: ID do responsável
        dados_cobranca: Dict com dados da cobrança parcelada
        
    Returns:
        Dict: {"success": bool, "cobrancas_criadas": int, "ids_cobrancas": List[str]}
    """
    try:
        # Validar parâmetros obrigatórios
        titulo_base = dados_cobranca.get("titulo")
        valor_parcela = float(dados_cobranca.get("valor_parcela", 0))
        numero_parcelas = int(dados_cobranca.get("numero_parcelas", 1))
        data_primeira_parcela = dados_cobranca.get("data_primeira_parcela")
        tipo_cobranca = dados_cobranca.get("tipo_cobranca", "outros")
        
        if not all([titulo_base, valor_parcela > 0, numero_parcelas > 0, data_primeira_parcela]):
            return {"success": False, "error": "Parâmetros obrigatórios não fornecidos"}
        
        if numero_parcelas > 24:
            return {"success": False, "error": "Número máximo de parcelas é 24"}
        
        # Gerar ID do grupo
        grupo_cobranca = gerar_grupo_cobranca(tipo_cobranca, id_aluno)
        
        # Calcular datas de vencimento
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        data_base = datetime.strptime(data_primeira_parcela, "%Y-%m-%d").date()
        
        cobrancas_criadas = []
        ids_cobrancas = []
        
        for i in range(numero_parcelas):
            # Calcular data de vencimento (soma meses)
            data_vencimento = data_base + relativedelta(months=i)
            
            # Preparar dados da parcela
            dados_parcela = {
                "titulo": f"{titulo_base} - Parcela {i+1}/{numero_parcelas}",
                "descricao": dados_cobranca.get("descricao"),
                "valor": valor_parcela,
                "data_vencimento": data_vencimento.isoformat(),
                "tipo_cobranca": tipo_cobranca,
                "grupo_cobranca": grupo_cobranca,
                "parcela_numero": i + 1,
                "parcela_total": numero_parcelas,
                "observacoes": dados_cobranca.get("observacoes"),
                "prioridade": dados_cobranca.get("prioridade", 2)
            }
            
            # Cadastrar parcela
            resultado_parcela = cadastrar_cobranca_individual(id_aluno, id_responsavel, dados_parcela)
            
            if resultado_parcela.get("success"):
                cobrancas_criadas.append(resultado_parcela)
                ids_cobrancas.append(resultado_parcela["id_cobranca"])
            else:
                # Se uma parcela falhar, reverter todas as criadas
                for id_cobranca in ids_cobrancas:
                    supabase.table("cobrancas").delete().eq("id_cobranca", id_cobranca).execute()
                
                return {
                    "success": False, 
                    "error": f"Erro ao criar parcela {i+1}: {resultado_parcela.get('error')}"
                }
        
        return {
            "success": True,
            "cobrancas_criadas": len(cobrancas_criadas),
            "ids_cobrancas": ids_cobrancas,
            "grupo_cobranca": grupo_cobranca,
            "titulo_base": titulo_base,
            "valor_total": valor_parcela * numero_parcelas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_cobranca(id_cobranca: str, campos: Dict) -> Dict:
    """
    Atualiza campos específicos de uma cobrança
    
    Args:
        id_cobranca: ID da cobrança
        campos: Dict com campos a atualizar
        
    Returns:
        Dict: {"success": bool, "campos_atualizados": List[str], "data": Dict}
    """
    try:
        campos_permitidos = [
            "titulo", "descricao", "valor", "data_vencimento", "status",
            "tipo_cobranca", "observacoes", "prioridade"
        ]
        
        dados_update = {k: v for k, v in campos.items() if k in campos_permitidos}
        
        if not dados_update:
            return {"success": False, "error": "Nenhum campo válido para atualizar"}
        
        dados_update["updated_at"] = obter_timestamp()
        
        response = supabase.table("cobrancas").update(dados_update).eq("id_cobranca", id_cobranca).execute()
        
        if response.data:
            return {
                "success": True,
                "campos_atualizados": list(dados_update.keys()),
                "data": response.data[0]
            }
        else:
            return {"success": False, "error": "Cobrança não encontrada"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def marcar_cobranca_como_paga(id_cobranca: str, data_pagamento: str, id_pagamento: str = None) -> Dict:
    """
    Marca uma cobrança como paga
    
    Args:
        id_cobranca: ID da cobrança
        data_pagamento: Data do pagamento (YYYY-MM-DD)
        id_pagamento: ID do pagamento relacionado (opcional)
        
    Returns:
        Dict: {"success": bool, "data": Dict}
    """
    try:
        dados_update = {
            "status": "Pago",
            "data_pagamento": data_pagamento,
            "updated_at": obter_timestamp()
        }
        
        if id_pagamento:
            dados_update["id_pagamento"] = id_pagamento
        
        response = supabase.table("cobrancas").update(dados_update).eq("id_cobranca", id_cobranca).execute()
        
        if response.data:
            return {
                "success": True,
                "data": response.data[0],
                "message": "Cobrança marcada como paga"
            }
        else:
            return {"success": False, "error": "Cobrança não encontrada"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def cancelar_cobranca(id_cobranca: str, motivo: str = None) -> Dict:
    """
    Cancela uma cobrança
    
    Args:
        id_cobranca: ID da cobrança
        motivo: Motivo do cancelamento (opcional)
        
    Returns:
        Dict: {"success": bool, "data": Dict}
    """
    try:
        dados_update = {
            "status": "Cancelado",
            "updated_at": obter_timestamp()
        }
        
        if motivo:
            observacoes_atuais = supabase.table("cobrancas").select("observacoes").eq("id_cobranca", id_cobranca).execute()
            if observacoes_atuais.data:
                obs_existentes = observacoes_atuais.data[0].get("observacoes", "")
                if obs_existentes:
                    dados_update["observacoes"] = f"{obs_existentes} | Cancelado: {motivo}"
                else:
                    dados_update["observacoes"] = f"Cancelado: {motivo}"
        
        response = supabase.table("cobrancas").update(dados_update).eq("id_cobranca", id_cobranca).execute()
        
        if response.data:
            return {
                "success": True,
                "data": response.data[0],
                "message": "Cobrança cancelada"
            }
        else:
            return {"success": False, "error": "Cobrança não encontrada"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_cobrancas_por_grupo(grupo_cobranca: str) -> Dict:
    """
    Lista todas as cobranças de um grupo (ex: todas as parcelas da formatura)
    
    Args:
        grupo_cobranca: ID do grupo de cobranças
        
    Returns:
        Dict: {"success": bool, "cobrancas": List[Dict], "count": int}
    """
    try:
        response = supabase.table("cobrancas").select("""
            id_cobranca, titulo, valor, data_vencimento, status, 
            parcela_numero, parcela_total,
            alunos!inner(nome),
            responsaveis!inner(nome)
        """).eq("grupo_cobranca", grupo_cobranca).order("parcela_numero").execute()
        
        if not response.data:
            return {
                "success": True,
                "cobrancas": [],
                "count": 0
            }
        
        cobrancas_formatadas = []
        for cobranca in response.data:
            cobranca_formatada = {
                "id_cobranca": cobranca["id_cobranca"],
                "titulo": cobranca["titulo"],
                "valor": float(cobranca["valor"]),
                "data_vencimento": cobranca["data_vencimento"],
                "status": cobranca["status"],
                "parcela_numero": cobranca["parcela_numero"],
                "parcela_total": cobranca["parcela_total"],
                "aluno_nome": cobranca["alunos"]["nome"],
                "responsavel_nome": cobranca["responsaveis"]["nome"],
                "data_vencimento_br": formatar_data_br(cobranca["data_vencimento"]),
                "valor_br": formatar_valor_br(cobranca["valor"])
            }
            cobrancas_formatadas.append(cobranca_formatada)
        
        return {
            "success": True,
            "cobrancas": cobrancas_formatadas,
            "count": len(cobrancas_formatadas)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)} 