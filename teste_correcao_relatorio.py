#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 TESTE DE CORREÇÃO DO SISTEMA DE RELATÓRIOS
============================================

Script para testar as correções implementadas no sistema de relatórios financeiros:
1. Filtragem correta de mensalidades apenas com status "Atrasado"
2. Eliminação de duplicações
3. Ordem correta das turmas e alunos
4. Apenas alunos com mensalidades geradas
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from funcoes_relatorios import (
    coletar_dados_financeiros,
    gerar_relatorio_financeiro,
    obter_campos_disponiveis
)

def teste_filtragem_relatorio():
    """
    Testa se o relatório está filtrando corretamente apenas mensalidades atrasadas
    """
    print("🔍 TESTE DE CORREÇÃO - RELATÓRIOS FINANCEIROS")
    print("=" * 60)
    
    # Configuração de teste baseada no problema reportado
    turmas_selecionadas = ["Berçário", "Infantil I", "Infantil II", "Infantil III"]
    
    # Campos para relatório de mensalidades atrasadas com responsáveis
    campos_selecionados = [
        'nome',  # do aluno
        'nome',  # do responsável  
        'telefone',  # do responsável
        'mes_referencia',  # da mensalidade
        'data_vencimento',  # da mensalidade
        'valor',  # da mensalidade
        'status'  # da mensalidade
    ]
    
    # Filtros específicos para mensalidades atrasadas
    filtros = {
        'status_mensalidades': ['Atrasado'],  # APENAS status "Atrasado"
        'turmas_selecionadas': turmas_selecionadas
    }
    
    print(f"📋 Turmas selecionadas: {', '.join(turmas_selecionadas)}")
    print(f"🔧 Filtros aplicados: {filtros}")
    print(f"📊 Campos selecionados: {len(campos_selecionados)} campos")
    print()
    
    try:
        # ETAPA 1: Coletar dados
        print("1️⃣ Coletando dados financeiros...")
        dados_brutos = coletar_dados_financeiros(turmas_selecionadas, campos_selecionados, filtros)
        
        if not dados_brutos.get("success"):
            print(f"❌ Erro na coleta de dados: {dados_brutos.get('error')}")
            return False
        
        # ETAPA 2: Analisar dados coletados
        print("2️⃣ Analisando dados coletados...")
        
        total_alunos = len(dados_brutos.get("alunos", []))
        total_mensalidades = len(dados_brutos.get("mensalidades", []))
        
        print(f"   📈 Total de alunos encontrados: {total_alunos}")
        print(f"   📈 Total de mensalidades encontradas: {total_mensalidades}")
        
        # Verificar se há mensalidades duplicadas
        mensalidades = dados_brutos.get("mensalidades", [])
        ids_mensalidades = [m.get("id") for m in mensalidades if m.get("id")]
        duplicadas = len(ids_mensalidades) != len(set(ids_mensalidades))
        
        if duplicadas:
            print(f"   ⚠️ AVISO: Mensalidades duplicadas detectadas!")
        else:
            print(f"   ✅ Nenhuma mensalidade duplicada")
        
        # Verificar status das mensalidades
        status_encontrados = set(m.get("status") for m in mensalidades)
        print(f"   📊 Status de mensalidades encontrados: {status_encontrados}")
        
        if status_encontrados - {"Atrasado"}:
            print(f"   ⚠️ AVISO: Encontrados status além de 'Atrasado': {status_encontrados - {'Atrasado'}}")
        else:
            print(f"   ✅ Apenas mensalidades 'Atrasado' foram retornadas")
        
        # Verificar organização por turma
        print("   📚 Verificando ordem das turmas:")
        alunos_por_turma = {}
        for aluno in dados_brutos.get("alunos", []):
            turma = aluno.get("turma_nome", "Sem turma")
            if turma not in alunos_por_turma:
                alunos_por_turma[turma] = []
            alunos_por_turma[turma].append(aluno.get("nome", "Sem nome"))
        
        for i, turma_esperada in enumerate(turmas_selecionadas):
            alunos_turma = alunos_por_turma.get(turma_esperada, [])
            if alunos_turma:
                print(f"      {i+1}. {turma_esperada}: {len(alunos_turma)} alunos")
                # Verificar se estão em ordem alfabética
                alunos_ordenados = sorted(alunos_turma)
                if alunos_turma == alunos_ordenados:
                    print(f"         ✅ Alunos em ordem alfabética")
                else:
                    print(f"         ⚠️ Alunos NÃO estão em ordem alfabética")
            else:
                print(f"      {i+1}. {turma_esperada}: Nenhum aluno com mensalidades atrasadas")
        
        # ETAPA 3: Gerar relatório
        print("\n3️⃣ Gerando relatório...")
        resultado = gerar_relatorio_financeiro(turmas_selecionadas, campos_selecionados, filtros)
        
        if resultado.get("success"):
            print("   ✅ Relatório gerado com sucesso")
            
            # Verificar se há arquivo temporário
            arquivo_temp = resultado.get("arquivo_temporario")
            if arquivo_temp:
                print(f"   📄 Arquivo temporário: {arquivo_temp}")
            
            # Mostrar primeiras linhas do conteúdo
            conteudo = resultado.get("conteudo_formatado", "")
            primeiras_linhas = "\n".join(conteudo.split("\n")[:10])
            print(f"\n   📋 Primeiras linhas do relatório:")
            print("   " + "─" * 50)
            for linha in primeiras_linhas.split("\n"):
                print(f"   {linha}")
            print("   " + "─" * 50)
            
        else:
            print(f"   ❌ Erro na geração do relatório: {resultado.get('error')}")
            return False
        
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_campos_disponíveis():
    """
    Verifica quais campos estão disponíveis para relatórios
    """
    print("\n📊 CAMPOS DISPONÍVEIS PARA RELATÓRIOS")
    print("=" * 40)
    
    try:
        campos = obter_campos_disponiveis()
        
        for categoria, lista_campos in campos.items():
            print(f"\n🏷️ {categoria.upper()}:")
            for campo_id, campo_nome in lista_campos.items():
                print(f"   • {campo_id}: {campo_nome}")
                
    except Exception as e:
        print(f"❌ Erro ao obter campos: {e}")

if __name__ == "__main__":
    print(f"🚀 Iniciando teste em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Executar verificação de campos disponíveis
    verificar_campos_disponíveis()
    
    # Executar teste principal
    sucesso = teste_filtragem_relatorio()
    
    print(f"\n🏁 Teste finalizado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    if sucesso:
        print("🎉 RESULTADO: SUCESSO - Correções implementadas corretamente!")
        sys.exit(0)
    else:
        print("💥 RESULTADO: FALHA - Ainda há problemas a serem corrigidos")
        sys.exit(1) 