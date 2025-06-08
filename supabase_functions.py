import os
import uuid
import unicodedata
import re
from datetime import datetime, date
from typing import Optional, Dict, List, Any, Union
from supabase import create_client
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# Configurações do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def converter_data(data_str: str) -> str:
    """Converte diferentes formatos de data para o formato do banco (YYYY-MM-DD)"""
    if not data_str:
        return None
    
    # Se já está no formato correto
    if len(data_str) == 10 and data_str[4] == '-' and data_str[7] == '-':
        return data_str
    
    # Formatos aceitos: DD/MM/YYYY, DD-MM-YYYY
    for separador in ['/', '-']:
        if separador in data_str:
            partes = data_str.split(separador)
            if len(partes) == 3:
                # DD/MM/YYYY ou DD-MM-YYYY
                if len(partes[2]) == 4:
                    return f"{partes[2]}-{partes[1].zfill(2)}-{partes[0].zfill(2)}"
                # YYYY/MM/DD ou YYYY-MM-DD  
                elif len(partes[0]) == 4:
                    return f"{partes[0]}-{partes[1].zfill(2)}-{partes[2].zfill(2)}"
    
    raise ValueError(f"Formato de data inválido: {data_str}")

def gerar_id_aluno() -> str:
    """Gera um novo ID para aluno no formato ALU_XXXXXX"""
    return f"ALU_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_responsavel() -> str:
    """Gera um novo ID para responsável no formato RES_XXXXXX"""
    return f"RES_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_pagamento() -> str:
    """Gera um novo ID para pagamento no formato PAG_XXXXXX"""
    return f"PAG_{str(uuid.uuid4().int)[:6].upper()}"

def normalizar_nome(nome: str) -> str:
    """Normaliza nome removendo acentos, convertendo para minúsculas e removendo palavras conectivas"""
    if not nome or not nome.strip():
        return ""
    
    # Remove acentos/diacríticos
    nome_sem_acento = unicodedata.normalize('NFD', nome)
    nome_sem_acento = ''.join(char for char in nome_sem_acento if unicodedata.category(char) != 'Mn')
    
    # Converte para minúsculas
    nome_normalizado = nome_sem_acento.lower().strip()
    
    # Remove palavras conectivas comuns
    palavras_conectivas = ['de', 'da', 'do', 'dos', 'das', 'e', 'del', 'la', 'el']
    palavras = nome_normalizado.split()
    palavras_filtradas = [palavra for palavra in palavras if palavra not in palavras_conectivas]
    
    # Reconstitui o nome
    return ' '.join(palavras_filtradas)

def nomes_sao_similares(nome1: str, nome2: str) -> bool:
    """Verifica se dois nomes são similares após normalização"""
    nome1_norm = normalizar_nome(nome1)
    nome2_norm = normalizar_nome(nome2)
    
    # Correspondência exata
    if nome1_norm == nome2_norm:
        return True
    
    # Verifica se um nome está contido no outro (para casos como "João Silva" vs "João da Silva")
    palavras1 = set(nome1_norm.split())
    palavras2 = set(nome2_norm.split())
    
    # Se uma das listas tem pelo menos 80% das palavras da outra, considera similar
    if len(palavras1) >= 2 and len(palavras2) >= 2:
        intersecao = len(palavras1.intersection(palavras2))
        return (intersecao / len(palavras1) >= 0.8) or (intersecao / len(palavras2) >= 0.8)
    
    return False

# ========================= FUNÇÕES DE LISTAGEM =========================

def listar_alunos(filtro_nome: Optional[str] = None, 
                  filtro_turma: Optional[str] = None,
                  sem_dia_vencimento: Optional[bool] = None,
                  sem_data_matricula: Optional[bool] = None,
                  sem_valor_mensalidade: Optional[bool] = None,
                  id_aluno: Optional[str] = None) -> Dict:
    """Lista alunos com filtros opcionais"""
    try:
        query = supabase.table("alunos").select("*, turmas(nome_turma)")
        
        if id_aluno:
            query = query.eq("id", id_aluno)
        
        if filtro_nome:
            query = query.ilike("nome", f"%{filtro_nome}%")
            
        if filtro_turma:
            query = query.eq("turmas.nome_turma", filtro_turma)
            
        if sem_dia_vencimento:
            query = query.is_("dia_vencimento", "null")
            
        if sem_data_matricula:
            query = query.is_("data_matricula", "null")
            
        if sem_valor_mensalidade:
            query = query.is_("valor_mensalidade", "null")
        
        response = query.execute()
        return {"success": True, "data": response.data, "count": len(response.data)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_responsaveis(filtro_nome: Optional[str] = None, 
                       cpf: Optional[str] = None) -> Dict:
    """Lista responsáveis cadastrados"""
    try:
        query = supabase.table("responsaveis").select("*")
        
        if filtro_nome:
            query = query.ilike("nome", f"%{filtro_nome}%")
            
        if cpf:
            query = query.eq("cpf", cpf)
        
        response = query.execute()
        return {"success": True, "data": response.data, "count": len(response.data)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_pagamentos(filtros: Optional[Dict] = None) -> Dict:
    """Lista pagamentos cadastrados"""
    try:
        query = supabase.table("pagamentos").select("*, responsaveis(nome), alunos(nome)")
        
        if filtros:
            for campo, valor in filtros.items():
                if campo in ["id_responsavel", "id_aluno", "tipo_pagamento", "forma_pagamento"]:
                    query = query.eq(campo, valor)
                elif campo == "data_pagamento_inicial":
                    query = query.gte("data_pagamento", valor)
                elif campo == "data_pagamento_final":
                    query = query.lte("data_pagamento", valor)
        
        response = query.execute()
        return {"success": True, "data": response.data, "count": len(response.data)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_mensalidades(id_aluno: str) -> Dict:
    """Lista mensalidades de um aluno específico"""
    try:
        response = (supabase.table("mensalidades")
                   .select("*, responsaveis(nome), alunos(nome)")
                   .eq("id_aluno", id_aluno)
                   .order("data_vencimento", desc=True)
                   .execute())
        
        return {"success": True, "data": response.data, "count": len(response.data)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def consultar_extrato_pix(limite: Optional[int] = None, 
                         filtros: Optional[Dict] = None) -> Dict:
    """Consulta registros do extrato PIX com filtros opcionais"""
    try:
        query = supabase.table("extrato_pix").select("*")
        
        if filtros:
            for campo, valor in filtros.items():
                if campo == "status":
                    query = query.eq("status", valor)
                elif campo == "nome_remetente":
                    query = query.ilike("nome_remetente", f"%{valor}%")
                elif campo == "data_inicial":
                    query = query.gte("data_pagamento", valor)
                elif campo == "data_final":
                    query = query.lte("data_pagamento", valor)
        
        query = query.order("data_pagamento", desc=True)
        
        if limite:
            query = query.limit(limite)
        
        response = query.execute()
        return {"success": True, "data": response.data, "count": len(response.data)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================= FUNÇÕES ESPECÍFICAS DO EXTRATO PIX =========================

def identificar_responsaveis_nao_cadastrados() -> Dict:
    """Identifica responsáveis presentes no extrato_pix que não estão cadastrados em responsáveis"""
    try:
        # Busca todos os nomes únicos do extrato_pix (com normalização)
        extrato_response = (supabase.table("extrato_pix")
                           .select("nome_remetente")
                           .execute())
        
        # Normaliza nomes do extrato (remove espaços extras, converte para minúsculo)
        nomes_extrato_raw = [item["nome_remetente"] for item in extrato_response.data if item["nome_remetente"] and item["nome_remetente"].strip()]
        nomes_extrato_normalizados = {}  # {nome_normalizado: nome_original}
        
        for nome in nomes_extrato_raw:
            nome_original = nome.strip()
            nome_normalizado = nome_original.lower().strip()
            if nome_normalizado and nome_normalizado not in nomes_extrato_normalizados:
                nomes_extrato_normalizados[nome_normalizado] = nome_original
        
        # Busca todos os responsáveis já cadastrados (com normalização)
        responsaveis_response = (supabase.table("responsaveis")
                               .select("nome")
                               .execute())
        
        # Normaliza nomes dos responsáveis
        nomes_responsaveis_normalizados = set()
        for item in responsaveis_response.data:
            if item["nome"] and item["nome"].strip():
                nome_normalizado = item["nome"].lower().strip()
                nomes_responsaveis_normalizados.add(nome_normalizado)
        
        # Identifica os nomes não cadastrados (que estão no extrato mas NÃO estão na tabela responsáveis)
        nomes_nao_cadastrados_normalizados = set(nomes_extrato_normalizados.keys()) - nomes_responsaveis_normalizados
        
        # Converte de volta para nomes originais
        nomes_nao_cadastrados_originais = [nomes_extrato_normalizados[nome_norm] for nome_norm in nomes_nao_cadastrados_normalizados]
        
        # Log informativo
        print(f"✅ Análise concluída: {len(nomes_extrato_normalizados)} nomes únicos no extrato, {len(nomes_responsaveis_normalizados)} responsáveis cadastrados")
        
        if len(nomes_nao_cadastrados_originais) == 0:
            print("✅ Todos os responsáveis do extrato PIX já estão cadastrados na tabela responsáveis")
        
        # Busca detalhes dos não cadastrados no extrato
        detalhes_nao_cadastrados = []
        for nome_original in nomes_nao_cadastrados_originais:
            pagamentos = (supabase.table("extrato_pix")
                         .select("*")
                         .eq("nome_remetente", nome_original)
                         .execute())
            
            total_valor = sum([float(p["valor"]) for p in pagamentos.data])
            detalhes_nao_cadastrados.append({
                "nome": nome_original,
                "quantidade_pagamentos": len(pagamentos.data),
                "valor_total": total_valor,
                "pagamentos": pagamentos.data
            })
        
        return {
            "success": True, 
            "nomes_nao_cadastrados": nomes_nao_cadastrados_originais,
            "detalhes": detalhes_nao_cadastrados,
            "count": len(nomes_nao_cadastrados_originais),
            "total_nomes_extrato": len(nomes_extrato_normalizados),
            "total_responsaveis_cadastrados": len(nomes_responsaveis_normalizados)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_responsaveis_extrato_por_nome() -> Dict:
    """
    Atualiza a coluna id_responsavel da tabela extrato_pix
    com base na correspondência normalizada entre nome_remetente e nome da tabela responsáveis.
    Usa normalização para ignorar acentos e pequenas palavras conectivas.
    SOBRESCREVE valores existentes para corrigir registros inseridos incorretamente.
    """
    try:
        # 1. Buscar todos os responsáveis cadastrados
        responsaveis_response = supabase.table("responsaveis").select("id, nome").execute()
        responsaveis = responsaveis_response.data

        if not responsaveis:
            return {"success": False, "error": "Nenhum responsável cadastrado"}

        # 2. Buscar todos os registros do extrato_pix
        extrato_response = supabase.table("extrato_pix").select("id, nome_remetente").execute()
        registros_extrato = extrato_response.data

        if not registros_extrato:
            return {"success": False, "error": "Nenhum registro no extrato PIX"}

        atualizados = 0
        erros = []
        correspondencias = []

        # 3. Para cada responsável, buscar correspondências no extrato usando normalização
        for responsavel in responsaveis:
            nome_responsavel = responsavel["nome"]
            id_responsavel = responsavel["id"]
            
            registros_para_atualizar = []

            # Busca registros do extrato que correspondem a este responsável
            for registro in registros_extrato:
                nome_extrato = registro["nome_remetente"]
                
                if nome_extrato and nomes_sao_similares(nome_responsavel, nome_extrato):
                    registros_para_atualizar.append(registro["id"])

            # Se encontrou correspondências, atualiza os registros
            if registros_para_atualizar:
                try:
                    for id_registro in registros_para_atualizar:
                        update_response = (
                            supabase.table("extrato_pix")
                            .update({
                                "id_responsavel": id_responsavel,
                                "atualizado_em": datetime.now().isoformat()
                            })
                            .eq("id", id_registro)
                            .execute()
                        )

                    atualizados += len(registros_para_atualizar)
                    correspondencias.append({
                        "nome_responsavel": nome_responsavel,
                        "id_responsavel": id_responsavel,
                        "registros_atualizados": len(registros_para_atualizar),
                        "nomes_extrato_correspondentes": [reg.get("nome_remetente") for reg in registros_extrato 
                                                        if reg["id"] in registros_para_atualizar]
                    })

                except Exception as e:
                    erros.append(f"{nome_responsavel}: {str(e)}")

        return {
            "success": True,
            "total_responsaveis": len(responsaveis),
            "registros_atualizados": atualizados,
            "correspondencias_encontradas": len(correspondencias),
            "detalhes_correspondencias": correspondencias,
            "erros": erros if erros else None,
            "resumo": f"Atualizados {atualizados} registros do extrato PIX com base em {len(correspondencias)} correspondências normalizadas de nomes (de {len(responsaveis)} responsáveis cadastrados)"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_registros_extrato_com_responsaveis_cadastrados(limite: Optional[int] = 50) -> Dict:
    """Lista registros do extrato PIX cujos remetentes já estão cadastrados como responsáveis"""
    try:
        # Busca todos os responsáveis cadastrados
        responsaveis_response = (supabase.table("responsaveis")
                               .select("nome")
                               .execute())
        
        nomes_cadastrados = set([item["nome"] for item in responsaveis_response.data])
        
        # Busca registros do extrato cujos remetentes estão cadastrados
        registros_identificados = []
        for nome in nomes_cadastrados:
            pagamentos = (supabase.table("extrato_pix")
                         .select("*")
                         .eq("nome_remetente", nome)
                         .execute())
            
            if pagamentos.data:
                registros_identificados.extend(pagamentos.data)
        
        # Ordena por data de pagamento (mais recentes primeiro)
        registros_identificados.sort(key=lambda x: x.get("data_pagamento", ""), reverse=True)
        
        # Aplica limite se especificado
        if limite:
            registros_identificados = registros_identificados[:limite]
        
        return {
            "success": True,
            "data": registros_identificados,
            "count": len(registros_identificados),
            "total_identificados": len(registros_identificados)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_pagamentos_por_responsavel_ordenados(status_filtro: Optional[str] = "novo") -> Dict:
    """Lista pagamentos do extrato_pix por responsável cadastrado, ordenados por data (mais antigo primeiro)"""
    try:
        # Busca registros do extrato com responsáveis identificados
        query = (supabase.table("extrato_pix")
                .select("*, responsaveis(nome)")
                .not_.is_("id_responsavel", "null"))
        
        if status_filtro:
            query = query.eq("status", status_filtro)
        
        response = query.execute()
        
        if not response.data:
            return {
                "success": True,
                "pagamentos_por_responsavel": [],
                "total_responsaveis": 0,
                "total_pagamentos": 0,
                "resumo": "Nenhum pagamento encontrado com os critérios especificados"
            }
        
        # Organiza por responsável
        pagamentos_por_responsavel = {}
        
        for registro in response.data:
            nome_responsavel = registro.get("nome_remetente", "Nome não disponível")
            id_responsavel = registro.get("id_responsavel")
            
            if nome_responsavel not in pagamentos_por_responsavel:
                pagamentos_por_responsavel[nome_responsavel] = {
                    "id_responsavel": id_responsavel,
                    "nome": nome_responsavel,
                    "pagamentos": []
                }
            
            pagamentos_por_responsavel[nome_responsavel]["pagamentos"].append({
                "id": registro.get("id"),
                "data_pagamento": registro.get("data_pagamento"),
                "valor": registro.get("valor"),
                "status": registro.get("status"),
                "descricao": registro.get("descricao")
            })
        
        # Ordena pagamentos de cada responsável por data (mais antigo primeiro)
        for responsavel in pagamentos_por_responsavel.values():
            responsavel["pagamentos"].sort(key=lambda x: x["data_pagamento"] or "")
        
        # Converte para lista ordenada por nome do responsável
        resultado_lista = sorted(pagamentos_por_responsavel.values(), key=lambda x: x["nome"])
        
        total_pagamentos = sum(len(resp["pagamentos"]) for resp in resultado_lista)
        
        return {
            "success": True,
            "pagamentos_por_responsavel": resultado_lista,
            "total_responsaveis": len(resultado_lista),
            "total_pagamentos": total_pagamentos,
            "status_filtro": status_filtro,
            "resumo": f"Encontrados {total_pagamentos} pagamentos de {len(resultado_lista)} responsáveis (status: {status_filtro})"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_pagamentos_nao_identificados(limite: Optional[int] = 50, 
                                       formato_resumido: Optional[bool] = True) -> Dict:
    """Lista pagadores do extrato PIX que não foram identificados"""
    try:
        query = (supabase.table("extrato_pix")
                .select("*")
                .is_("id_responsavel", "null")
                .order("data_pagamento", desc=True))
        
        if limite:
            query = query.limit(limite)
        
        response = query.execute()
        
        if formato_resumido:
            resumo = {}
            for item in response.data:
                nome = item["nome_remetente"]
                if nome not in resumo:
                    resumo[nome] = {"quantidade": 0, "valor_total": 0, "datas": []}
                resumo[nome]["quantidade"] += 1
                resumo[nome]["valor_total"] += float(item["valor"])
                resumo[nome]["datas"].append(item["data_pagamento"])
            
            return {"success": True, "resumo": resumo, "data_completa": response.data}
        
        return {"success": True, "data": response.data, "count": len(response.data)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def analisar_estatisticas_extrato() -> Dict:
    """Gera estatísticas completas do extrato PIX"""
    try:
        # Estatísticas gerais
        total_response = supabase.table("extrato_pix").select("*").execute()
        total_registros = len(total_response.data)
        
        identificados_response = (supabase.table("extrato_pix")
                                .select("*")
                                .not_.is_("id_responsavel", "null")
                                .execute())
        total_identificados = len(identificados_response.data)
        
        nao_identificados = total_registros - total_identificados
        
        # Valores
        valor_total = sum([float(item["valor"]) for item in total_response.data])
        valor_identificado = sum([float(item["valor"]) for item in identificados_response.data])
        valor_nao_identificado = valor_total - valor_identificado
        
        # Por status
        stats_por_status = {}
        for item in total_response.data:
            status = item["status"]
            if status not in stats_por_status:
                stats_por_status[status] = {"count": 0, "valor": 0}
            stats_por_status[status]["count"] += 1
            stats_por_status[status]["valor"] += float(item["valor"])
        
        return {
            "success": True,
            "estatisticas": {
                "total_registros": total_registros,
                "total_identificados": total_identificados,
                "total_nao_identificados": nao_identificados,
                "percentual_identificacao": round((total_identificados / total_registros) * 100, 2) if total_registros > 0 else 0,
                "valor_total": valor_total,
                "valor_identificado": valor_identificado,
                "valor_nao_identificado": valor_nao_identificado,
                "stats_por_status": stats_por_status
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def remover_pagamentos_extrato(nomes_pagadores: List[str]) -> Dict:
    """Remove registros específicos do extrato PIX por nome do pagador"""
    try:
        removidos = 0
        erros = []
        
        for nome in nomes_pagadores:
            try:
                response = (supabase.table("extrato_pix")
                           .delete()
                           .eq("nome_remetente", nome)
                           .execute())
                removidos += len(response.data) if response.data else 0
            except Exception as e:
                erros.append(f"Erro ao remover {nome}: {str(e)}")
        
        return {
            "success": True,
            "removidos": removidos,
            "erros": erros if erros else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================= FUNÇÕES DE CADASTRO =========================

def cadastrar_responsavel_e_vincular_aluno(nome_responsavel: str,
                                         nome_aluno: str,
                                         cpf: Optional[str] = None,
                                         telefone: Optional[str] = None,
                                         email: Optional[str] = None,
                                         endereco: Optional[str] = None,
                                         tipo_relacao: Optional[str] = None) -> Dict:
    """Cadastra responsável e vincula automaticamente ao aluno especificado"""
    try:
        # Primeiro, busca o aluno pelo nome
        resultado_busca = buscar_aluno_por_nome(nome_aluno)
        
        if not resultado_busca["success"] or resultado_busca["count"] == 0:
            return {"success": False, "error": f"Aluno '{nome_aluno}' não encontrado"}
        
        # Se encontrou múltiplos alunos, retorna erro pedindo especificação
        if resultado_busca["count"] > 1:
            alunos_encontrados = [f"{a['nome']} (ID: {a['id']})" for a in resultado_busca["data"]]
            return {
                "success": False, 
                "error": f"Múltiplos alunos encontrados: {', '.join(alunos_encontrados)}. Especifique o ID do aluno."
            }
        
        aluno = resultado_busca["data"][0]
        id_aluno = aluno["id"]
        
        # Cadastra o responsável
        resultado_cadastro = cadastrar_responsavel_completo(
            nome=nome_responsavel,
            cpf=cpf,
            telefone=telefone,
            email=email,
            endereco=endereco,
            tipo_relacao=tipo_relacao
        )
        
        if not resultado_cadastro["success"]:
            return resultado_cadastro
        
        id_responsavel = resultado_cadastro["id_responsavel"]
        
        # Vincula responsável ao aluno
        resultado_vinculo = vincular_aluno_responsavel(
            id_aluno=id_aluno,
            id_responsavel=id_responsavel,
            responsavel_financeiro=True,
            tipo_relacao=tipo_relacao
        )
        
        if not resultado_vinculo["success"]:
            return {
                "success": False,
                "error": f"Responsável cadastrado mas erro ao vincular: {resultado_vinculo.get('error')}",
                "id_responsavel": id_responsavel
            }
        
        return {
            "success": True,
            "id_responsavel": id_responsavel,
            "id_aluno": id_aluno,
            "id_vinculo": resultado_vinculo["id_vinculo"],
            "nome_responsavel": nome_responsavel,
            "nome_aluno": aluno["nome"],
            "tipo_relacao": tipo_relacao,
            "message": f"Responsável {nome_responsavel} cadastrado e vinculado como {tipo_relacao} do aluno {aluno['nome']}"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_responsavel_completo(nome: str,
                                  cpf: Optional[str] = None,
                                  telefone: Optional[str] = None,
                                  email: Optional[str] = None,
                                  endereco: Optional[str] = None,
                                  tipo_relacao: Optional[str] = None) -> Dict:
    """Cadastra um novo responsável"""
    try:
        id_responsavel = gerar_id_responsavel()
        
        dados_responsavel = {
            "id": id_responsavel,
            "nome": nome,
            "cpf": cpf,
            "telefone": telefone,
            "email": email,
            "endereco": endereco,
            "tipo_relacao": tipo_relacao,
            "responsavel_financeiro": True,
            "inserted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table("responsaveis").insert(dados_responsavel).execute()
        
        return {
            "success": True,
            "id_responsavel": id_responsavel,
            "data": response.data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_aluno(nome: str,
                   nome_turma: str,
                   data_nascimento: Optional[str] = None,
                   dia_vencimento: Optional[int] = None,
                   valor_mensalidade: Optional[float] = None,
                   data_matricula: Optional[str] = None,
                   turno: Optional[str] = None) -> Dict:
    """Cadastra um novo aluno"""
    try:
        # Busca o ID da turma pelo nome
        turma_response = (supabase.table("turmas")
                         .select("id")
                         .eq("nome_turma", nome_turma)
                         .execute())
        
        if not turma_response.data:
            return {"success": False, "error": f"Turma '{nome_turma}' não encontrada"}
        
        id_turma = turma_response.data[0]["id"]
        id_aluno = gerar_id_aluno()
        
        dados_aluno = {
            "id": id_aluno,
            "nome": nome,
            "id_turma": id_turma,
            "inserted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if data_nascimento:
            dados_aluno["data_nascimento"] = converter_data(data_nascimento)
        if dia_vencimento:
            dados_aluno["dia_vencimento"] = str(dia_vencimento)
        if valor_mensalidade:
            dados_aluno["valor_mensalidade"] = valor_mensalidade
        if data_matricula:
            dados_aluno["data_matricula"] = converter_data(data_matricula)
        if turno:
            dados_aluno["turno"] = turno
        
        response = supabase.table("alunos").insert(dados_aluno).execute()
        
        return {
            "success": True,
            "id_aluno": id_aluno,
            "data": response.data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def verificar_responsaveis_financeiros(id_aluno: str) -> Dict:
    """Verifica todos os responsáveis vinculados a um aluno"""
    try:
        # Busca todos os responsáveis vinculados (não apenas financeiros)
        response = (supabase.table("alunos_responsaveis")
                   .select("*, responsaveis(nome, cpf, telefone, email)")
                   .eq("id_aluno", id_aluno)
                   .execute())
        
        # Organiza os dados de forma mais clara
        responsaveis_organizados = []
        for vinculo in response.data:
            responsavel_info = vinculo.get("responsaveis", {})
            responsaveis_organizados.append({
                "id_responsavel": vinculo.get("id_responsavel"),
                "nome": responsavel_info.get("nome"),
                "cpf": responsavel_info.get("cpf"),
                "telefone": responsavel_info.get("telefone"),
                "email": responsavel_info.get("email"),
                "tipo_relacao": vinculo.get("tipo_relacao"),
                "responsavel_financeiro": vinculo.get("responsavel_financeiro", False),
                "data_vinculo": vinculo.get("created_at")
            })
        
        return {
            "success": True,
            "responsaveis_vinculados": responsaveis_organizados,
            "count": len(responsaveis_organizados),
            "aluno_id": id_aluno
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def vincular_aluno_responsavel(id_aluno: str, 
                              id_responsavel: str,
                              responsavel_financeiro: bool = True,
                              tipo_relacao: Optional[str] = None) -> Dict:
    """Vincula um aluno a um responsável"""
    try:
        id_vinculo = f"AR_{str(uuid.uuid4().int)[:8].upper()}"
        
        dados_vinculo = {
            "id": id_vinculo,
            "id_aluno": id_aluno,
            "id_responsavel": id_responsavel,
            "responsavel_financeiro": responsavel_financeiro,
            "tipo_relacao": tipo_relacao,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table("alunos_responsaveis").insert(dados_vinculo).execute()
        
        return {
            "success": True,
            "id_vinculo": id_vinculo,
            "data": response.data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def registrar_pagamento(id_responsavel: str,
                       id_aluno: str,
                       data_pagamento: str,
                       valor: float,
                       tipo_pagamento: str,
                       forma_pagamento: str,
                       descricao: Optional[str] = None,
                       id_extrato_pix: Optional[str] = None) -> Dict:
    """Registra um pagamento na tabela pagamentos e atualiza status do extrato_pix se aplicável"""
    try:
        # Converte data se necessário
        data_convertida = converter_data(data_pagamento)
        
        # Gera ID único para o pagamento
        id_pagamento = gerar_id_pagamento()
        
        dados_pagamento = {
            "id_pagamento": id_pagamento,
            "id_responsavel": id_responsavel,
            "id_aluno": id_aluno,
            "data_pagamento": data_convertida,
            "valor": valor,
            "tipo_pagamento": tipo_pagamento,
            "forma_pagamento": forma_pagamento,
            "descricao": descricao,
            "inserted_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Registra o pagamento
        response = supabase.table("pagamentos").insert(dados_pagamento).execute()
        
        # Se é pagamento de matrícula, atualiza/insere data_matricula do aluno
        if tipo_pagamento.lower() == "matricula":
            try:
                update_aluno_response = (supabase.table("alunos")
                                       .update({
                                           "data_matricula": data_convertida,
                                           "updated_at": datetime.now().isoformat()
                                       })
                                       .eq("id", id_aluno)
                                       .execute())
            except Exception as e:
                print(f"⚠️ Aviso: Erro ao atualizar data_matricula do aluno: {str(e)}")
        
        # Se veio de um extrato_pix, atualiza o status para "registrado"
        if id_extrato_pix:
            try:
                update_extrato_response = (supabase.table("extrato_pix")
                                         .update({
                                             "status": "registrado",
                                             "atualizado_em": datetime.now().isoformat()
                                         })
                                         .eq("id", id_extrato_pix)
                                         .execute())
            except Exception as e:
                print(f"⚠️ Aviso: Erro ao atualizar status do extrato_pix: {str(e)}")
        
        return {
            "success": True,
            "id_pagamento": id_pagamento,
            "data": response.data,
            "data_matricula_atualizada": tipo_pagamento.lower() == "matricula",
            "status_extrato_atualizado": bool(id_extrato_pix)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================= FUNÇÕES DE ATUALIZAÇÃO =========================

def atualizar_dados_aluno(id_aluno: str, campos_para_atualizar: Dict) -> Dict:
    """Atualiza dados de um aluno existente"""
    try:
        # Processa campos especiais
        if "data_matricula" in campos_para_atualizar:
            campos_para_atualizar["data_matricula"] = converter_data(campos_para_atualizar["data_matricula"])
        
        if "nome_turma" in campos_para_atualizar:
            turma_response = (supabase.table("turmas")
                             .select("id")
                             .eq("nome_turma", campos_para_atualizar["nome_turma"])
                             .execute())
            
            if not turma_response.data:
                return {"success": False, "error": f"Turma '{campos_para_atualizar['nome_turma']}' não encontrada"}
            
            campos_para_atualizar["id_turma"] = turma_response.data[0]["id"]
            del campos_para_atualizar["nome_turma"]
        
        if "dia_vencimento" in campos_para_atualizar:
            campos_para_atualizar["dia_vencimento"] = str(campos_para_atualizar["dia_vencimento"])
        
        campos_para_atualizar["updated_at"] = datetime.now().isoformat()
        
        response = (supabase.table("alunos")
                   .update(campos_para_atualizar)
                   .eq("id", id_aluno)
                   .execute())
        
        return {"success": True, "data": response.data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_dados_responsavel(id_responsavel: str, campos_para_atualizar: Dict) -> Dict:
    """Atualiza dados de um responsável existente"""
    try:
        campos_para_atualizar["updated_at"] = datetime.now().isoformat()
        
        response = (supabase.table("responsaveis")
                   .update(campos_para_atualizar)
                   .eq("id", id_responsavel)
                   .execute())
        
        return {"success": True, "data": response.data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def atualizar_responsavel_extrato_pix(nome_remetente: str, id_responsavel: str) -> Dict:
    """Atualiza registros do extrato PIX com o ID do responsável"""
    try:
        response = (supabase.table("extrato_pix")
                   .update({"id_responsavel": id_responsavel})
                   .eq("nome_remetente", nome_remetente)
                   .is_("id_responsavel", "null")
                   .execute())
        
        return {
            "success": True,
            "registros_atualizados": len(response.data) if response.data else 0,
            "data": response.data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================= FUNÇÕES DE PROCESSAMENTO EM MASSA =========================

def processar_responsaveis_extrato_pix() -> Dict:
    """Processa responsáveis do extrato PIX, cadastrando os não identificados"""
    try:
        # Identifica responsáveis não cadastrados
        resultado_identificacao = identificar_responsaveis_nao_cadastrados()
        
        if not resultado_identificacao["success"]:
            return resultado_identificacao
        
        responsaveis_cadastrados = []
        erros = []
        
        for detalhe in resultado_identificacao["detalhes"]:
            nome = detalhe["nome"]
            
            # Cadastra o responsável
            resultado_cadastro = cadastrar_responsavel_completo(nome=nome)
            
            if resultado_cadastro["success"]:
                id_responsavel = resultado_cadastro["id_responsavel"]
                
                # Atualiza registros do extrato PIX
                resultado_atualizacao = atualizar_responsavel_extrato_pix(nome, id_responsavel)
                
                responsaveis_cadastrados.append({
                    "nome": nome,
                    "id_responsavel": id_responsavel,
                    "registros_atualizados": resultado_atualizacao.get("registros_atualizados", 0)
                })
            else:
                erros.append(f"Erro ao cadastrar {nome}: {resultado_cadastro['error']}")
        
        return {
            "success": True,
            "responsaveis_cadastrados": responsaveis_cadastrados,
            "total_cadastrados": len(responsaveis_cadastrados),
            "erros": erros if erros else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def cadastrar_responsaveis_em_massa(nomes_responsaveis: List[str]) -> Dict:
    """Cadastra múltiplos responsáveis"""
    try:
        responsaveis_cadastrados = []
        erros = []
        
        dados_para_inserir = []
        
        for nome in nomes_responsaveis:
            id_responsavel = gerar_id_responsavel()
            
            dados_responsavel = {
                "id": id_responsavel,
                "nome": nome,
                "responsavel_financeiro": True,
                "inserted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            dados_para_inserir.append(dados_responsavel)
            responsaveis_cadastrados.append({
                "nome": nome,
                "id_responsavel": id_responsavel
            })
        
        # Insert em massa
        try:
            response = supabase.table("responsaveis").insert(dados_para_inserir).execute()
            
            return {
                "success": True,
                "responsaveis_cadastrados": responsaveis_cadastrados,
                "total_cadastrados": len(responsaveis_cadastrados),
                "data": response.data
            }
        except Exception as e:
            return {"success": False, "error": f"Erro no insert em massa: {str(e)}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================= FUNÇÕES AUXILIARES =========================

def buscar_responsavel_por_nome(nome: str) -> Dict:
    """Busca responsável por nome exato"""
    try:
        response = (supabase.table("responsaveis")
                   .select("*")
                   .eq("nome", nome)
                   .execute())
        
        return {
            "success": True,
            "encontrado": len(response.data) > 0,
            "data": response.data[0] if response.data else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_aluno_por_nome(nome: str) -> Dict:
    """Busca aluno por nome (busca parcial) e inclui responsáveis vinculados"""
    try:
        response = (supabase.table("alunos")
                   .select("*, turmas(nome_turma)")
                   .ilike("nome", f"%{nome}%")
                   .execute())
        
        # Para cada aluno encontrado, busca os responsáveis vinculados
        alunos_com_responsaveis = []
        for aluno in response.data:
            id_aluno = aluno.get("id")
            
            # Busca responsáveis vinculados
            responsaveis_result = verificar_responsaveis_financeiros(id_aluno)
            responsaveis_vinculados = []
            
            if responsaveis_result.get("success"):
                responsaveis_vinculados = responsaveis_result.get("responsaveis_vinculados", [])
            
            # Adiciona informações dos responsáveis ao aluno
            aluno_completo = aluno.copy()
            aluno_completo["responsaveis_vinculados"] = responsaveis_vinculados
            aluno_completo["total_responsaveis"] = len(responsaveis_vinculados)
            
            alunos_com_responsaveis.append(aluno_completo)
        
        return {
            "success": True,
            "data": alunos_com_responsaveis,
            "count": len(alunos_com_responsaveis)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def listar_turmas() -> Dict:
    """Lista todas as turmas disponíveis"""
    try:
        response = supabase.table("turmas").select("*").execute()
        
        return {
            "success": True,
            "data": response.data,
            "count": len(response.data)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def remover_aluno(id_aluno: str, remover_responsaveis_vinculados: bool = False) -> Dict:
    """Remove um aluno e opcionalmente seus responsáveis vinculados"""
    try:
        responsaveis_removidos = []
        
        # Se solicitado, busca e remove responsáveis vinculados
        if remover_responsaveis_vinculados:
            # Busca relacionamentos aluno-responsável
            relacoes_response = (supabase.table("alunos_responsaveis")
                               .select("id_responsavel")
                               .eq("id_aluno", id_aluno)
                               .execute())
            
            for relacao in relacoes_response.data:
                id_responsavel = relacao["id_responsavel"]
                
                # Remove o responsável
                try:
                    remove_resp_response = (supabase.table("responsaveis")
                                          .delete()
                                          .eq("id", id_responsavel)
                                          .execute())
                    responsaveis_removidos.append(id_responsavel)
                except Exception as e:
                    print(f"⚠️ Erro ao remover responsável {id_responsavel}: {str(e)}")
        
        # Remove relacionamentos aluno-responsável
        try:
            relacoes_delete_response = (supabase.table("alunos_responsaveis")
                                      .delete()
                                      .eq("id_aluno", id_aluno)
                                      .execute())
        except Exception as e:
            print(f"⚠️ Erro ao remover relacionamentos: {str(e)}")
        
        # Remove mensalidades do aluno
        try:
            mensalidades_delete_response = (supabase.table("mensalidades")
                                          .delete()
                                          .eq("id_aluno", id_aluno)
                                          .execute())
        except Exception as e:
            print(f"⚠️ Erro ao remover mensalidades: {str(e)}")
        
        # Remove pagamentos do aluno
        try:
            pagamentos_delete_response = (supabase.table("pagamentos")
                                        .delete()
                                        .eq("id_aluno", id_aluno)
                                        .execute())
        except Exception as e:
            print(f"⚠️ Erro ao remover pagamentos: {str(e)}")
        
        # Remove o aluno
        aluno_delete_response = (supabase.table("alunos")
                               .delete()
                               .eq("id", id_aluno)
                               .execute())
        
        return {
            "success": True,
            "id_aluno_removido": id_aluno,
            "responsaveis_removidos": responsaveis_removidos,
            "total_responsaveis_removidos": len(responsaveis_removidos),
            "message": f"Aluno {id_aluno} removido com sucesso"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================= EXEMPLO DE USO =========================

if __name__ == "__main__":
    # Exemplo de como usar as funções
    print("=== Identificando responsáveis não cadastrados ===")
    resultado = identificar_responsaveis_nao_cadastrados()
    if resultado["success"]:
        print(f"Encontrados {resultado['count']} responsáveis não cadastrados:")
        for nome in resultado["nomes_nao_cadastrados"]:
            print(f"- {nome}")
    else:
        print(f"Erro: {resultado['error']}")
    
    print("\n=== Processando responsáveis do extrato ===")
    resultado_processamento = processar_responsaveis_extrato_pix()
    if resultado_processamento["success"]:
        print(f"Cadastrados {resultado_processamento['total_cadastrados']} responsáveis")
        for resp in resultado_processamento["responsaveis_cadastrados"]:
            print(f"- {resp['nome']} (ID: {resp['id_responsavel']})")
    else:
        print(f"Erro: {resultado_processamento['error']}")

    print("\n=== Sistema de Gestão Escolar - Supabase ===")
    print("Funções implementadas:")
    print("1. identificar_responsaveis_nao_cadastrados()")
    print("2. cadastrar_responsavel_completo()")
    print("3. processar_responsaveis_extrato_pix()")
    print("4. listar_alunos(), listar_responsaveis(), listar_pagamentos()")
    print("5. cadastrar_aluno()")
    print("6. registrar_pagamento()")
    print("7. atualizar_dados_aluno(), atualizar_dados_responsavel()")
    print("8. verificar_responsaveis_financeiros()")
    print("9. vincular_aluno_responsavel()")
    print("10. analisar_estatisticas_extrato()")
    print("\nPara usar, importe as funções e chame conforme necessário.") 