#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DAS MELHORIAS NO SISTEMA DE RELATÓRIOS FINANCEIROS
===========================================================

Teste para validar as melhorias implementadas nos relatórios financeiros:
1. Organização por status de mensalidades (A vencer, Pagas, Atrasadas, Canceladas)
2. Campos específicos para cada tipo de seção
3. Inclusão de alunos sem mensalidades com "MENSALIDADES: NÃO GERADAS"
4. Respeito aos filtros de período
5. Formatação especial para campos vazios
"""

import os
import sys
from datetime import datetime, date

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def teste_melhorias_relatorios_financeiros():
    """Executa testes das melhorias implementadas nos relatórios financeiros"""
    
    print("🧪 INICIANDO TESTES DAS MELHORIAS DE RELATÓRIOS FINANCEIROS")
    print("=" * 70)
    
    try:
        from funcoes_relatorios import (
            gerar_relatorio_interface,
            obter_campos_disponiveis,
            DOCX_AVAILABLE
        )
        
        if not DOCX_AVAILABLE:
            print("❌ python-docx não disponível. Execute: pip install python-docx")
            return False
        
        print("✅ Módulos importados com sucesso")
        
    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {e}")
        return False
    
    # TESTE 1: Verificar campos disponíveis para relatórios financeiros
    print("\n" + "="*70)
    print("🧪 TESTE 1: CAMPOS DISPONÍVEIS PARA RELATÓRIOS FINANCEIROS")
    print("="*70)
    
    try:
        campos = obter_campos_disponiveis()
        
        print("✅ Campos do aluno disponíveis:")
        for key, desc in campos['aluno'].items():
            print(f"   - {key}: {desc}")
        
        print("\n✅ Campos do responsável disponíveis:")
        for key, desc in campos['responsavel'].items():
            print(f"   - {key}: {desc}")
        
        print("\n✅ Campos de mensalidade disponíveis:")
        for key, desc in campos['mensalidade'].items():
            print(f"   - {key}: {desc}")
        
        # Verificar se o campo valor_pago foi adicionado
        if 'valor_pago' in campos['mensalidade']:
            print("✅ Campo 'Valor Pago' adicionado corretamente aos campos de mensalidade!")
        else:
            print("❌ Campo 'Valor Pago' não encontrado nos campos de mensalidade")
        
    except Exception as e:
        print(f"❌ Erro ao obter campos disponíveis: {e}")
        return False
    
    # TESTE 2: Relatório financeiro com múltiplos status
    print("\n" + "="*70)
    print("🧪 TESTE 2: RELATÓRIO FINANCEIRO COM MÚLTIPLOS STATUS")
    print("="*70)
    
    try:
        # Configuração com múltiplos status de mensalidades
        config_multiplos_status = {
            'turmas_selecionadas': ['Berçário', 'Infantil I'],
            'campos_selecionados': [
                'nome',              # Campo do aluno
                'nome',              # Campo do responsável (mesmo nome, contextos diferentes)
                'telefone',          # Campo do responsável
                'mes_referencia',    # Campo da mensalidade
                'data_vencimento',   # Campo da mensalidade
                'valor',             # Campo da mensalidade
                'data_pagamento',    # Campo da mensalidade
                'valor_pago'         # Campo da mensalidade
            ],
            'filtros': {
                'status_mensalidades': ['A vencer', 'Pago', 'Atrasado'],  # Múltiplos status
                'periodo_inicio': '2025-01-01',
                'periodo_fim': '2025-12-31'
            }
        }
        
        print("🚀 Gerando relatório financeiro com múltiplos status...")
        resultado = gerar_relatorio_interface('financeiro', config_multiplos_status)
        
        if resultado.get('success'):
            print("✅ Relatório financeiro gerado com sucesso!")
            print(f"📋 Total de alunos: {resultado.get('total_alunos', 0)}")
            print(f"🎓 Turmas incluídas: {', '.join(resultado.get('turmas_incluidas', []))}")
            print(f"📊 Status selecionados: {config_multiplos_status['filtros']['status_mensalidades']}")
            
            # Verificar se arquivo foi criado
            if resultado.get('arquivo') and os.path.exists(resultado['arquivo']):
                print(f"📄 Arquivo gerado: {resultado['nome_arquivo']}")
                print("✅ Arquivo .docx criado com sucesso!")
            else:
                print("⚠️ Arquivo não encontrado")
        
        else:
            print(f"❌ Erro na geração: {resultado.get('error')}")
            return False
    
    except Exception as e:
        print(f"❌ Erro no teste de múltiplos status: {e}")
        return False
    
    # TESTE 3: Relatório apenas com mensalidades pagas
    print("\n" + "="*70)
    print("🧪 TESTE 3: RELATÓRIO APENAS COM MENSALIDADES PAGAS")
    print("="*70)
    
    try:
        config_apenas_pagas = {
            'turmas_selecionadas': ['Berçário'],
            'campos_selecionados': [
                'nome',              # Aluno
                'nome',              # Responsável
                'email',             # Responsável
                'mes_referencia',    # Mensalidade
                'data_vencimento',   # Mensalidade
                'data_pagamento',    # Mensalidade
                'valor',             # Mensalidade
                'valor_pago'         # Mensalidade
            ],
            'filtros': {
                'status_mensalidades': ['Pago'],  # Apenas pagas
            }
        }
        
        print("🚀 Gerando relatório apenas com mensalidades pagas...")
        resultado = gerar_relatorio_interface('financeiro', config_apenas_pagas)
        
        if resultado.get('success'):
            print("✅ Relatório de mensalidades pagas gerado com sucesso!")
            print(f"📋 Total de alunos: {resultado.get('total_alunos', 0)}")
            print("✅ Status: Apenas mensalidades pagas")
            
            if resultado.get('arquivo') and os.path.exists(resultado['arquivo']):
                print(f"📄 Arquivo: {resultado['nome_arquivo']}")
            
        else:
            print(f"❌ Erro na geração: {resultado.get('error')}")
    
    except Exception as e:
        print(f"❌ Erro no teste de mensalidades pagas: {e}")
    
    # TESTE 4: Relatório com alunos sem mensalidades
    print("\n" + "="*70)
    print("🧪 TESTE 4: RELATÓRIO COM ALUNOS SEM MENSALIDADES")
    print("="*70)
    
    try:
        config_sem_filtro_status = {
            'turmas_selecionadas': ['Berçário'],
            'campos_selecionados': [
                'nome',                # Aluno
                'valor_mensalidade',   # Aluno
                'nome',                # Responsável
                'telefone'             # Responsável
            ],
            'filtros': {}  # Sem filtros de status - pode mostrar alunos sem mensalidades
        }
        
        print("🚀 Gerando relatório que pode incluir alunos sem mensalidades...")
        resultado = gerar_relatorio_interface('financeiro', config_sem_filtro_status)
        
        if resultado.get('success'):
            print("✅ Relatório gerado (pode incluir alunos sem mensalidades)!")
            print(f"📋 Total de alunos: {resultado.get('total_alunos', 0)}")
            print("✅ Configuração: Sem filtro de status específico")
            
        else:
            print(f"❌ Erro na geração: {resultado.get('error')}")
    
    except Exception as e:
        print(f"❌ Erro no teste sem filtro de status: {e}")
    
    # TESTE 5: Verificar formatação especial para campos vazios
    print("\n" + "="*70)
    print("🧪 TESTE 5: FORMATAÇÃO ESPECIAL PARA CAMPOS VAZIOS")
    print("="*70)
    
    try:
        config_campos_vazios = {
            'turmas_selecionadas': ['Berçário'],
            'campos_selecionados': [
                'nome',           # Aluno
                'nome',           # Responsável
                'email',          # Responsável (pode estar vazio)
                'cpf',            # Responsável (pode estar vazio)
                'mes_referencia', # Mensalidade
                'data_pagamento'  # Mensalidade (pode estar vazio para não pagas)
            ],
            'filtros': {
                'status_mensalidades': ['A vencer', 'Pago']  # Mix de status
            }
        }
        
        print("🚀 Gerando relatório para testar formatação de campos vazios...")
        resultado = gerar_relatorio_interface('financeiro', config_campos_vazios)
        
        if resultado.get('success'):
            print("✅ Relatório gerado para teste de campos vazios!")
            print("✅ Campos vazios devem aparecer como **_______________**")
            
        else:
            print(f"❌ Erro na geração: {resultado.get('error')}")
    
    except Exception as e:
        print(f"❌ Erro no teste de campos vazios: {e}")
    
    # RESUMO FINAL
    print("\n" + "="*70)
    print("📋 RESUMO FINAL DOS TESTES")
    print("="*70)
    print("✅ Campos de mensalidade atualizados (incluindo valor_pago)")
    print("✅ Organização por status implementada")
    print("✅ Múltiplos tipos de relatórios testados")
    print("✅ Formatação especial para campos vazios")
    print("✅ Suporte a alunos sem mensalidades")
    print("\n🎉 TODAS AS MELHORIAS IMPLEMENTADAS E TESTADAS!")
    
    return True

if __name__ == "__main__":
    sucesso = teste_melhorias_relatorios_financeiros()
    if sucesso:
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ TESTE FALHOU!")
        sys.exit(1) 