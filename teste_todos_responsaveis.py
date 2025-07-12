#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
👥 TESTE ESPECÍFICO - TODOS OS RESPONSÁVEIS
==========================================

Este teste verifica se o relatório está incluindo TODOS os responsáveis 
de cada aluno, não apenas um.
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from funcoes_relatorios import (
    coletar_dados_financeiros,
    gerar_relatorio_financeiro
)
from models.pedagogico import supabase

def verificar_responsaveis_por_aluno():
    """
    Verifica quantos responsáveis cada aluno tem no banco de dados
    """
    print("🔍 VERIFICANDO RESPONSÁVEIS NO BANCO DE DADOS")
    print("=" * 50)
    
    try:
        # Buscar alguns alunos das turmas teste
        turmas_teste = ["Berçário", "Infantil I", "Infantil II", "Infantil III"]
        
        for turma in turmas_teste:
            print(f"\n📚 TURMA: {turma}")
            print("-" * 30)
            
            # Buscar alunos da turma
            alunos_response = supabase.table("alunos").select("""
                *, turmas!inner(nome_turma)
            """).eq("turmas.nome_turma", turma).limit(3).execute()
            
            for aluno in alunos_response.data:
                aluno_nome = aluno.get('nome', 'NOME AUSENTE')
                aluno_id = aluno.get('id')
                
                # Buscar todos os responsáveis deste aluno
                responsaveis_response = supabase.table("alunos_responsaveis").select("""
                    *, responsaveis!inner(*)
                """).eq("id_aluno", aluno_id).execute()
                
                print(f"👤 {aluno_nome}")
                print(f"   ID: {aluno_id}")
                print(f"   📞 Total de responsáveis: {len(responsaveis_response.data)}")
                
                for i, vinculo in enumerate(responsaveis_response.data, 1):
                    resp_data = vinculo["responsaveis"]
                    is_financeiro = vinculo.get("responsavel_financeiro", False)
                    emoji = "💰" if is_financeiro else "👤"
                    
                    print(f"      {emoji} Responsável {i}: {resp_data.get('nome', 'NOME AUSENTE')}")
                    print(f"         Financeiro: {'SIM' if is_financeiro else 'NÃO'}")
                    print(f"         Telefone: {resp_data.get('telefone', 'AUSENTE')}")
                    print(f"         Email: {resp_data.get('email', 'AUSENTE')}")
                
                print()
    
    except Exception as e:
        print(f"❌ Erro ao verificar responsáveis: {e}")
        return False
    
    return True

def testar_relatorio_todos_responsaveis():
    """
    Testa se o relatório está incluindo todos os responsáveis
    """
    print("\n🧪 TESTE DO RELATÓRIO - TODOS OS RESPONSÁVEIS")
    print("=" * 50)
    
    # Configuração do teste
    turmas_selecionadas = ["Berçário", "Infantil I"]  # Apenas 2 turmas para teste rápido
    
    # Campos incluindo TODOS os campos de responsável
    campos_selecionados = [
        'nome',  # do aluno
        'nome',  # do responsável  
        'telefone',  # do responsável
        'email',  # do responsável
        'cpf',  # do responsável
        'tipo_relacao',  # do responsável
        'responsavel_financeiro',  # do responsável
        'mes_referencia',  # da mensalidade
        'data_vencimento',  # da mensalidade
        'valor',  # da mensalidade
        'status'  # da mensalidade
    ]
    
    filtros = {
        'status_mensalidades': ['Atrasado'],
        'turmas_selecionadas': turmas_selecionadas
    }
    
    print(f"📋 Turmas: {', '.join(turmas_selecionadas)}")
    print(f"📊 Campos selecionados: {len(campos_selecionados)} campos")
    print(f"🔧 Filtros: {filtros}")
    print()
    
    try:
        # 1. Coletar dados
        print("1️⃣ Coletando dados...")
        dados_brutos = coletar_dados_financeiros(turmas_selecionadas, campos_selecionados, filtros)
        
        if not dados_brutos.get("success"):
            print(f"❌ Erro na coleta: {dados_brutos.get('error')}")
            return False
        
        print(f"   ✅ {len(dados_brutos.get('alunos', []))} alunos coletados")
        print(f"   ✅ {len(dados_brutos.get('mensalidades', []))} mensalidades coletadas")
        
        # 2. Verificar quantos responsáveis cada aluno tem nos dados coletados
        print("\n2️⃣ Verificando responsáveis nos dados coletados...")
        for aluno in dados_brutos.get('alunos', []):
            nome_aluno = aluno.get('nome', 'NOME AUSENTE')
            responsaveis = aluno.get('responsaveis', [])
            
            print(f"   👤 {nome_aluno}: {len(responsaveis)} responsáveis")
            
            for i, resp in enumerate(responsaveis, 1):
                is_financeiro = resp.get('responsavel_financeiro', False)
                emoji = "💰" if is_financeiro else "👤"
                print(f"      {emoji} {i}. {resp.get('nome', 'NOME AUSENTE')} (Financeiro: {'SIM' if is_financeiro else 'NÃO'})")
        
        # 3. Gerar relatório
        print("\n3️⃣ Gerando relatório...")
        resultado = gerar_relatorio_financeiro(turmas_selecionadas, campos_selecionados, filtros)
        
        if not resultado.get("success"):
            print(f"❌ Erro na geração: {resultado.get('error')}")
            return False
        
        # 4. Analisar o conteúdo do relatório
        print("4️⃣ Analisando conteúdo do relatório...")
        conteudo = resultado.get("conteudo_formatado", "")
        
        # Verificar se há múltiplos responsáveis no relatório
        if "💰" in conteudo and "👤" in conteudo:
            print("   ✅ Relatório contém responsáveis financeiros (💰) e outros (👤)")
        elif "💰" in conteudo:
            print("   ⚠️ Relatório contém apenas responsáveis financeiros (💰)")
        elif "👤" in conteudo:
            print("   ⚠️ Relatório contém apenas outros responsáveis (👤)")
        else:
            print("   ❌ Relatório não contém emojis de responsáveis")
        
        # Contar quantas vezes aparece "Responsável" no relatório
        count_responsaveis = conteudo.count("Responsável")
        print(f"   📊 Total de ocorrências de 'Responsável' no relatório: {count_responsaveis}")
        
        # Mostrar uma amostra do relatório
        print("\n5️⃣ Amostra do relatório gerado:")
        print("   " + "─" * 60)
        linhas = conteudo.split('\n')[:25]  # Primeiras 25 linhas
        for linha in linhas:
            print(f"   {linha}")
        print("   " + "─" * 60)
        
        # Verificar arquivo temporário
        arquivo_temp = resultado.get("arquivo_temporario")
        if arquivo_temp:
            print(f"\n📄 Arquivo temporário criado: {arquivo_temp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"🚀 Iniciando teste em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Primeiro verificar dados no banco
    sucesso_bd = verificar_responsaveis_por_aluno()
    
    if sucesso_bd:
        # Depois testar o relatório
        sucesso_relatorio = testar_relatorio_todos_responsaveis()
        
        print(f"\n🏁 Teste finalizado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if sucesso_relatorio:
            print("🎉 RESULTADO: SUCESSO - Todos os responsáveis estão sendo incluídos!")
            sys.exit(0)
        else:
            print("💥 RESULTADO: FALHA - Nem todos os responsáveis estão sendo incluídos")
            sys.exit(1)
    else:
        print("💥 FALHA - Erro ao verificar dados no banco de dados")
        sys.exit(1) 