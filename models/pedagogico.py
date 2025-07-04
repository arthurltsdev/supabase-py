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
    TIPOS_RELACAO, TURNOS_VALIDOS
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
            # Calcular status real baseado na data
            from datetime import datetime
            data_hoje = datetime.now().date()
            data_vencimento = datetime.strptime(mensalidade["data_vencimento"], "%Y-%m-%d").date()
            
            if mensalidade["status"] in ["Pago", "Pago parcial"]:
                status_real = mensalidade["status"]
                status_cor = "success" if status_real == "Pago" else "warning"
            elif data_vencimento < data_hoje:
                status_real = "Vencida"
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
        mensalidades_pendentes = len([m for m in mensalidades if m["status_real"] in ["A vencer", "Vencida"]])
        mensalidades_vencidas = len([m for m in mensalidades if m["status_real"] == "Vencida"])
        
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
            "mensalidades_geradas": aluno.get("mensalidades_geradas", False)
        }
        
        # Estatísticas financeiras
        estatisticas = {
            "total_responsaveis": len(responsaveis),
            "total_pagamentos": len(pagamentos),
            "total_pago": total_pago,
            "total_mensalidades": len(mensalidades),
            "mensalidades_pagas": mensalidades_pagas,
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
            "data_matricula", "valor_mensalidade", "mensalidades_geradas"
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