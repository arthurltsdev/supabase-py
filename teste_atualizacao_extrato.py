#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste da Nova Função: atualizar_responsaveis_extrato_por_nome
===========================================================

Este script testa a nova função que vincula os registros do extrato_pix
aos responsáveis já cadastrados com base na correspondência de nomes.
"""

from supabase_functions import (
    atualizar_responsaveis_extrato_por_nome,
    analisar_estatisticas_extrato,
    listar_responsaveis
)

def testar_atualizacao_extrato():
    """Testa o processo completo de atualização do extrato PIX"""
    
    print("🧪 TESTE - Atualização de Responsáveis no Extrato PIX")
    print("=" * 60)
    
    # 1. Análise antes da atualização
    print("\n📊 1. Análise ANTES da atualização:")
    stats_antes = analisar_estatisticas_extrato()
    
    if stats_antes["success"]:
        stats = stats_antes["estatisticas"]
        print(f"   • Total de registros: {stats['total_registros']}")
        print(f"   • Registros identificados: {stats['total_identificados']}")
        print(f"   • Não identificados: {stats['total_nao_identificados']}")
        print(f"   • Taxa de identificação: {stats['percentual_identificacao']:.1f}%")
        print(f"   • Valor total: R$ {stats['valor_total']:,.2f}")
        print(f"   • Valor identificado: R$ {stats['valor_identificado']:,.2f}")
    else:
        print(f"   ❌ Erro: {stats_antes['error']}")
        return
    
    # 2. Mostrar responsáveis cadastrados
    print("\n👥 2. Responsáveis cadastrados:")
    responsaveis_info = listar_responsaveis()
    if responsaveis_info["success"]:
        print(f"   • Total: {responsaveis_info['count']} responsáveis")
        print("   • Primeiros 5 nomes:")
        for i, resp in enumerate(responsaveis_info["data"][:5], 1):
            print(f"     {i}. {resp['nome']}")
    else:
        print(f"   ❌ Erro: {responsaveis_info['error']}")
        return
    
    # 3. Executar a atualização
    print("\n🔄 3. Executando atualização...")
    resultado = atualizar_responsaveis_extrato_por_nome()
    
    if resultado["success"]:
        print(f"   ✅ {resultado['resumo']}")
        print(f"   • Total de responsáveis verificados: {resultado['total_responsaveis']}")
        print(f"   • Registros atualizados: {resultado['registros_atualizados']}")
        
        if resultado.get("erros"):
            print(f"   ⚠️  Erros encontrados: {len(resultado['erros'])}")
            for erro in resultado["erros"][:3]:  # Mostra só os 3 primeiros
                print(f"      - {erro}")
    else:
        print(f"   ❌ Erro: {resultado['error']}")
        return
    
    # 4. Análise depois da atualização
    print("\n📊 4. Análise DEPOIS da atualização:")
    stats_depois = analisar_estatisticas_extrato()
    
    if stats_depois["success"]:
        stats = stats_depois["estatisticas"]
        print(f"   • Total de registros: {stats['total_registros']}")
        print(f"   • Registros identificados: {stats['total_identificados']}")
        print(f"   • Não identificados: {stats['total_nao_identificados']}")
        print(f"   • Taxa de identificação: {stats['percentual_identificacao']:.1f}%")
        print(f"   • Valor total: R$ {stats['valor_total']:,.2f}")
        print(f"   • Valor identificado: R$ {stats['valor_identificado']:,.2f}")
        
        # Mostra a melhoria
        melhoria = stats['total_identificados'] - stats_antes['estatisticas']['total_identificados']
        print(f"\n🎯 5. Resultado da atualização:")
        print(f"   • Novos registros identificados: {melhoria}")
        
        valor_melhoria = stats['valor_identificado'] - stats_antes['estatisticas']['valor_identificado']
        print(f"   • Valor adicional identificado: R$ {valor_melhoria:,.2f}")
        
        if melhoria > 0:
            print("   ✅ Atualização bem-sucedida!")
        else:
            print("   ⚠️  Nenhum novo registro foi identificado")
    else:
        print(f"   ❌ Erro: {stats_depois['error']}")

if __name__ == "__main__":
    testar_atualizacao_extrato() 