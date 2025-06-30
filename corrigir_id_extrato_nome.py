#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 SCRIPT DE CORREÇÃO: ID_EXTRATO POR NOME
==========================================

Script para corrigir a coluna id_extrato vazia na tabela pagamentos,
usando correspondência por NOME + VALOR + DATA.
"""

import os
import sys
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

def limpar_nome(nome: str) -> str:
    """Limpa e normaliza nome para comparação"""
    if not nome:
        return ""
    return nome.lower().strip().replace("  ", " ")

def calcular_similaridade_nome(nome1: str, nome2: str) -> float:
    """Calcula similaridade entre nomes (0.0 a 1.0)"""
    nome1_limpo = limpar_nome(nome1)
    nome2_limpo = limpar_nome(nome2)
    
    if not nome1_limpo or not nome2_limpo:
        return 0.0
        
    return difflib.SequenceMatcher(None, nome1_limpo, nome2_limpo).ratio()

def valores_similares(valor1: float, valor2: float, tolerancia: float = 0.01) -> bool:
    """Verifica se dois valores são similares com tolerância"""
    return abs(float(valor1) - float(valor2)) <= tolerancia

def buscar_correspondencia_por_nome(pagamento: Dict, registros_extrato: List[Dict]) -> Optional[Dict]:
    """Busca correspondência usando nome + valor + data"""
    
    melhor_match = None
    melhor_score = 0.0
    
    for registro in registros_extrato:
        # 1. Verificar data (obrigatório)
        if pagamento["data_pagamento"] != registro["data_pagamento"]:
            continue
            
        # 2. Verificar valor (com tolerância)
        if not valores_similares(pagamento["valor"], registro["valor"]):
            continue
            
        # 3. Calcular similaridade do nome
        nome_responsavel = pagamento.get("nome_responsavel", "")
        nome_remetente = registro.get("nome_remetente", "")
        
        if nome_responsavel and nome_remetente:
            similaridade_nome = calcular_similaridade_nome(nome_responsavel, nome_remetente)
            
            # Só considerar se similaridade for alta (>= 70%)
            if similaridade_nome >= 0.7:
                if similaridade_nome > melhor_score:
                    melhor_score = similaridade_nome
                    melhor_match = registro
    
    return melhor_match if melhor_score >= 0.7 else None

def main():
    """Função principal"""
    print("🔧 SCRIPT DE CORREÇÃO: ID_EXTRATO POR NOME")
    print("="*80)
    
    # Perguntar modo
    modo = input("Executar em modo TESTE (sem alterações) ou PRODUÇÃO? [T/P]: ").strip().upper()
    modo_teste = modo != 'P'
    
    print("="*80)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ℹ️  🚀 INICIANDO CORREÇÃO")
    if modo_teste:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ℹ️  🧪 MODO TESTE")
    print("="*80)
    
    # Buscar pagamentos sem id_extrato com nome do responsável
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ℹ️  Buscando pagamentos...")
    
    response_pagamentos = supabase.table("pagamentos").select("""
        id_pagamento, id_responsavel, valor, data_pagamento, origem_extrato, 
        id_extrato, responsaveis!inner(nome)
    """).eq("origem_extrato", True).is_("id_extrato", "null").execute()
    
    if not response_pagamentos.data:
        print("Nenhum pagamento encontrado para correção!")
        return
    
    # Preparar dados dos pagamentos
    pagamentos = []
    for pag in response_pagamentos.data:
        pag_copy = pag.copy()
        if "responsaveis" in pag and pag["responsaveis"]:
            pag_copy["nome_responsavel"] = pag["responsaveis"]["nome"]
        else:
            pag_copy["nome_responsavel"] = ""
        pagamentos.append(pag_copy)
    
    print(f"Encontrados {len(pagamentos)} pagamentos sem id_extrato")
    
    # Buscar registros do extrato
    response_extrato = supabase.table("extrato_pix").select("*").execute()
    registros_extrato = response_extrato.data
    
    print(f"Carregados {len(registros_extrato)} registros do extrato PIX")
    
    # Processar correspondências
    correspondencias_encontradas = []
    sem_correspondencia = []
    
    for i, pagamento in enumerate(pagamentos, 1):
        print(f"\n📄 Processando {i}/{len(pagamentos)}: {pagamento['id_pagamento']}")
        print(f"   Responsável: {pagamento.get('nome_responsavel', 'N/A')}")
        print(f"   Valor: R$ {pagamento['valor']:.2f}")
        print(f"   Data: {pagamento['data_pagamento']}")
        
        correspondencia = buscar_correspondencia_por_nome(pagamento, registros_extrato)
        
        if correspondencia:
            print(f"   ✅ ENCONTRADA: {correspondencia['id']}")
            print(f"      Remetente: {correspondencia.get('nome_remetente', 'N/A')}")
            print(f"      Similaridade: {calcular_similaridade_nome(pagamento.get('nome_responsavel', ''), correspondencia.get('nome_remetente', '')):.2%}")
            
            correspondencias_encontradas.append({
                "pagamento_id": pagamento["id_pagamento"],
                "extrato_id": correspondencia["id"],
                "nome_responsavel": pagamento.get("nome_responsavel", ""),
                "nome_remetente": correspondencia.get("nome_remetente", ""),
                "valor": pagamento["valor"],
                "data": pagamento["data_pagamento"],
                "similaridade": calcular_similaridade_nome(pagamento.get('nome_responsavel', ''), correspondencia.get('nome_remetente', ''))
            })
            
            # Aplicar correção se não for modo teste
            if not modo_teste:
                try:
                    supabase.table("pagamentos").update({
                        "id_extrato": correspondencia["id"]
                    }).eq("id_pagamento", pagamento["id_pagamento"]).execute()
                    print(f"      ✅ ATUALIZADO no banco!")
                except Exception as e:
                    print(f"      ❌ Erro ao atualizar: {e}")
        else:
            print(f"   ❌ Nenhuma correspondência encontrada")
            sem_correspondencia.append(pagamento["id_pagamento"])
    
    # Relatório final
    print("\n" + "="*80)
    print("📊 RELATÓRIO FINAL")
    print("="*80)
    print(f"Total processados: {len(pagamentos)}")
    print(f"Correspondências encontradas: {len(correspondencias_encontradas)}")
    print(f"Sem correspondência: {len(sem_correspondencia)}")
    
    if modo_teste:
        print("\n🧪 MODO TESTE - Nenhuma alteração foi feita no banco")
    
    if correspondencias_encontradas:
        print(f"\n✅ CORRESPONDÊNCIAS ENCONTRADAS:")
        for corresp in correspondencias_encontradas:
            print(f"   {corresp['pagamento_id']} -> {corresp['extrato_id']} ({corresp['similaridade']:.1%})")
    
    if sem_correspondencia:
        print(f"\n❌ SEM CORRESPONDÊNCIA:")
        for pag_id in sem_correspondencia:
            print(f"   {pag_id}")
    
    print("\n✅ Script finalizado!")

if __name__ == "__main__":
    main() 