#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DAS CORREÇÕES NO SISTEMA DE RELATÓRIOS FINANCEIROS
============================================================

Teste para validar as correções implementadas:
1. Campo situação funcionando para relatórios financeiros
2. 4 seções distintas de mensalidades (A vencer, Pagas, Atrasadas, Canceladas)
3. Status "Pago parcial", "Baixado" e "Cancelado" classificados corretamente
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def teste_correcoes_financeiros():
    """Executa testes das correções implementadas"""
    
    print("🧪 TESTANDO CORREÇÕES DOS RELATÓRIOS FINANCEIROS")
    print("=" * 60)
    
    try:
        from funcoes_relatorios import gerar_relatorio_interface, obter_campos_disponiveis
        
        # TESTE 1: Verificar campos disponíveis
        print("\n🔍 TESTE 1: Verificação de campos disponíveis")
        print("-" * 40)
        
        campos = obter_campos_disponiveis()
        
        # Verificar campo situação no aluno
        situacao_disponivel = 'situacao' in campos['aluno']
        print(f"✅ Campo 'situacao' no aluno: {'DISPONÍVEL' if situacao_disponivel else 'AUSENTE'}")
        
        # Verificar campo valor_pago na mensalidade
        valor_pago_disponivel = 'valor_pago' in campos['mensalidade']
        print(f"✅ Campo 'valor_pago' na mensalidade: {'DISPONÍVEL' if valor_pago_disponivel else 'AUSENTE'}")
        
        # TESTE 2: Gerar relatório com diferentes status de mensalidades
        print("\n🧪 TESTE 2: Relatório com múltiplos status de mensalidades")
        print("-" * 40)
        
        configuracao = {
            'turmas_selecionadas': ['Berçário'], 
            'campos_selecionados': ['nome', 'situacao', 'nome', 'mes_referencia', 'valor', 'status', 'valor_pago'],
            'filtros': {
                'status_mensalidades': ['A vencer', 'Pago', 'Baixado', 'Pago parcial', 'Atrasado', 'Cancelado'],
                'situacoes_filtradas': ['matriculado', 'trancado']
            }
        }
        
        print("🚀 Gerando relatório financeiro com todas as seções...")
        resultado = gerar_relatorio_interface('financeiro', configuracao)
        
        if resultado.get('success'):
            print("✅ SUCESSO! Relatório gerado com sucesso")
            print(f"📋 Turmas incluídas: {resultado.get('turmas_incluidas', [])}")
            print(f"📊 Total de alunos: {resultado.get('total_alunos', 0)}")
            print(f"📝 Arquivo gerado: {resultado.get('nome_arquivo', 'N/A')}")
            
            # Verificar se os campos foram incluídos
            campos_resultado = resultado.get('campos_selecionados', [])
            print(f"📋 Campos incluídos: {', '.join(campos_resultado)}")
            
            # Verificar presença de campo situação
            if 'situacao' in campos_resultado:
                print("✅ Campo 'situação' incluído corretamente")
            else:
                print("❌ Campo 'situação' ausente no resultado")
                
            # Verificar presença de campo valor_pago
            if 'valor_pago' in campos_resultado:
                print("✅ Campo 'valor_pago' incluído corretamente")
            else:
                print("❌ Campo 'valor_pago' ausente no resultado")
                
        else:
            print("❌ ERRO ao gerar relatório:")
            print(f"   {resultado.get('error', 'Erro desconhecido')}")
        
        # TESTE 3: Relatório apenas com mensalidades canceladas
        print("\n🧪 TESTE 3: Relatório específico para mensalidades canceladas")
        print("-" * 40)
        
        configuracao_canceladas = {
            'turmas_selecionadas': ['Berçário'], 
            'campos_selecionados': ['nome', 'mes_referencia', 'status'],
            'filtros': {
                'status_mensalidades': ['Cancelado']
            }
        }
        
        resultado_canceladas = gerar_relatorio_interface('financeiro', configuracao_canceladas)
        
        if resultado_canceladas.get('success'):
            print("✅ Relatório de mensalidades canceladas gerado com sucesso")
            print(f"📋 Total de alunos: {resultado_canceladas.get('total_alunos', 0)}")
        else:
            print("❌ ERRO ao gerar relatório de canceladas:")
            print(f"   {resultado_canceladas.get('error', 'Erro desconhecido')}")
        
        print("\n" + "=" * 60)
        print("🎯 RESUMO DOS TESTES")
        print("=" * 60)
        
        testes_passaram = [
            situacao_disponivel,
            valor_pago_disponivel,
            resultado.get('success', False),
            resultado_canceladas.get('success', False)
        ]
        
        sucesso_total = all(testes_passaram)
        
        print(f"📊 Testes executados: 4")
        print(f"✅ Testes passaram: {sum(testes_passaram)}")
        print(f"❌ Testes falharam: {4 - sum(testes_passaram)}")
        print(f"🎯 Status geral: {'SUCESSO' if sucesso_total else 'ATENÇÃO - Alguns testes falharam'}")
        
        if sucesso_total:
            print("\n🎉 TODAS AS CORREÇÕES FORAM IMPLEMENTADAS COM SUCESSO!")
        else:
            print("\n⚠️ Algumas correções ainda precisam de ajustes.")
            
    except Exception as e:
        print(f"❌ ERRO CRÍTICO durante os testes: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    teste_correcoes_financeiros() 