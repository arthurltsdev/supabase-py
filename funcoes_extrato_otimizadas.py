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
import random
import difflib

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

def gerar_id_aluno() -> str:
    """Gera ID único para aluno"""
    return f"ALU_{random.randint(100000, 999999):06d}"

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
                                      data_fim: Optional[str] = None,
                                      filtro_turma: Optional[str] = None) -> Dict:
    """
    Lista registros separando COM e SEM responsável cadastrado
    Com filtro opcional por turma e verificação automática de duplicados
    """
    try:
        # PRIMEIRO: Executar verificação e correção de duplicados
        correcao_resultado = verificar_e_corrigir_extrato_duplicado()
        
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
            "filtro_turma": filtro_turma,
            "correcoes_aplicadas": correcao_resultado.get("corrigidos", 0),
            "detalhes_correcoes": correcao_resultado.get("detalhes", []) if correcao_resultado.get("success") else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_dados_completos_alunos_responsavel(id_responsavel: str) -> Dict:
    """
    Busca dados completos dos alunos vinculados ao responsável
    Incluindo informações financeiras e da turma
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
            aluno_data["valor_mensalidade_fmt"] = f"R$ {aluno_data.get('valor_mensalidade', 0):.2f}"
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

def listar_turmas_disponiveis() -> Dict:
    """
    Lista todas as turmas disponíveis para filtros
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

def cadastrar_aluno_e_vincular(dados_aluno: Dict, 
                               id_responsavel: Optional[str] = None,
                               tipo_relacao: str = "responsavel",
                               responsavel_financeiro: bool = True) -> Dict:
    """
    Cadastra novo aluno e opcionalmente vincula a um responsável existente
    
    Args:
        dados_aluno: Dict com nome, id_turma, turno, data_nascimento, dia_vencimento, valor_mensalidade
        id_responsavel: ID do responsável para vincular (opcional)
        tipo_relacao: Tipo de relação com o responsável
        responsavel_financeiro: Se o responsável é financeiro
    """
    try:
        # 1. Validar turma existe
        if dados_aluno.get('id_turma'):
            turma_check = supabase.table("turmas").select("id, nome_turma").eq("id", dados_aluno.get('id_turma')).execute()
            if not turma_check.data:
                return {"success": False, "error": f"Turma com ID {dados_aluno.get('id_turma')} não encontrada"}
        
        # 2. Validar responsável se fornecido
        if id_responsavel:
            resp_check = supabase.table("responsaveis").select("id, nome").eq("id", id_responsavel).execute()
            if not resp_check.data:
                return {"success": False, "error": f"Responsável com ID {id_responsavel} não encontrado"}
        
        # 3. Cadastrar aluno
        id_aluno = gerar_id_aluno()
        
        dados_cadastro = {
            "id": id_aluno,
            "nome": dados_aluno.get("nome"),
            "id_turma": dados_aluno.get("id_turma"),
            "turno": dados_aluno.get("turno"),
            "data_nascimento": dados_aluno.get("data_nascimento"),
            "dia_vencimento": dados_aluno.get("dia_vencimento"),
            "valor_mensalidade": dados_aluno.get("valor_mensalidade"),
            "mensalidades_geradas": False,  # Default para novo aluno
            "inserted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Remover campos None/vazios
        dados_cadastro = {k: v for k, v in dados_cadastro.items() if v is not None and v != ""}
        
        aluno_response = supabase.table("alunos").insert(dados_cadastro).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": "Erro ao cadastrar aluno"}
        
        resultado = {
            "success": True,
            "id_aluno": id_aluno,
            "nome_aluno": dados_aluno.get("nome"),
            "aluno_data": aluno_response.data[0]
        }
        
        # 4. Criar vínculo com responsável se fornecido
        if id_responsavel:
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
            
            if vinculo_response.data:
                resultado.update({
                    "vinculo_criado": True,
                    "id_vinculo": id_vinculo,
                    "nome_responsavel": resp_check.data[0]["nome"] if resp_check.data else "N/A"
                })
            else:
                resultado.update({
                    "vinculo_criado": False,
                    "vinculo_erro": "Erro ao criar vínculo com responsável"
                })
        
        return resultado
        
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
                "id_extrato": id_extrato,
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
            
            # Atualizar pagamento com id_extrato
            debug_log(f"      📝 Atualizando pagamento com id_extrato")
            supabase.table("pagamentos").update({
                "id_extrato": id_extrato,
                "updated_at": datetime.now().isoformat()
            }).eq("id_pagamento", id_pagamento).execute()
            debug_log(f"      📊 Pagamento {id_pagamento} atualizado com id_extrato: {id_extrato}")
            
            # Se é mensalidade, atualizar status da mensalidade
            if pag_detalhe.get('tipo_pagamento') == 'mensalidade' and pag_detalhe.get('id_mensalidade'):
                debug_log(f"      📅 Atualizando status da mensalidade {pag_detalhe.get('id_mensalidade')}")
                
                # Determinar novo status baseado no valor pago
                valor_mensalidade = float(pag_detalhe.get('valor'))
                # Buscar valor original da mensalidade
                mens_response = supabase.table("mensalidades").select("valor").eq("id_mensalidade", pag_detalhe.get('id_mensalidade')).execute()
                
                if mens_response.data:
                    valor_original = float(mens_response.data[0]["valor"])
                    novo_status = "Pago" if valor_mensalidade >= valor_original else "Pago parcial"
                    
                    mens_update = supabase.table("mensalidades").update({
                        "status": novo_status,
                        "id_pagamento": id_pagamento,
                        "data_pagamento": extrato["data_pagamento"],
                        "updated_at": datetime.now().isoformat()
                    }).eq("id_mensalidade", pag_detalhe.get('id_mensalidade')).execute()
                    
                    if mens_update.data:
                        debug_log(f"      ✅ Status da mensalidade atualizado para '{novo_status}'")
                    else:
                        debug_log(f"      ⚠️ Falha ao atualizar status da mensalidade")
                else:
                    debug_log(f"      ⚠️ Mensalidade não encontrada para atualização de status")
            
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
            "atualizado_em": datetime.now().isoformat()
        }
        
        # Se todos os pagamentos são para o mesmo aluno, preencher id_aluno no extrato
        alunos_unicos = set(pag.get('id_aluno', '') for pag in pagamentos_detalhados)
        if len(alunos_unicos) == 1 and list(alunos_unicos)[0]:
            dados_update_extrato["id_aluno"] = list(alunos_unicos)[0]
            debug_log(f"   📊 Todos os pagamentos para o mesmo aluno: {list(alunos_unicos)[0]}")
        
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
                                  descricao: Optional[str] = None,
                                  id_mensalidade: Optional[str] = None) -> Dict:
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
            "id_extrato": id_extrato,
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
        mensalidade_atualizada = False
        
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
        elif tipo_pagamento.lower() == "mensalidade" and id_mensalidade:
            debug_log(f"📅 ETAPA 4: Atualizando status da mensalidade {id_mensalidade}")
            
            # Buscar valor original da mensalidade
            mens_response = supabase.table("mensalidades").select("valor").eq("id_mensalidade", id_mensalidade).execute()
            
            if mens_response.data:
                valor_original = float(mens_response.data[0]["valor"])
                valor_pago = float(extrato["valor"])
                novo_status = "Pago" if valor_pago >= valor_original else "Pago parcial"
                
                debug_log(f"   📊 Valor original da mensalidade: R$ {valor_original:.2f}")
                debug_log(f"   📊 Valor pago: R$ {valor_pago:.2f}")
                debug_log(f"   📊 Novo status: {novo_status}")
                
                mens_update = supabase.table("mensalidades").update({
                    "status": novo_status,
                    "id_pagamento": id_pagamento,
                    "data_pagamento": extrato["data_pagamento"],
                    "updated_at": datetime.now().isoformat()
                }).eq("id_mensalidade", id_mensalidade).execute()
                
                debug_log(f"   📊 Response UPDATE mensalidade: {len(mens_update.data) if mens_update.data else 0} registros atualizados")
                mensalidade_atualizada = bool(mens_update.data)
                
                if mensalidade_atualizada:
                    debug_log(f"✅ Status da mensalidade atualizado para '{novo_status}'")
                else:
                    debug_log(f"⚠️ AVISO: Falha ao atualizar status da mensalidade")
            else:
                debug_log(f"⚠️ AVISO: Mensalidade {id_mensalidade} não encontrada")
        else:
            debug_log(f"ℹ️ Tipo não requer atualizações especiais ({tipo_pagamento})")
        
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
        
        # 6. Atualizar tabela pagamentos com id_extrato
        debug_log(f"📝 ETAPA 6: Atualizando pagamento com id_extrato")
        
        supabase.table("pagamentos").update({
            "id_extrato": id_extrato,
            "updated_at": datetime.now().isoformat()
        }).eq("id_pagamento", id_pagamento).execute()
        
        debug_log(f"   📊 Pagamento {id_pagamento} atualizado com id_extrato: {id_extrato}")
        
        resultado_final = {
            "success": True,
            "id_pagamento": id_pagamento,
            "extrato_atualizado": bool(extrato_update.data),
            "matricula_atualizada": matricula_atualizada,
            "mensalidade_atualizada": mensalidade_atualizada,
            "message": f"Pagamento registrado como {tipo_pagamento}",
            "debug_info": debug_info,
            "dados_processados": {
                "extrato": extrato,
                "pagamento": dados_pagamento,
                "updates": {
                    "extrato": bool(extrato_update.data),
                    "aluno": matricula_atualizada,
                    "mensalidade": mensalidade_atualizada
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

def ignorar_registro_extrato(id_extrato: str) -> Dict:
    """
    Marca um registro do extrato PIX como ignorado
    """
    try:
        response = supabase.table("extrato_pix").update({
            "status": "ignorado",
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", id_extrato).execute()
        
        if response.data:
            return {"success": True, "message": "Registro marcado como ignorado"}
        else:
            return {"success": False, "error": "Registro não encontrado"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

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

def listar_mensalidades_disponiveis_aluno(id_aluno: str) -> Dict:
    """
    Lista mensalidades disponíveis para pagamento de um aluno
    
    Args:
        id_aluno: ID do aluno
        
    Returns:
        Dict com mensalidades disponíveis
    """
    try:
        # Buscar mensalidades pendentes (status diferente de "Pago" e "Cancelado")
        response = supabase.table("mensalidades").select("""
            id_mensalidade, mes_referencia, valor, data_vencimento, status
        """).eq("id_aluno", id_aluno).not_.in_("status", ["Pago", "Cancelado"]).execute()
        
        if not response.data:
            return {"success": True, "mensalidades": []}
        
        mensalidades = []
        for mens in response.data:
            # Determinar status visual
            from datetime import datetime, date
            data_vencimento = datetime.strptime(mens['data_vencimento'], '%Y-%m-%d').date()
            hoje = date.today()
            
            if data_vencimento < hoje:
                status_texto = "⚠️ Atrasado"
            else:
                status_texto = "📅 A vencer"
            
            mensalidades.append({
                "id_mensalidade": mens["id_mensalidade"],
                "mes_referencia": mens["mes_referencia"],
                "valor": mens["valor"],
                "data_vencimento": mens["data_vencimento"],
                "status": mens["status"],
                "status_texto": status_texto,
                "label": f"{mens['mes_referencia']} - R$ {float(mens['valor']):,.2f} - {status_texto}"
            })
        
        return {"success": True, "mensalidades": mensalidades}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

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

# ==========================================================
# 🔍 FUNÇÕES DE VERIFICAÇÃO E CORREÇÃO
# ==========================================================

def verificar_e_corrigir_extrato_duplicado() -> Dict:
    """
    Verifica registros do extrato_pix que já foram processados mas ainda 
    aparecem como 'novo' e corrige o status para 'registrado'
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
                                "atualizado_em": datetime.now().isoformat(),
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

def verificar_consistencia_extrato_pagamentos(data_inicio: Optional[str] = None,
                                            data_fim: Optional[str] = None) -> Dict:
    """
    Verifica a consistência entre registros do extrato e pagamentos
    Retorna relatório detalhado de possíveis inconsistências
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

def buscar_responsaveis_para_dropdown(termo_busca: str = "") -> Dict:
    """
    Busca responsáveis para exibir em dropdown com filtro
    Similar à função buscar_alunos_para_dropdown mas para responsáveis
    
    Args:
        termo_busca: Termo para filtrar responsáveis por nome
        
    Returns:
        Dict com responsáveis encontrados formatados para dropdown
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

def corrigir_status_extrato_com_pagamentos() -> Dict:
    """
    Corrige o status de registros do extrato_pix que já possuem pagamentos vinculados
    mas ainda estão com status "novo". Atualiza para "registrado".
    
    Returns:
        Dict com resultado da operação
    """
    try:
        debug_info = []
        
        # 1. Buscar registros do extrato com status "novo"
        response_extrato = supabase.table("extrato_pix").select(
            "id, nome_remetente, data_pagamento, valor, status"
        ).eq("status", "novo").execute()
        
        if not response_extrato.data:
            return {
                "success": True,
                "message": "Nenhum registro com status 'novo' encontrado",
                "corrigidos": 0,
                "debug_info": debug_info
            }
        
        debug_info.append(f"Encontrados {len(response_extrato.data)} registros com status 'novo'")
        
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
                debug_info.append(f"Corrigindo: {registro_extrato['nome_remetente']} - {len(response_pagamentos.data)} pagamentos encontrados")
                
                # Pegar dados do primeiro pagamento para atualizar o extrato
                primeiro_pagamento = response_pagamentos.data[0]
                
                dados_update = {
                    "status": "registrado",
                    "id_responsavel": primeiro_pagamento.get("id_responsavel"),
                    "atualizado_em": datetime.now().isoformat()
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
            "detalhes_correcoes": detalhes_correcoes,
            "debug_info": debug_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao corrigir status do extrato: {str(e)}",
            "debug_info": debug_info
        }

def atualizar_responsaveis_extrato_pix() -> Dict:
    """
    Identifica registros do extrato_pix sem id_responsavel e tenta fazer correspondência
    com a tabela responsaveis usando similaridade de nomes (>90%).
    Para responsáveis com apenas 1 aluno, também preenche id_aluno.
    
    MODIFICADO: Agora tenta usar nome_norm se disponível para melhor correspondência.
    
    Returns:
        Dict com resultado da operação
    """
    
    try:
        debug_info = []
        
        # 1. Buscar registros do extrato_pix sem id_responsavel
        response_extrato = supabase.table("extrato_pix").select(
            "id, nome_remetente, data_pagamento, valor"
        ).is_("id_responsavel", "null").execute()
        
        if not response_extrato.data:
            return {
                "success": True,
                "message": "Nenhum registro sem id_responsavel encontrado",
                "atualizados": 0,
                "debug_info": debug_info
            }
        
        debug_info.append(f"Encontrados {len(response_extrato.data)} registros sem id_responsavel")
        
        # 2. Buscar todos os responsáveis (verificar se existe nome_norm)
        # Primeiro tentar com nome_norm
        try:
            response_responsaveis = supabase.table("responsaveis").select("id, nome, nome_norm").execute()
            usar_nome_norm = True
            debug_info.append(f"Carregados {len(response_responsaveis.data)} responsáveis (usando nome_norm)")
        except:
            # Se nome_norm não existe, usar nome normal
            response_responsaveis = supabase.table("responsaveis").select("id, nome").execute()
            usar_nome_norm = False
            debug_info.append(f"Carregados {len(response_responsaveis.data)} responsáveis (usando nome)")
        
        if not response_responsaveis.data:
            return {
                "success": False,
                "error": "Nenhum responsável encontrado na tabela responsaveis",
                "debug_info": debug_info
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
                    debug_info.append(f"Comparando '{nome_remetente}' com nome_norm '{nome_comparacao}'")
                else:
                    nome_comparacao = responsavel["nome"]
                    debug_info.append(f"Comparando '{nome_remetente}' com nome '{nome_comparacao}'")
                
                # Usar a função de similaridade
                similaridade = calcular_similaridade_nomes(nome_remetente, nome_comparacao)
                
                if similaridade > melhor_similaridade and similaridade >= 90:
                    melhor_similaridade = similaridade
                    melhor_responsavel = responsavel
            
            if melhor_responsavel:
                nome_usado = melhor_responsavel.get("nome_norm") if usar_nome_norm and melhor_responsavel.get("nome_norm") else melhor_responsavel["nome"]
                debug_info.append(f"Correspondência: {nome_remetente} → {nome_usado} ({melhor_similaridade:.1f}%)")
                
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
                    debug_info.append(f"  → Preenchido id_aluno: {response_alunos.data[0]['alunos']['nome']}")
                elif len(response_alunos.data) > 1:
                    debug_info.append(f"  → {len(response_alunos.data)} alunos vinculados - id_aluno será preenchido no registro do pagamento")
                
                # Atualizar o registro
                supabase.table("extrato_pix").update(dados_update).eq("id", registro_extrato["id"]).execute()
                
                atualizados += 1
                correspondencias.append({
                    "id_extrato": registro_extrato["id"],
                    "nome_remetente": nome_remetente,
                    "nome_responsavel": melhor_responsavel["nome"],  # Sempre mostrar o nome original
                    "nome_usado_comparacao": nome_usado,  # Mostrar qual nome foi usado na comparação
                    "similaridade": melhor_similaridade,
                    "id_responsavel": melhor_responsavel["id"],
                    "alunos_vinculados": len(response_alunos.data),
                    "id_aluno_preenchido": dados_update.get("id_aluno") is not None,
                    "usado_nome_norm": usar_nome_norm and melhor_responsavel.get("nome_norm") is not None
                })
            else:
                debug_info.append(f"Sem correspondência para: {nome_remetente}")
        
        return {
            "success": True,
            "message": f"{atualizados} registros atualizados com responsáveis",
            "atualizados": atualizados,
            "total_analisados": len(response_extrato.data),
            "correspondencias": correspondencias,
            "debug_info": debug_info,
            "usou_nome_norm": usar_nome_norm
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao atualizar responsáveis: {str(e)}",
            "debug_info": debug_info
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

def atualizar_extrato_apos_pagamento(id_extrato: str, status: str = "registrado", id_aluno: Optional[str] = None) -> Dict:
    """
    Atualiza o registro do extrato_pix após um pagamento ser registrado
    
    Args:
        id_extrato: ID do registro no extrato_pix
        status: Novo status (default: "registrado")
        id_aluno: ID do aluno (opcional, usado quando responsável tem múltiplos alunos)
        
    Returns:
        Dict com resultado da operação
    """
    
    try:
        dados_update = {
            "status": status,
            "atualizado_em": datetime.now().isoformat()
        }
        
        # Se id_aluno foi fornecido, incluir na atualização
        if id_aluno:
            dados_update["id_aluno"] = id_aluno
        
        # Atualizar o registro
        supabase.table("extrato_pix").update(dados_update).eq("id", id_extrato).execute()
        
        return {
            "success": True,
            "message": f"Extrato {id_extrato} atualizado com status: {status}",
            "dados_atualizados": dados_update
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao atualizar extrato após pagamento: {str(e)}"
        }

def buscar_alunos_por_turmas(ids_turmas: List[str]) -> Dict:
    """
    Busca alunos por uma lista de IDs de turmas com informações completas dos responsáveis
    
    Args:
        ids_turmas: Lista de IDs das turmas para filtrar
        
    Returns:
        Dict com alunos encontrados agrupados por turma, incluindo dados dos responsáveis
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
            
            # Buscar responsáveis do aluno
            responsaveis_response = supabase.table("alunos_responsaveis").select("""
                tipo_relacao, responsavel_financeiro,
                responsaveis!inner(nome)
            """).eq("id_aluno", aluno["id"]).execute()
            
            # Organizar responsáveis
            responsaveis_info = []
            responsavel_financeiro_nome = "Não informado"
            
            for vinculo in responsaveis_response.data:
                resp_info = {
                    "nome": vinculo["responsaveis"]["nome"],
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
        Dict com informações completas do aluno
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
            "mensalidades_geradas": aluno.get("mensalidades_geradas", False)
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

# ==========================================================
# 📅 FUNÇÕES DE GERAÇÃO DE MENSALIDADES
# ==========================================================

def gerar_mensalidades_aluno(id_aluno: str, 
                            automatico: bool = True,
                            numero_parcelas: Optional[int] = None,
                            data_primeira_parcela: Optional[str] = None) -> Dict:
    """
    Gera mensalidades para um aluno baseado na data de matrícula
    
    Args:
        id_aluno: ID do aluno
        automatico: Se True, gera do mês seguinte à matrícula até dezembro
        numero_parcelas: Número de parcelas (usado quando automatico=False)
        data_primeira_parcela: Data da primeira parcela YYYY-MM-DD (usado quando automatico=False)
    
    Returns:
        Dict com resultado da operação
    """
    try:
        # 1. Buscar dados do aluno
        aluno_response = supabase.table("alunos").select("""
            id, nome, data_matricula, dia_vencimento, valor_mensalidade, mensalidades_geradas
        """).eq("id", id_aluno).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": f"Aluno com ID {id_aluno} não encontrado"}
        
        aluno = aluno_response.data[0]
        
        # 1.5. Buscar responsável financeiro do aluno
        responsavel_response = supabase.table("alunos_responsaveis").select("""
            id_responsavel
        """).eq("id_aluno", id_aluno).eq("responsavel_financeiro", True).execute()
        
        id_responsavel_financeiro = None
        if responsavel_response.data:
            id_responsavel_financeiro = responsavel_response.data[0]["id_responsavel"]
        else:
            # Se não há responsável financeiro marcado, buscar qualquer responsável
            resp_qualquer = supabase.table("alunos_responsaveis").select("""
                id_responsavel
            """).eq("id_aluno", id_aluno).limit(1).execute()
            
            if resp_qualquer.data:
                id_responsavel_financeiro = resp_qualquer.data[0]["id_responsavel"]
            else:
                return {"success": False, "error": "Aluno não possui responsável vinculado"}
        
        if not id_responsavel_financeiro:
            return {"success": False, "error": "Não foi possível identificar responsável financeiro do aluno"}
        
        # 2. Validar pré-requisitos
        if not aluno.get('data_matricula'):
            return {"success": False, "error": "Aluno não possui data de matrícula"}
        
        if not aluno.get('dia_vencimento'):
            return {"success": False, "error": "Aluno não possui dia de vencimento configurado"}
        
        if not aluno.get('valor_mensalidade') or float(aluno.get('valor_mensalidade', 0)) <= 0:
            return {"success": False, "error": "Aluno não possui valor de mensalidade configurado"}
        
        # 3. Verificar se tem pagamento de matrícula
        matricula_response = supabase.table("pagamentos").select("id_pagamento").eq(
            "id_aluno", id_aluno
        ).eq("tipo_pagamento", "matricula").execute()
        
        if not matricula_response.data:
            return {"success": False, "error": "Aluno não possui pagamento de matrícula registrado"}
        
        # 4. Verificar se já tem mensalidades geradas
        if aluno.get('mensalidades_geradas'):
            return {"success": False, "error": "Aluno já possui mensalidades geradas"}
        
        # 5. Calcular datas das mensalidades
        from datetime import datetime, timedelta
        try:
            from dateutil.relativedelta import relativedelta
        except ImportError:
            # Fallback se dateutil não estiver disponível
            def relativedelta(months=0):
                class RelativeDelta:
                    def __init__(self, months):
                        self.months = months
                return RelativeDelta(months)
        
        data_matricula = datetime.strptime(aluno['data_matricula'], '%Y-%m-%d').date()
        dia_vencimento = int(aluno['dia_vencimento'])
        valor_mensalidade = float(aluno['valor_mensalidade'])
        
        mensalidades_para_criar = []
        
        if automatico:
            # Modo automático: do mês seguinte à matrícula até dezembro
            mes_matricula = data_matricula.month
            ano_matricula = data_matricula.year
            
            # Regra especial: se matrícula foi em dezembro, começar em fevereiro do ano seguinte
            if mes_matricula == 12:
                mes_inicio = 2
                ano_inicio = ano_matricula + 1
            else:
                mes_inicio = mes_matricula + 1
                ano_inicio = ano_matricula
            
            # Gerar mensalidades até dezembro
            mes_atual = mes_inicio
            ano_atual = ano_inicio
            
            while mes_atual <= 12:
                try:
                    # Calcular data de vencimento
                    data_vencimento = datetime(ano_atual, mes_atual, dia_vencimento).date()
                    
                    # Nome do mês
                    nomes_meses = [
                        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ]
                    mes_referencia = f"{nomes_meses[mes_atual]}/{ano_atual}"
                    
                    mensalidades_para_criar.append({
                        "mes_referencia": mes_referencia,
                        "data_vencimento": data_vencimento.isoformat(),
                        "valor": valor_mensalidade
                    })
                    
                    mes_atual += 1
                    
                except ValueError:
                    # Dia não existe no mês (ex: 31 de fevereiro)
                    # Usar último dia do mês
                    import calendar
                    ultimo_dia = calendar.monthrange(ano_atual, mes_atual)[1]
                    data_vencimento = datetime(ano_atual, mes_atual, min(dia_vencimento, ultimo_dia)).date()
                    
                    nomes_meses = [
                        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ]
                    mes_referencia = f"{nomes_meses[mes_atual]}/{ano_atual}"
                    
                    mensalidades_para_criar.append({
                        "mes_referencia": mes_referencia,
                        "data_vencimento": data_vencimento.isoformat(),
                        "valor": valor_mensalidade
                    })
                    
                    mes_atual += 1
        
        else:
            # Modo manual: usar número de parcelas e data da primeira parcela
            if not numero_parcelas or numero_parcelas <= 0:
                return {"success": False, "error": "Número de parcelas deve ser maior que zero"}
            
            if not data_primeira_parcela:
                return {"success": False, "error": "Data da primeira parcela é obrigatória"}
            
            try:
                data_primeira = datetime.strptime(data_primeira_parcela, '%Y-%m-%d').date()
            except:
                return {"success": False, "error": "Data da primeira parcela deve estar no formato YYYY-MM-DD"}
            
            # Gerar mensalidades baseadas na primeira data
            for i in range(numero_parcelas):
                # Calcular próximo mês
                mes_atual = data_primeira.month + i
                ano_atual = data_primeira.year
                
                # Ajustar ano se necessário
                while mes_atual > 12:
                    mes_atual -= 12
                    ano_atual += 1
                
                try:
                    data_vencimento = datetime(ano_atual, mes_atual, dia_vencimento).date()
                except ValueError:
                    # Dia não existe no mês
                    import calendar
                    ultimo_dia = calendar.monthrange(ano_atual, mes_atual)[1]
                    data_vencimento = datetime(ano_atual, mes_atual, min(dia_vencimento, ultimo_dia)).date()
                
                # Nome do mês
                nomes_meses = [
                    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                ]
                mes_referencia = f"{nomes_meses[mes_atual]}/{ano_atual}"
                
                mensalidades_para_criar.append({
                    "mes_referencia": mes_referencia,
                    "data_vencimento": data_vencimento.isoformat(),
                    "valor": valor_mensalidade
                })
        
        # 6. Criar mensalidades no banco
        mensalidades_criadas = []
        
        for mensalidade_data in mensalidades_para_criar:
            id_mensalidade = f"MENS_{str(uuid.uuid4().int)[:8].upper()}"
            
            dados_mensalidade = {
                "id_mensalidade": id_mensalidade,
                "id_aluno": id_aluno,
                "id_responsavel": id_responsavel_financeiro,
                "mes_referencia": mensalidade_data["mes_referencia"],
                "valor": mensalidade_data["valor"],
                "data_vencimento": mensalidade_data["data_vencimento"],
                "status": "A vencer",
                "inserted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            response = supabase.table("mensalidades").insert(dados_mensalidade).execute()
            
            if response.data:
                mensalidades_criadas.append(response.data[0])
            else:
                # Se falhar, tentar reverter as já criadas
                for mens_criada in mensalidades_criadas:
                    supabase.table("mensalidades").delete().eq("id_mensalidade", mens_criada["id_mensalidade"]).execute()
                
                return {
                    "success": False, 
                    "error": f"Erro ao criar mensalidade {mensalidade_data['mes_referencia']}"
                }
        
        # 7. Marcar aluno como tendo mensalidades geradas
        supabase.table("alunos").update({
            "mensalidades_geradas": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", id_aluno).execute()
        
        return {
            "success": True,
            "mensalidades_criadas": len(mensalidades_criadas),
            "mensalidades": mensalidades_criadas,
            "modo": "automático" if automatico else "manual",
            "aluno_nome": aluno["nome"],
            "message": f"{len(mensalidades_criadas)} mensalidades geradas para {aluno['nome']}"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def verificar_pode_gerar_mensalidades(id_aluno: str) -> Dict:
    """
    Verifica se um aluno pode ter mensalidades geradas
    
    Args:
        id_aluno: ID do aluno
        
    Returns:
        Dict com resultado da verificação
    """
    try:
        # Buscar dados do aluno
        aluno_response = supabase.table("alunos").select("""
            id, nome, data_matricula, dia_vencimento, valor_mensalidade, mensalidades_geradas
        """).eq("id", id_aluno).execute()
        
        if not aluno_response.data:
            return {"success": False, "error": f"Aluno com ID {id_aluno} não encontrado"}
        
        aluno = aluno_response.data[0]
        
        # Verificar condições
        condicoes = {
            "tem_data_matricula": bool(aluno.get('data_matricula')),
            "tem_dia_vencimento": bool(aluno.get('dia_vencimento')),
            "tem_valor_mensalidade": bool(aluno.get('valor_mensalidade')) and float(aluno.get('valor_mensalidade', 0)) > 0,
            "ja_tem_mensalidades": bool(aluno.get('mensalidades_geradas')),
            "tem_pagamento_matricula": False,
            "tem_responsavel": False
        }
        
        # Verificar pagamento de matrícula
        matricula_response = supabase.table("pagamentos").select("id_pagamento").eq(
            "id_aluno", id_aluno
        ).eq("tipo_pagamento", "matricula").execute()
        
        condicoes["tem_pagamento_matricula"] = bool(matricula_response.data)
        
        # Verificar se tem responsável vinculado
        responsavel_response = supabase.table("alunos_responsaveis").select("id_responsavel").eq("id_aluno", id_aluno).execute()
        condicoes["tem_responsavel"] = bool(responsavel_response.data)
        
        # Determinar se pode gerar
        pode_gerar = (
            condicoes["tem_data_matricula"] and
            condicoes["tem_dia_vencimento"] and
            condicoes["tem_valor_mensalidade"] and
            condicoes["tem_pagamento_matricula"] and
            condicoes["tem_responsavel"] and
            not condicoes["ja_tem_mensalidades"]
        )
        
        # Preparar mensagens
        problemas = []
        if not condicoes["tem_data_matricula"]:
            problemas.append("❌ Falta data de matrícula")
        if not condicoes["tem_dia_vencimento"]:
            problemas.append("❌ Falta dia de vencimento")
        if not condicoes["tem_valor_mensalidade"]:
            problemas.append("❌ Falta valor da mensalidade")
        if not condicoes["tem_pagamento_matricula"]:
            problemas.append("❌ Falta pagamento de matrícula")
        if not condicoes["tem_responsavel"]:
            problemas.append("❌ Falta responsável vinculado")
        if condicoes["ja_tem_mensalidades"]:
            problemas.append("⚠️ Já possui mensalidades geradas")
        
        return {
            "success": True,
            "pode_gerar": pode_gerar,
            "condicoes": condicoes,
            "problemas": problemas,
            "aluno": aluno
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 📅 FUNÇÕES DE ATUALIZAÇÃO AUTOMÁTICA DE STATUS
# ==========================================================

def atualizar_status_mensalidades_automatico(limite_registros: int = 1000) -> Dict:
    """
    Atualiza automaticamente o status das mensalidades de "A vencer" 
    para "Atrasado" quando a data de vencimento for anterior à data atual.
    
    Args:
        limite_registros: Limite de registros para processar por vez
        
    Returns:
        Dict: {"success": bool, "atualizadas": int, "detalhes": List}
    """
    try:
        from datetime import datetime, date
        
        # Data atual
        data_hoje = date.today().isoformat()
        
        # Buscar mensalidades com status "A vencer" e data de vencimento anterior a hoje
        response = supabase.table("mensalidades").select(
            "id_mensalidade, mes_referencia, data_vencimento, status, id_aluno"
        ).eq("status", "A vencer").lt("data_vencimento", data_hoje).limit(limite_registros).execute()
        
        if not response.data:
            return {
                "success": True,
                "atualizadas": 0,
                "detalhes": [],
                "message": "Nenhuma mensalidade precisava ser atualizada"
            }
        
        # Atualizar cada mensalidade
        mensalidades_atualizadas = []
        erros = []
        
        for mensalidade in response.data:
            try:
                # Atualizar status para "Atrasado"
                update_response = supabase.table("mensalidades").update({
                    "status": "Atrasado",
                    "updated_at": datetime.now().isoformat()
                }).eq("id_mensalidade", mensalidade["id_mensalidade"]).execute()
                
                if update_response.data:
                    mensalidades_atualizadas.append({
                        "id_mensalidade": mensalidade["id_mensalidade"],
                        "mes_referencia": mensalidade["mes_referencia"],
                        "data_vencimento": mensalidade["data_vencimento"],
                        "status_anterior": "A vencer",
                        "status_novo": "Atrasado"
                    })
                else:
                    erros.append(f"Erro ao atualizar {mensalidade['id_mensalidade']}")
                    
            except Exception as e:
                erros.append(f"Erro na mensalidade {mensalidade['id_mensalidade']}: {str(e)}")
        
        resultado = {
            "success": True,
            "atualizadas": len(mensalidades_atualizadas),
            "total_encontradas": len(response.data),
            "detalhes": mensalidades_atualizadas,
            "erros": erros,
            "data_execucao": datetime.now().isoformat()
        }
        
        if erros:
            resultado["warning"] = f"{len(erros)} mensalidades não puderam ser atualizadas"
            
        return resultado
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao atualizar status das mensalidades: {str(e)}",
            "atualizadas": 0
        }

def verificar_mensalidades_precisam_atualizacao() -> Dict:
    """
    Verifica quantas mensalidades precisam ter o status atualizado
    sem fazer a atualização.
    
    Returns:
        Dict: {"success": bool, "count": int, "mensalidades": List}
    """
    try:
        from datetime import date
        
        data_hoje = date.today().isoformat()
        
        # Contar mensalidades que precisam ser atualizadas
        response = supabase.table("mensalidades").select(
            "id_mensalidade, mes_referencia, data_vencimento, id_aluno"
        ).eq("status", "A vencer").lt("data_vencimento", data_hoje).execute()
        
        return {
            "success": True,
            "count": len(response.data),
            "mensalidades": response.data,
            "data_verificacao": date.today().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "count": 0
        }

if __name__ == "__main__":
    print("🧪 Testando funções otimizadas...")
    
    # Teste básico
    stats = obter_estatisticas_extrato()
    if stats["success"]:
        print(f"✅ Estatísticas: {stats['estatisticas']['total_registros']} registros")
    else:
        print(f"❌ Erro: {stats['error']}")
    
    print("✅ Funções otimizadas prontas para uso!") 