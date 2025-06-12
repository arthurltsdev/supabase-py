#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 FUNÇÕES OTIMIZADAS PARA PROCESSAMENTO DO EXTRATO PIX
======================================================

Funções específicas e eficientes para a interface de processamento.
Focadas nos requisitos exatos do usuário.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from supabase import create_client
from dotenv import load_dotenv
import uuid

# Carrega as variáveis do .env
load_dotenv()

# Configurações do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def gerar_id_responsavel() -> str:
    """Gera ID único para responsável"""
    return f"RES_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_pagamento() -> str:
    """Gera ID único para pagamento"""
    return f"PAG_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_vinculo() -> str:
    """Gera ID único para vínculo aluno-responsável"""
    return f"AR_{str(uuid.uuid4().int)[:8].upper()}"

# ==========================================================
# 📊 FUNÇÕES DE CONSULTA E LISTAGEM
# ==========================================================

def listar_extrato_pix_por_status(status: str = "novo", 
                                  data_inicio: Optional[str] = None,
                                  data_fim: Optional[str] = None,
                                  limite: Optional[int] = None) -> Dict:
    """
    Lista registros do extrato PIX filtrados por status e período
    
    Args:
        status: Status dos registros ('novo', 'registrado', etc.)
        data_inicio: Data início (YYYY-MM-DD)
        data_fim: Data fim (YYYY-MM-DD)
        limite: Limite de registros
    """
    try:
        query = supabase.table("extrato_pix").select("*").eq("status", status)
        
        if data_inicio:
            query = query.gte("data_pagamento", data_inicio)
        if data_fim:
            query = query.lte("data_pagamento", data_fim)
        if limite:
            query = query.limit(limite)
            
        query = query.order("data_pagamento", desc=True)
        response = query.execute()
        
        return {
            "success": True,
            "data": response.data,
            "count": len(response.data),
            "filtros": {
                "status": status,
                "data_inicio": data_inicio,
                "data_fim": data_fim
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_extrato_com_sem_responsavel(data_inicio: Optional[str] = None,
                                      data_fim: Optional[str] = None) -> Dict:
    """
    Lista registros separando COM e SEM responsável cadastrado
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
            "total_geral": len(response.data)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_alunos_para_dropdown(termo_busca: str = "") -> Dict:
    """
    Busca alunos para dropdown com filtro incremental
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

def listar_responsaveis_aluno(id_aluno: str) -> Dict:
    """
    Lista todos os responsáveis vinculados a um aluno
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
        Dict com lista de alunos vinculados
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

# ==========================================================
# 📝 FUNÇÕES DE CADASTRO E VINCULAÇÃO
# ==========================================================

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
            "inserted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Remover campos None/vazios
        dados_cadastro = {k: v for k, v in dados_cadastro.items() if v is not None and v != ""}
        
        resp_response = supabase.table("responsaveis").insert(dados_cadastro).execute()
        
        if not resp_response.data:
            return {"success": False, "error": "Erro ao cadastrar responsável"}
        
        # 3. Criar vínculo
        id_vinculo = gerar_id_vinculo()
        
        dados_vinculo = {
            "id": id_vinculo,
            "id_aluno": id_aluno,
            "id_responsavel": id_responsavel,
            "tipo_relacao": tipo_relacao,
            "responsavel_financeiro": responsavel_financeiro,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        vinculo_response = supabase.table("alunos_responsaveis").insert(dados_vinculo).execute()
        
        if not vinculo_response.data:
            # Se falhar vínculo, remover responsável
            supabase.table("responsaveis").delete().eq("id", id_responsavel).execute()
            return {"success": False, "error": "Erro ao criar vínculo"}
        
        return {
            "success": True,
            "id_responsavel": id_responsavel,
            "id_vinculo": id_vinculo,
            "nome_responsavel": dados_responsavel.get("nome"),
            "nome_aluno": aluno_check.data[0]["nome"]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def adicionar_responsavel_existente_ao_aluno(id_responsavel: str,
                                           id_aluno: str,
                                           tipo_relacao: str,
                                           responsavel_financeiro: bool = False) -> Dict:
    """
    Vincula um responsável já existente a um aluno
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
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
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

# ==========================================================
# 💰 FUNÇÕES DE PROCESSAMENTO DE PAGAMENTOS
# ==========================================================

def registrar_pagamentos_multiplos_do_extrato(id_extrato: str,
                                              id_responsavel: str,
                                              pagamentos_detalhados: List[Dict],
                                              descricao: Optional[str] = None) -> Dict:
    """
    Registra múltiplos pagamentos baseado em um registro do extrato PIX
    
    Args:
        id_extrato: ID do registro no extrato_pix
        id_responsavel: ID do responsável pagador
        pagamentos_detalhados: Lista de dicts com:
            {
                "id_aluno": str,
                "tipo_pagamento": str,
                "valor": float,
                "observacoes": str (opcional)
            }
        descricao: Descrição adicional
    
    Returns:
        Dict com resultado do processamento múltiplo
    """
    debug_info = []
    
    def debug_log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        debug_entry = f"[{timestamp}] {msg}"
        debug_info.append(debug_entry)
        print(debug_entry)
    
    try:
        debug_log(f"🚀 INICIANDO registrar_pagamentos_multiplos_do_extrato")
        debug_log(f"   📋 Parâmetros recebidos:")
        debug_log(f"      - id_extrato: {id_extrato}")
        debug_log(f"      - id_responsavel: {id_responsavel}")
        debug_log(f"      - total_pagamentos: {len(pagamentos_detalhados)}")
        debug_log(f"      - descricao: {descricao}")
        
        for i, pag in enumerate(pagamentos_detalhados):
            debug_log(f"      - pagamento_{i+1}: aluno={pag.get('id_aluno')}, tipo={pag.get('tipo_pagamento')}, valor=R${pag.get('valor', 0):.2f}")
        
        # 1. Buscar dados do extrato
        debug_log(f"🔍 ETAPA 1: Buscando dados do extrato {id_extrato}")
        extrato_response = supabase.table("extrato_pix").select("*").eq("id", id_extrato).execute()
        debug_log(f"   📊 Query extrato_pix executada")
        debug_log(f"   📊 Dados retornados: {len(extrato_response.data) if extrato_response.data else 0} registros")
        
        if not extrato_response.data:
            debug_log(f"❌ ERRO: Registro do extrato não encontrado")
            return {
                "success": False, 
                "error": "Registro do extrato não encontrado",
                "debug_info": debug_info
            }
        
        extrato = extrato_response.data[0]
        valor_total_extrato = float(extrato.get('valor', 0))
        
        debug_log(f"✅ Extrato encontrado:")
        debug_log(f"   📊 ID: {extrato.get('id')}")
        debug_log(f"   📊 Status atual: {extrato.get('status')}")
        debug_log(f"   📊 Valor total: R$ {valor_total_extrato:.2f}")
        debug_log(f"   📊 Data: {extrato.get('data_pagamento')}")
        debug_log(f"   📊 Remetente: {extrato.get('nome_remetente')}")
        
        # 2. Verificar se já foi processado
        debug_log(f"🔍 ETAPA 2: Verificando se registro já foi processado")
        if extrato.get("status") == "registrado":
            debug_log(f"❌ ERRO: Este registro já foi processado")
            return {
                "success": False, 
                "error": "Este registro já foi processado",
                "debug_info": debug_info
            }
        
        # 3. Validar valores
        debug_log(f"🔍 ETAPA 3: Validando valores dos pagamentos")
        valor_total_pagamentos = sum(float(pag.get('valor', 0)) for pag in pagamentos_detalhados)
        debug_log(f"   📊 Valor total dos pagamentos: R$ {valor_total_pagamentos:.2f}")
        debug_log(f"   📊 Valor total do extrato: R$ {valor_total_extrato:.2f}")
        debug_log(f"   📊 Diferença: R$ {abs(valor_total_extrato - valor_total_pagamentos):.2f}")
        
        if abs(valor_total_extrato - valor_total_pagamentos) > 0.01:  # Tolerância de 1 centavo
            debug_log(f"❌ ERRO: Valores não conferem")
            return {
                "success": False,
                "error": f"Soma dos pagamentos (R$ {valor_total_pagamentos:.2f}) não confere com valor do extrato (R$ {valor_total_extrato:.2f})",
                "debug_info": debug_info
            }
        
        debug_log(f"✅ Valores validados com sucesso")
        
        # 4. Validar alunos
        debug_log(f"🔍 ETAPA 4: Validando alunos")
        alunos_ids = [pag.get('id_aluno') for pag in pagamentos_detalhados]
        alunos_response = supabase.table("alunos").select("id, nome").in_("id", alunos_ids).execute()
        
        if len(alunos_response.data) != len(set(alunos_ids)):
            debug_log(f"❌ ERRO: Alguns alunos não foram encontrados")
            return {
                "success": False,
                "error": "Um ou mais alunos não foram encontrados",
                "debug_info": debug_info
            }
        
        debug_log(f"✅ Todos os alunos validados")
        
        # 5. Registrar cada pagamento
        debug_log(f"💰 ETAPA 5: Registrando {len(pagamentos_detalhados)} pagamentos")
        pagamentos_criados = []
        matriculas_atualizadas = []
        
        for i, pag_detalhe in enumerate(pagamentos_detalhados):
            debug_log(f"   💳 Processando pagamento {i+1}/{len(pagamentos_detalhados)}")
            
            id_pagamento = gerar_id_pagamento()
            debug_log(f"      🆔 ID gerado: {id_pagamento}")
            
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
                "id_extrato_origem": id_extrato,
                "inserted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            debug_log(f"      📊 Dados do pagamento:")
            for key, value in dados_pagamento.items():
                debug_log(f"         - {key}: {value}")
            
            # Inserir pagamento
            debug_log(f"      💾 Executando INSERT na tabela pagamentos")
            pag_response = supabase.table("pagamentos").insert(dados_pagamento).execute()
            debug_log(f"      📊 Response INSERT: {len(pag_response.data) if pag_response.data else 0} registros")
            
            if not pag_response.data:
                debug_log(f"      ❌ ERRO: Falha ao inserir pagamento {i+1}")
                return {
                    "success": False,
                    "error": f"Erro ao registrar pagamento {i+1}",
                    "debug_info": debug_info,
                    "pagamentos_criados": pagamentos_criados  # Retornar os que já foram criados
                }
            
            pagamentos_criados.append(pag_response.data[0])
            debug_log(f"      ✅ Pagamento {i+1} inserido com sucesso")
            
            # Se for matrícula, atualizar data_matricula do aluno
            if pag_detalhe.get('tipo_pagamento', '').lower() == 'matricula':
                debug_log(f"      🎓 Atualizando data_matricula do aluno {pag_detalhe.get('id_aluno')}")
                
                aluno_update = supabase.table("alunos").update({
                    "data_matricula": extrato["data_pagamento"],
                    "updated_at": datetime.now().isoformat()
                }).eq("id", pag_detalhe.get('id_aluno')).execute()
                
                if aluno_update.data:
                    matriculas_atualizadas.append(pag_detalhe.get('id_aluno'))
                    debug_log(f"      ✅ Data de matrícula atualizada")
                else:
                    debug_log(f"      ⚠️ Falha ao atualizar data de matrícula")
        
        # 6. Atualizar status do extrato
        debug_log(f"📝 ETAPA 6: Atualizando status do extrato para 'registrado'")
        
        # Criar resumo dos tipos de pagamento
        tipos_resumo = ", ".join(set(pag.get('tipo_pagamento', '') for pag in pagamentos_detalhados))
        alunos_resumo = ", ".join(set(pag.get('id_aluno', '') for pag in pagamentos_detalhados))
        
        dados_update_extrato = {
            "status": "registrado",
            "id_responsavel": id_responsavel,
            "tipo_pagamento": tipos_resumo,  # Resumo dos tipos
            "processamento_multiplo": True,
            "total_pagamentos_gerados": len(pagamentos_detalhados),
            "alunos_beneficiarios": alunos_resumo,
            "atualizado_em": datetime.now().isoformat()
        }
        
        debug_log(f"   📊 Dados para UPDATE extrato:")
        for key, value in dados_update_extrato.items():
            debug_log(f"      - {key}: {value}")
        
        extrato_update = supabase.table("extrato_pix").update(dados_update_extrato).eq("id", id_extrato).execute()
        debug_log(f"   📊 Response UPDATE extrato: {len(extrato_update.data) if extrato_update.data else 0} registros")
        
        resultado_final = {
            "success": True,
            "total_pagamentos_criados": len(pagamentos_criados),
            "pagamentos_criados": pagamentos_criados,
            "matriculas_atualizadas": matriculas_atualizadas,
            "extrato_atualizado": bool(extrato_update.data),
            "valor_total_processado": valor_total_pagamentos,
            "tipos_pagamento": [pag.get('tipo_pagamento') for pag in pagamentos_detalhados],
            "alunos_beneficiarios": [pag.get('id_aluno') for pag in pagamentos_detalhados],
            "message": f"{len(pagamentos_criados)} pagamentos registrados: {tipos_resumo}",
            "debug_info": debug_info
        }
        
        debug_log(f"🏁 SUCESSO: Processamento múltiplo finalizado")
        debug_log(f"   📊 Resultado: {len(pagamentos_criados)} pagamentos criados")
        debug_log(f"   📊 Tipos: {tipos_resumo}")
        debug_log(f"   📊 Valor total: R$ {valor_total_pagamentos:.2f}")
        
        return resultado_final
        
    except Exception as e:
        debug_log(f"❌ EXCEÇÃO CAPTURADA: {str(e)}")
        
        import traceback
        tb = traceback.format_exc()
        debug_log(f"   📊 Traceback completo:")
        for line in tb.split('\n'):
            if line.strip():
                debug_log(f"      {line}")
        
        return {
            "success": False,
            "error": str(e),
            "debug_info": debug_info,
            "exception_type": type(e).__name__,
            "traceback": tb
        }

def registrar_pagamento_do_extrato(id_extrato: str,
                                  id_responsavel: str,
                                  id_aluno: str,
                                  tipo_pagamento: str,
                                  descricao: Optional[str] = None) -> Dict:
    """
    Registra pagamento baseado em registro do extrato PIX com debugging detalhado
    
    Args:
        id_extrato: ID do registro no extrato_pix
        id_responsavel: ID do responsável pagador
        id_aluno: ID do aluno beneficiário
        tipo_pagamento: Tipo (matricula, fardamento, outro, etc.)
        descricao: Descrição adicional
    """
    debug_info = []
    
    def debug_log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        debug_entry = f"[{timestamp}] {msg}"
        debug_info.append(debug_entry)
        print(debug_entry)  # Log no terminal
    
    try:
        debug_log(f"🚀 INICIANDO registrar_pagamento_do_extrato")
        debug_log(f"   📋 Parâmetros recebidos:")
        debug_log(f"      - id_extrato: {id_extrato}")
        debug_log(f"      - id_responsavel: {id_responsavel}")
        debug_log(f"      - id_aluno: {id_aluno}")
        debug_log(f"      - tipo_pagamento: {tipo_pagamento}")
        debug_log(f"      - descricao: {descricao}")
        
        # 1. Buscar dados do extrato
        debug_log(f"🔍 ETAPA 1: Buscando dados do extrato {id_extrato}")
        extrato_response = supabase.table("extrato_pix").select("*").eq("id", id_extrato).execute()
        debug_log(f"   📊 Query extrato_pix executada")
        debug_log(f"   📊 Dados retornados: {len(extrato_response.data) if extrato_response.data else 0} registros")
        
        if not extrato_response.data:
            debug_log(f"❌ ERRO: Registro do extrato não encontrado")
            return {
                "success": False, 
                "error": "Registro do extrato não encontrado",
                "debug_info": debug_info
            }
        
        extrato = extrato_response.data[0]
        debug_log(f"✅ Extrato encontrado:")
        debug_log(f"   📊 ID: {extrato.get('id')}")
        debug_log(f"   📊 Status atual: {extrato.get('status')}")
        debug_log(f"   📊 Valor: R$ {extrato.get('valor')}")
        debug_log(f"   📊 Data: {extrato.get('data_pagamento')}")
        debug_log(f"   📊 Remetente: {extrato.get('nome_remetente')}")
        
        # 2. Verificar se já foi processado
        debug_log(f"🔍 ETAPA 2: Verificando se registro já foi processado")
        if extrato.get("status") == "registrado":
            debug_log(f"❌ ERRO: Este registro já foi processado")
            return {
                "success": False, 
                "error": "Este registro já foi processado",
                "debug_info": debug_info
            }
        
        debug_log(f"✅ Registro pode ser processado (status: {extrato.get('status')})")
        
        # 3. Registrar pagamento
        debug_log(f"💰 ETAPA 3: Registrando pagamento na tabela pagamentos")
        id_pagamento = gerar_id_pagamento()
        debug_log(f"   🆔 ID gerado para pagamento: {id_pagamento}")
        
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
            "inserted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        debug_log(f"   📊 Dados do pagamento preparados:")
        for key, value in dados_pagamento.items():
            debug_log(f"      - {key}: {value}")
        
        debug_log(f"   💾 Executando INSERT na tabela pagamentos")
        pag_response = supabase.table("pagamentos").insert(dados_pagamento).execute()
        debug_log(f"   📊 Response INSERT: {len(pag_response.data) if pag_response.data else 0} registros inseridos")
        
        if not pag_response.data:
            debug_log(f"❌ ERRO: Falha ao inserir pagamento")
            debug_log(f"   📊 Response completo: {pag_response}")
            return {
                "success": False, 
                "error": "Erro ao registrar pagamento",
                "debug_info": debug_info,
                "response_details": str(pag_response)
            }
        
        debug_log(f"✅ Pagamento inserido com sucesso: {pag_response.data[0]}")
        
        # 4. Se for matrícula, atualizar data_matricula do aluno
        matricula_atualizada = False
        if tipo_pagamento.lower() == "matricula":
            debug_log(f"🎓 ETAPA 4: Atualizando data_matricula do aluno (tipo: matricula)")
            debug_log(f"   📊 Atualizando aluno ID: {id_aluno}")
            debug_log(f"   📊 Nova data_matricula: {extrato['data_pagamento']}")
            
            aluno_update = supabase.table("alunos").update({
                "data_matricula": extrato["data_pagamento"],
                "updated_at": datetime.now().isoformat()
            }).eq("id", id_aluno).execute()
            
            debug_log(f"   📊 Response UPDATE aluno: {len(aluno_update.data) if aluno_update.data else 0} registros atualizados")
            matricula_atualizada = bool(aluno_update.data)
            
            if matricula_atualizada:
                debug_log(f"✅ Data de matrícula atualizada com sucesso")
            else:
                debug_log(f"⚠️ AVISO: Falha ao atualizar data de matrícula")
        else:
            debug_log(f"ℹ️ Tipo não é matrícula ({tipo_pagamento}), pulando atualização do aluno")
        
        # 5. Atualizar status do extrato para "registrado"
        debug_log(f"📝 ETAPA 5: Atualizando status do extrato para 'registrado'")
        
        dados_update_extrato = {
            "status": "registrado",
            "id_responsavel": id_responsavel,
            "id_aluno": id_aluno,
            "tipo_pagamento": tipo_pagamento,
            "atualizado_em": datetime.now().isoformat()
        }
        
        debug_log(f"   📊 Dados para UPDATE extrato:")
        for key, value in dados_update_extrato.items():
            debug_log(f"      - {key}: {value}")
        
        extrato_update = supabase.table("extrato_pix").update(dados_update_extrato).eq("id", id_extrato).execute()
        debug_log(f"   📊 Response UPDATE extrato: {len(extrato_update.data) if extrato_update.data else 0} registros atualizados")
        
        resultado_final = {
            "success": True,
            "id_pagamento": id_pagamento,
            "extrato_atualizado": bool(extrato_update.data),
            "matricula_atualizada": matricula_atualizada,
            "message": f"Pagamento registrado como {tipo_pagamento}",
            "debug_info": debug_info,
            "dados_processados": {
                "extrato": extrato,
                "pagamento": dados_pagamento,
                "updates": {
                    "extrato": bool(extrato_update.data),
                    "aluno": matricula_atualizada
                }
            }
        }
        
        debug_log(f"🏁 SUCESSO: Processamento finalizado com êxito")
        debug_log(f"   📊 Resultado: {resultado_final['message']}")
        debug_log(f"   🆔 ID Pagamento: {id_pagamento}")
        
        return resultado_final
        
    except Exception as e:
        debug_log(f"❌ EXCEÇÃO CAPTURADA: {str(e)}")
        debug_log(f"   📊 Tipo da exceção: {type(e).__name__}")
        
        import traceback
        tb = traceback.format_exc()
        debug_log(f"   📊 Traceback completo:")
        for line in tb.split('\n'):
            if line.strip():
                debug_log(f"      {line}")
        
        return {
            "success": False, 
            "error": str(e),
            "debug_info": debug_info,
            "exception_type": type(e).__name__,
            "traceback": tb
        }

def processar_registros_extrato_em_massa(registros_acoes: List[Dict]) -> Dict:
    """
    Processa múltiplos registros do extrato em massa
    
    Args:
        registros_acoes: Lista de dicts com {id_extrato, id_responsavel, id_aluno, tipo_pagamento, acao}
    """
    try:
        resultados = {
            "total": len(registros_acoes),
            "sucessos": 0,
            "erros": 0,
            "detalhes": []
        }
        
        for item in registros_acoes:
            try:
                if item["acao"] == "registrar_pagamento":
                    resultado = registrar_pagamento_do_extrato(
                        id_extrato=item["id_extrato"],
                        id_responsavel=item["id_responsavel"],
                        id_aluno=item["id_aluno"],
                        tipo_pagamento=item["tipo_pagamento"],
                        descricao=item.get("descricao")
                    )
                elif item["acao"] == "remover":
                    resultado = remover_registro_extrato(item["id_extrato"])
                else:
                    resultado = {"success": False, "error": "Ação não reconhecida"}
                
                if resultado["success"]:
                    resultados["sucessos"] += 1
                    resultados["detalhes"].append({
                        "id_extrato": item["id_extrato"],
                        "status": "sucesso",
                        "acao": item["acao"],
                        "resultado": resultado
                    })
                else:
                    resultados["erros"] += 1
                    resultados["detalhes"].append({
                        "id_extrato": item["id_extrato"],
                        "status": "erro",
                        "acao": item["acao"],
                        "erro": resultado["error"]
                    })
                    
            except Exception as e:
                resultados["erros"] += 1
                resultados["detalhes"].append({
                    "id_extrato": item.get("id_extrato", "unknown"),
                    "status": "erro",
                    "acao": item.get("acao", "unknown"),
                    "erro": str(e)
                })
        
        return {
            "success": True,
            "resultados": resultados
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# ✏️ FUNÇÕES DE ATUALIZAÇÃO
# ==========================================================

def atualizar_aluno_campos(id_aluno: str, campos: Dict) -> Dict:
    """
    Atualiza campos específicos de um aluno
    
    Args:
        id_aluno: ID do aluno
        campos: Dict com campos a atualizar
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
        
        dados_update["updated_at"] = datetime.now().isoformat()
        
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

def atualizar_vinculo_responsavel(id_vinculo: str, 
                                tipo_relacao: Optional[str] = None,
                                responsavel_financeiro: Optional[bool] = None) -> Dict:
    """
    Atualiza vínculo entre aluno e responsável
    """
    try:
        dados_update = {"updated_at": datetime.now().isoformat()}
        
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
    """
    try:
        response = supabase.table("alunos_responsaveis").delete().eq("id", id_vinculo).execute()
        
        if response.data:
            return {"success": True, "message": "Vínculo removido com sucesso"}
        else:
            return {"success": False, "error": "Vínculo não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🗑️ FUNÇÕES DE REMOÇÃO
# ==========================================================

def remover_registro_extrato(id_extrato: str) -> Dict:
    """
    Remove um registro do extrato PIX
    """
    try:
        response = supabase.table("extrato_pix").delete().eq("id", id_extrato).execute()
        
        if response.data:
            return {"success": True, "message": "Registro removido do extrato"}
        else:
            return {"success": False, "error": "Registro não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 📊 FUNÇÕES DE ESTATÍSTICAS
# ==========================================================

def obter_estatisticas_extrato(data_inicio: Optional[str] = None,
                              data_fim: Optional[str] = None) -> Dict:
    """
    Obtém estatísticas do extrato PIX
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
            "valor_total": 0,
            "valor_novos": 0,
            "valor_registrados": 0
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

# ==========================================================
# 🔍 FUNÇÕES AUXILIARES
# ==========================================================

def verificar_responsavel_existe(nome: str) -> Dict:
    """
    Verifica se responsável já existe pelo nome
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

if __name__ == "__main__":
    print("🧪 Testando funções otimizadas...")
    
    # Teste básico
    stats = obter_estatisticas_extrato()
    if stats["success"]:
        print(f"✅ Estatísticas: {stats['estatisticas']['total_registros']} registros")
    else:
        print(f"❌ Erro: {stats['error']}")
    
    print("✅ Funções otimizadas prontas para uso!") 