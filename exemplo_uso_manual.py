#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemplo de Uso Manual - atualizar_responsaveis_extrato_por_nome
==============================================================

Este script mostra como usar a nova função manualmente.
ATENÇÃO: Agora SOBRESCREVE valores existentes para corrigir dados incorretos!
"""

from supabase_functions import atualizar_responsaveis_extrato_por_nome

print("🔄 Executando atualização de responsáveis no extrato PIX...")
print("   ⚠️  ATENÇÃO: Esta operação irá SOBRESCREVER valores existentes!")
resultado = atualizar_responsaveis_extrato_por_nome()

if resultado["success"]:
    print(f"✅ Sucesso! {resultado['resumo']}")
    print(f"📊 Detalhes:")
    print(f"   • Responsáveis verificados: {resultado['total_responsaveis']}")
    print(f"   • Correspondências encontradas: {resultado['correspondencias_encontradas']}")
    print(f"   • Total de registros atualizados: {resultado['registros_atualizados']}")
    
    # Mostra as correspondências encontradas
    if resultado.get("detalhes_correspondencias"):
        print(f"\n🎯 Correspondências processadas:")
        for corresp in resultado["detalhes_correspondencias"][:10]:  # Mostra só as primeiras 10
            print(f"   • {corresp['nome']} → {corresp['registros_atualizados']} registros atualizados")
        
        if len(resultado["detalhes_correspondencias"]) > 10:
            print(f"   ... e mais {len(resultado['detalhes_correspondencias']) - 10} correspondências")
    
    if resultado.get("erros"):
        print(f"   ⚠️  {len(resultado['erros'])} erros encontrados")
        for erro in resultado["erros"]:
            print(f"     - {erro}")
    else:
        print("   ✅ Nenhum erro encontrado")
else:
    print(f"❌ Erro: {resultado['error']}") 