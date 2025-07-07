#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
💰 GESTÃO DE COBRANÇAS - Funcionalidades Independentes
======================================================

Módulo dedicado para gestão de cobranças adicionais:
- Formatura parcelada (6x)
- Eventos e taxas
- Dívidas anteriores
- Cobranças pontuais

Este módulo pode ser integrado ao sistema principal após os testes.
"""

from typing import Dict, List, Optional
from models.base import (
    supabase, gerar_id_cobranca, gerar_grupo_cobranca,
    obter_timestamp, formatar_data_br, formatar_valor_br,
    TIPOS_COBRANCA_DISPLAY, PRIORIDADES_COBRANCA
)

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
        try:
            from dateutil.relativedelta import relativedelta
        except ImportError:
            # Fallback se dateutil não estiver disponível
            def relativedelta(months=0):
                return timedelta(days=30 * months)
        
        data_base = datetime.strptime(data_primeira_parcela, "%Y-%m-%d").date()
        
        cobrancas_criadas = []
        ids_cobrancas = []
        
        for i in range(numero_parcelas):
            # Calcular data de vencimento (soma meses)
            if 'dateutil' in str(relativedelta):
                data_vencimento = data_base + relativedelta(months=i)
            else:
                data_vencimento = data_base + timedelta(days=30 * i)
            
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

def demonstrar_funcionalidades_cobrancas():
    """Demonstra as funcionalidades de cobranças implementadas"""
    
    print("💰 DEMONSTRAÇÃO - SISTEMA DE COBRANÇAS")
    print("=" * 60)
    
    print("\n📋 FUNCIONALIDADES IMPLEMENTADAS:")
    print("-" * 40)
    print("✅ Cadastro de cobrança individual")
    print("✅ Cadastro de cobrança parcelada (até 24x)")
    print("✅ Listagem de cobranças por aluno") 
    print("✅ Agrupamento de parcelas relacionadas")
    print("✅ Cálculo automático de status (Pendente/Vencido/Pago)")
    print("✅ Estatísticas financeiras")
    print("✅ Integração com sistema de pagamentos")
    
    print("\n🎯 TIPOS DE COBRANÇA SUPORTADOS:")
    print("-" * 35)
    for key, valor in TIPOS_COBRANCA_DISPLAY.items():
        print(f"{valor}")
    
    print("\n🔢 NÍVEIS DE PRIORIDADE:")
    print("-" * 25)
    for nivel, display in PRIORIDADES_COBRANCA.items():
        print(f"{display}")
    
    print("\n💡 EXEMPLOS DE USO:")
    print("-" * 20)
    print("📚 Formatura 2025: 6 parcelas de R$ 150,00")
    print("📝 Taxa de Material: R$ 280,00 (cobrança única)")
    print("⚠️ Dívida anterior: R$ 300,00 (alta prioridade)")
    print("🎉 Festa Junina: R$ 50,00 (evento)")
    
    print("\n" + "=" * 60)
    print("🚀 Sistema pronto para implementação!")
    print("📁 Criação da tabela: script_criacao_tabela_cobrancas.sql")
    print("⚙️ Funções Python: gestao_cobrancas.py")
    print("🔧 Integração: Adicionar ao models/pedagogico.py")
    print("🎨 Interface: Adicionar nova tab 'Cobranças' ao Streamlit")

if __name__ == "__main__":
    demonstrar_funcionalidades_cobrancas() 