#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 SCRIPT COMPLETO: CORREÇÃO DE REFERÊNCIAS
==========================================

1. Atualiza id_responsavel no extrato_pix para correspondências encontradas
2. Trata pagamentos múltiplos (soma valores por responsável + data)
3. Atualiza tanto id_extrato nos pagamentos quanto id_responsavel no extrato_pix

Autor: Sistema de Gestão Escolar
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client
from dotenv import load_dotenv
import difflib

# Carrega as variáveis do .env
load_dotenv()

# Configurações do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ ERRO: Variáveis SUPABASE_URL e SUPABASE_KEY devem estar configuradas no .env")
    exit(1)

supabase = create_client(url, key)

def calcular_similaridade(nome1: str, nome2: str) -> float:
    """Calcula similaridade entre dois nomes"""
    if not nome1 or not nome2:
        return 0.0
    
    nome1_limpo = nome1.lower().strip().replace("  ", " ")
    nome2_limpo = nome2.lower().strip().replace("  ", " ")
    
    return difflib.SequenceMatcher(None, nome1_limpo, nome2_limpo).ratio() * 100

def fase1_atualizar_extrato_com_correspondencias():
    """
    FASE 1: Atualiza id_responsavel no extrato_pix para correspondências já encontradas
    """
    print("\n" + "="*80)
    print("📋 FASE 1: ATUALIZANDO ID_RESPONSAVEL NO EXTRATO_PIX")
    print("="*80)
    
    # Buscar pagamentos que já têm id_extrato preenchido
    response_pagamentos = supabase.table("pagamentos").select("""
        id_pagamento, id_extrato, id_responsavel, valor, data_pagamento
    """).not_.is_("id_extrato", "null").eq("origem_extrato", True).execute()
    
    if not response_pagamentos.data:
        print("❌ Nenhum pagamento com id_extrato encontrado")
        return 0
    
    print(f"📊 Encontrados {len(response_pagamentos.data)} pagamentos com id_extrato")
    
    atualizados = 0
    
    for pagamento in response_pagamentos.data:
        id_extrato = pagamento["id_extrato"]
        id_responsavel = pagamento["id_responsavel"]
        
        print(f"📄 Verificando extrato {id_extrato}")
        
        # Verificar se o extrato já tem id_responsavel
        response_extrato = supabase.table("extrato_pix").select(
            "id, id_responsavel, nome_remetente"
        ).eq("id", id_extrato).execute()
        
        if not response_extrato.data:
            print(f"   ❌ Extrato {id_extrato} não encontrado")
            continue
        
        extrato = response_extrato.data[0]
        
        if extrato.get("id_responsavel"):
            print(f"   ✅ Extrato já tem id_responsavel")
            continue
        
        # Atualizar o extrato com id_responsavel
        try:
            supabase.table("extrato_pix").update({
                "id_responsavel": id_responsavel
            }).eq("id", id_extrato).execute()
            
            print(f"   ✅ ATUALIZADO: {extrato['nome_remetente']}")
            atualizados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao atualizar: {e}")
    
    print(f"\n📊 FASE 1 CONCLUÍDA: {atualizados} registros atualizados")
    return atualizados

def fase2_tratar_pagamentos_multiplos():
    """
    FASE 2: Trata pagamentos múltiplos agrupando por responsável + data
    """
    print("\n" + "="*80)
    print("📋 FASE 2: TRATANDO PAGAMENTOS MÚLTIPLOS")
    print("="*80)
    
    # Buscar pagamentos sem id_extrato
    response_pagamentos = supabase.table("pagamentos").select("""
        id_pagamento, id_responsavel, valor, data_pagamento,
        responsaveis!inner(nome)
    """).is_("id_extrato", "null").eq("origem_extrato", True).execute()
    
    if not response_pagamentos.data:
        print("✅ Nenhum pagamento sem id_extrato encontrado")
        return 0
    
    print(f"📊 Encontrados {len(response_pagamentos.data)} pagamentos sem id_extrato")
    
    # Agrupar por responsável + data
    grupos = {}
    for pagamento in response_pagamentos.data:
        chave = (pagamento["id_responsavel"], pagamento["data_pagamento"])
        
        if chave not in grupos:
            grupos[chave] = {
                "id_responsavel": pagamento["id_responsavel"],
                "nome_responsavel": pagamento["responsaveis"]["nome"],
                "data_pagamento": pagamento["data_pagamento"],
                "pagamentos": [],
                "valor_total": 0
            }
        
        grupos[chave]["pagamentos"].append(pagamento)
        grupos[chave]["valor_total"] += float(pagamento["valor"])
    
    print(f"📊 Agrupados em {len(grupos)} grupos (responsável + data)")
    
    correspondencias_encontradas = 0
    pagamentos_atualizados = 0
    
    for i, (chave, grupo) in enumerate(grupos.items(), 1):
        print(f"\n📄 Grupo {i}: {grupo['nome_responsavel']}")
        print(f"   📅 Data: {grupo['data_pagamento']}")
        print(f"   💰 Total: R$ {grupo['valor_total']:.2f}")
        print(f"   📋 {len(grupo['pagamentos'])} pagamentos")
        
        # Buscar no extrato_pix por valor total + data
        response_extrato = supabase.table("extrato_pix").select(
            "id, nome_remetente, valor, id_responsavel"
        ).eq("data_pagamento", grupo["data_pagamento"]).eq("valor", grupo["valor_total"]).execute()
        
        if not response_extrato.data:
            print(f"   ❌ Nenhum extrato com R$ {grupo['valor_total']:.2f}")
            continue
        
        # Escolher melhor por similaridade de nome
        melhor_extrato = None
        melhor_similaridade = 0
        
        for extrato in response_extrato.data:
            similaridade = calcular_similaridade(
                grupo['nome_responsavel'], 
                extrato['nome_remetente']
            )
            
            if similaridade > melhor_similaridade:
                melhor_similaridade = similaridade
                melhor_extrato = extrato
        
        if not melhor_extrato or melhor_similaridade < 80:
            print(f"   ❌ Similaridade baixa: {melhor_similaridade:.1f}%")
            continue
        
        print(f"   ✅ ENCONTRADO:")
        print(f"      ID: {melhor_extrato['id']}")
        print(f"      Similaridade: {melhor_similaridade:.1f}%")
        
        correspondencias_encontradas += 1
        
        # Atualizar pagamentos
        for pagamento in grupo["pagamentos"]:
            try:
                supabase.table("pagamentos").update({
                    "id_extrato": melhor_extrato["id"]
                }).eq("id_pagamento", pagamento["id_pagamento"]).execute()
                
                pagamentos_atualizados += 1
                
            except Exception as e:
                print(f"      ❌ Erro pagamento: {e}")
        
        # Atualizar extrato com id_responsavel
        if not melhor_extrato.get("id_responsavel"):
            try:
                supabase.table("extrato_pix").update({
                    "id_responsavel": grupo["id_responsavel"]
                }).eq("id", melhor_extrato["id"]).execute()
                
                print(f"      ✅ Extrato atualizado com id_responsavel")
                
            except Exception as e:
                print(f"      ❌ Erro extrato: {e}")
    
    print(f"\n📊 FASE 2 CONCLUÍDA:")
    print(f"   - {correspondencias_encontradas} correspondências")
    print(f"   - {pagamentos_atualizados} pagamentos atualizados")
    
    return correspondencias_encontradas

def verificar_resultados():
    """Verifica os resultados"""
    print("\n" + "="*80)
    print("📊 VERIFICAÇÃO DOS RESULTADOS")
    print("="*80)
    
    # Pagamentos
    sem_extrato = supabase.table("pagamentos").select("id_pagamento").is_("id_extrato", "null").eq("origem_extrato", True).execute()
    com_extrato = supabase.table("pagamentos").select("id_pagamento").not_.is_("id_extrato", "null").eq("origem_extrato", True).execute()
    
    # Extratos
    sem_responsavel = supabase.table("extrato_pix").select("id").is_("id_responsavel", "null").execute()
    com_responsavel = supabase.table("extrato_pix").select("id").not_.is_("id_responsavel", "null").execute()
    
    print(f"📋 PAGAMENTOS:")
    print(f"   ✅ Com id_extrato: {len(com_extrato.data)}")
    print(f"   ❌ Sem id_extrato: {len(sem_extrato.data)}")
    
    print(f"\n📋 EXTRATO PIX:")
    print(f"   ✅ Com id_responsavel: {len(com_responsavel.data)}")
    print(f"   ❌ Sem id_responsavel: {len(sem_responsavel.data)}")

def main():
    """Função principal"""
    print("🔧 SCRIPT COMPLETO: CORREÇÃO DE REFERÊNCIAS")
    print("="*80)
    
    verificar_resultados()
    
    atualizados_fase1 = fase1_atualizar_extrato_com_correspondencias()
    correspondencias_fase2 = fase2_tratar_pagamentos_multiplos()
    
    verificar_resultados()
    
    print("\n🎉 FINALIZADO!")
    print(f"Fase 1: {atualizados_fase1} atualizações")
    print(f"Fase 2: {correspondencias_fase2} correspondências")

if __name__ == "__main__":
    main() 