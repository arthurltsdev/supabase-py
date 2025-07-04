#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 EXECUTOR DE TESTES COMPLETO - SISTEMA DE GESTÃO ESCOLAR
==========================================================

Script principal para executar todos os testes do sistema de forma
organizada, estratégica e com relatórios detalhados.

Executa testes por domínios:
1. 🔧 Base (estruturas e utilitários)
2. 🎓 Pedagógico (alunos, responsáveis, turmas)
3. 💰 Financeiro (pagamentos, mensalidades, extrato)
4. 🏢 Organizacional (validações, relatórios, manutenção)
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List

# Adicionar path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar configurações de teste
from tests import TEST_CONFIG, TEST_DATA

def print_header(titulo: str, simbolo: str = "="):
    """Imprime cabeçalho formatado"""
    linha = simbolo * 80
    print(f"\n{linha}")
    print(f"{titulo:^80}")
    print(linha)

def print_section(titulo: str):
    """Imprime seção formatada"""
    print(f"\n{'='*20} {titulo} {'='*20}")

def executar_teste_modelo(nome_modelo: str, funcao_teste) -> Dict:
    """
    Executa testes de um modelo específico
    
    Args:
        nome_modelo: Nome do modelo (ex: "Pedagógico")
        funcao_teste: Função que executa os testes
        
    Returns:
        Dict: Resultado dos testes
    """
    print_section(f"🧪 TESTANDO MODELO {nome_modelo.upper()}")
    
    inicio = time.time()
    
    try:
        # Executar testes
        sucesso = funcao_teste()
        
        fim = time.time()
        duracao = fim - inicio
        
        resultado = {
            "modelo": nome_modelo,
            "sucesso": sucesso,
            "duracao": duracao,
            "erro": None
        }
        
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"\n{status} - {nome_modelo} ({duracao:.2f}s)")
        
        return resultado
        
    except Exception as e:
        fim = time.time()
        duracao = fim - inicio
        
        resultado = {
            "modelo": nome_modelo,
            "sucesso": False,
            "duracao": duracao,
            "erro": str(e)
        }
        
        print(f"\n🚫 ERRO - {nome_modelo} ({duracao:.2f}s)")
        print(f"   Erro: {str(e)}")
        
        return resultado

def verificar_ambiente():
    """Verifica se o ambiente está pronto para os testes"""
    print_section("🔍 VERIFICAÇÃO DO AMBIENTE")
    
    verificacoes = []
    
    # Verificar conexão com banco
    try:
        from models.base import supabase
        response = supabase.table("turmas").select("id").limit(1).execute()
        verificacoes.append(("Conexão com banco", True, "OK"))
    except Exception as e:
        verificacoes.append(("Conexão com banco", False, str(e)))
    
    # Verificar estrutura de diretórios
    diretorios = ["models", "tests"]
    for diretorio in diretorios:
        existe = os.path.exists(diretorio)
        verificacoes.append((f"Diretório {diretorio}", existe, "OK" if existe else "Não encontrado"))
    
    # Verificar arquivos de modelo
    arquivos_modelo = ["models/base.py", "models/pedagogico.py", "models/financeiro.py", "models/organizacional.py"]
    for arquivo in arquivos_modelo:
        existe = os.path.exists(arquivo)
        verificacoes.append((f"Arquivo {arquivo}", existe, "OK" if existe else "Não encontrado"))
    
    # Imprimir resultados
    todos_ok = True
    for descricao, sucesso, detalhes in verificacoes:
        status = "✅" if sucesso else "❌"
        print(f"{status} {descricao}: {detalhes}")
        if not sucesso:
            todos_ok = False
    
    return todos_ok

def executar_testes_base():
    """Executa testes do modelo base"""
    try:
        # Importar e executar testes básicos
        from models.base import supabase, gerar_id_aluno, gerar_id_responsavel, formatar_valor_br
        
        print("🔧 Testando funções utilitárias...")
        
        # Teste 1: Geração de IDs
        id_aluno = gerar_id_aluno()
        id_responsavel = gerar_id_responsavel()
        
        assert id_aluno.startswith("ALU_"), f"ID aluno inválido: {id_aluno}"
        assert id_responsavel.startswith("RES_"), f"ID responsável inválido: {id_responsavel}"
        print("✅ Geração de IDs funcionando")
        
        # Teste 2: Formatação de valores
        valor_formatado = formatar_valor_br(1234.56)
        assert valor_formatado == "R$ 1.234,56", f"Formatação incorreta: {valor_formatado}"
        print("✅ Formatação de valores funcionando")
        
        # Teste 3: Conexão com banco
        response = supabase.table("turmas").select("id").limit(1).execute()
        assert response.data is not None, "Erro na conexão com banco"
        print("✅ Conexão com banco funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes base: {str(e)}")
        return False

def executar_testes_pedagogico():
    """Executa testes do modelo pedagógico"""
    try:
        from tests.test_pedagogico import run_pedagogico_tests
        return run_pedagogico_tests()
    except ImportError:
        print("⚠️ Testes pedagógicos não disponíveis - criando testes básicos...")
        return executar_testes_pedagogico_basico()

def executar_testes_pedagogico_basico():
    """Executa testes básicos do modelo pedagógico"""
    try:
        from models.pedagogico import listar_turmas_disponiveis, buscar_alunos_para_dropdown
        
        print("🎓 Testando funções pedagógicas básicas...")
        
        # Teste 1: Listar turmas
        resultado_turmas = listar_turmas_disponiveis()
        assert resultado_turmas["success"], f"Erro ao listar turmas: {resultado_turmas.get('error')}"
        print(f"✅ Turmas listadas: {resultado_turmas['count']} encontradas")
        
        # Teste 2: Buscar alunos
        resultado_alunos = buscar_alunos_para_dropdown()
        assert resultado_alunos["success"], f"Erro ao buscar alunos: {resultado_alunos.get('error')}"
        print(f"✅ Alunos encontrados: {resultado_alunos['count']} disponíveis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes pedagógicos: {str(e)}")
        return False

def executar_testes_financeiro():
    """Executa testes do modelo financeiro"""
    try:
        from models.financeiro import listar_extrato_com_sem_responsavel, obter_estatisticas_extrato
        
        print("💰 Testando funções financeiras básicas...")
        
        # Teste 1: Listar extrato
        resultado_extrato = listar_extrato_com_sem_responsavel()
        assert resultado_extrato["success"], f"Erro ao listar extrato: {resultado_extrato.get('error')}"
        print(f"✅ Extrato listado: {resultado_extrato['total_geral']} registros")
        
        # Teste 2: Estatísticas
        resultado_stats = obter_estatisticas_extrato()
        assert resultado_stats["success"], f"Erro ao obter estatísticas: {resultado_stats.get('error')}"
        print(f"✅ Estatísticas obtidas: {resultado_stats['estatisticas']['total_registros']} registros")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes financeiros: {str(e)}")
        return False

def executar_testes_organizacional():
    """Executa testes do modelo organizacional"""
    try:
        from models.organizacional import obter_configuracoes_sistema, calcular_similaridade_nomes
        
        print("🏢 Testando funções organizacionais básicas...")
        
        # Teste 1: Configurações do sistema
        resultado_config = obter_configuracoes_sistema()
        assert resultado_config["success"], f"Erro ao obter configurações: {resultado_config.get('error')}"
        print(f"✅ Configurações obtidas: {resultado_config['configuracoes']['sistema']['nome']}")
        
        # Teste 2: Similaridade de nomes
        similaridade = calcular_similaridade_nomes("João Silva", "Joao Silva")
        assert similaridade > 80, f"Similaridade muito baixa: {similaridade}"
        print(f"✅ Similaridade de nomes funcionando: {similaridade:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes organizacionais: {str(e)}")
        return False

def gerar_relatorio_final(resultados: List[Dict]):
    """Gera relatório final dos testes"""
    print_header("📊 RELATÓRIO FINAL DOS TESTES")
    
    total_modelos = len(resultados)
    sucessos = sum(1 for r in resultados if r["sucesso"])
    falhas = total_modelos - sucessos
    duracao_total = sum(r["duracao"] for r in resultados)
    
    print(f"🎯 RESUMO GERAL:")
    print(f"   • Total de modelos testados: {total_modelos}")
    print(f"   • ✅ Sucessos: {sucessos}")
    print(f"   • ❌ Falhas: {falhas}")
    print(f"   • ⏱️ Tempo total: {duracao_total:.2f}s")
    print(f"   • 📈 Taxa de sucesso: {(sucessos/total_modelos*100):.1f}%")
    
    print(f"\n📋 DETALHES POR MODELO:")
    for resultado in resultados:
        status = "✅" if resultado["sucesso"] else "❌"
        print(f"   {status} {resultado['modelo']}: {resultado['duracao']:.2f}s")
        if resultado["erro"]:
            print(f"      Erro: {resultado['erro']}")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES:")
    if falhas == 0:
        print("   🎉 Todos os testes passaram! Sistema está funcionando corretamente.")
    else:
        print(f"   ⚠️ {falhas} modelo(s) falharam. Verifique os erros acima.")
        print("   🔧 Execute os testes individuais para mais detalhes.")
    
    return sucessos == total_modelos

def main():
    """Função principal"""
    print_header("🧪 SISTEMA DE TESTES COMPLETO - GESTÃO ESCOLAR")
    
    print(f"📅 Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔧 Configurações: {TEST_CONFIG}")
    
    # 1. Verificar ambiente
    if not verificar_ambiente():
        print("\n❌ Ambiente não está pronto para os testes!")
        return False
    
    print("\n✅ Ambiente verificado com sucesso!")
    
    # 2. Executar testes por modelo
    resultados = []
    
    # Ordem estratégica dos testes
    testes_modelo = [
        ("Base", executar_testes_base),
        ("Pedagógico", executar_testes_pedagogico),
        ("Financeiro", executar_testes_financeiro),
        ("Organizacional", executar_testes_organizacional)
    ]
    
    for nome_modelo, funcao_teste in testes_modelo:
        resultado = executar_teste_modelo(nome_modelo, funcao_teste)
        resultados.append(resultado)
        
        # Parar se teste crítico falhar
        if nome_modelo == "Base" and not resultado["sucesso"]:
            print("\n🚫 Teste base falhou - interrompendo execução")
            break
    
    # 3. Gerar relatório final
    sucesso_geral = gerar_relatorio_final(resultados)
    
    print_header("🏁 TESTES CONCLUÍDOS")
    print(f"📅 Finalizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    return sucesso_geral

if __name__ == "__main__":
    try:
        sucesso = main()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n🚫 Erro crítico: {str(e)}")
        sys.exit(1) 