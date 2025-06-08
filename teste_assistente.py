#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste rápido do Assistente Escolar IA
=====================================

Este script testa as principais funcionalidades do assistente
sem precisar interagir manualmente.
"""

from executor_unificado import executar_function

def testar_funcionalidades_basicas():
    """Testa as funcionalidades básicas do sistema"""
    print("🧪 **TESTE DO ASSISTENTE ESCOLAR IA**")
    print("=" * 50)
    
    # Teste 1: Listar turmas
    print("\n📋 1. Testando listagem de turmas...")
    resultado = executar_function("listar_turmas")
    if resultado.get("success"):
        count = resultado.get("count", 0)
        print(f"✅ Encontradas {count} turmas")
    else:
        print(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
    
    # Teste 2: Analisar estatísticas do extrato
    print("\n📊 2. Testando análise de estatísticas...")
    resultado = executar_function("analisar_estatisticas_extrato")
    if resultado.get("success"):
        stats = resultado.get("estatisticas", {})
        total = stats.get("total_registros", 0)
        identificados = stats.get("total_identificados", 0)
        percentual = stats.get("percentual_identificacao", 0)
        print(f"✅ Total de registros: {total}")
        print(f"✅ Identificados: {identificados} ({percentual:.1f}%)")
    else:
        print(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
    
    # Teste 3: Identificar responsáveis não cadastrados
    print("\n🔍 3. Testando identificação de responsáveis não cadastrados...")
    resultado = executar_function("identificar_responsaveis_nao_cadastrados")
    if resultado.get("success"):
        count = resultado.get("count", 0)
        print(f"✅ Encontrados {count} responsáveis não cadastrados")
        if count > 0:
            detalhes = resultado.get("detalhes", [])
            print("📝 Primeiros 5:")
            for i, detalhe in enumerate(detalhes[:5], 1):
                nome = detalhe.get("nome", "N/A")
                qtd = detalhe.get("quantidade_pagamentos", 0)
                valor = detalhe.get("valor_total", 0)
                print(f"   {i}. {nome} - {qtd} pagamento(s), R$ {valor:.2f}")
    else:
        print(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
    
    # Teste 4: Listar alguns alunos
    print("\n👥 4. Testando listagem de alunos...")
    resultado = executar_function("listar_alunos", sem_data_matricula=True)
    if resultado.get("success"):
        count = resultado.get("count", 0)
        print(f"✅ Encontrados {count} alunos sem data de matrícula")
    else:
        print(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
    
    # Teste 5: Listar responsáveis
    print("\n👨‍👩‍👧‍👦 5. Testando listagem de responsáveis...")
    resultado = executar_function("listar_responsaveis")
    if resultado.get("success"):
        count = resultado.get("count", 0)
        print(f"✅ Encontrados {count} responsáveis cadastrados")
    else:
        print(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
    
    print("\n" + "=" * 50)
    print("🎯 **TESTE CONCLUÍDO!**")
    print("\n💡 **Como usar o assistente:**")
    print("   python assistente_escolar_ia.py")
    print("\n🤖 **Comandos de exemplo:**")
    print("   • 'identificar' - Lista responsáveis não cadastrados")
    print("   • 'estatisticas' - Analisa extrato PIX")
    print("   • 'menu' - Mostra todas as opções")

if __name__ == "__main__":
    try:
        testar_funcionalidades_basicas()
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        print("💡 Verifique se as configurações estão corretas no .env") 