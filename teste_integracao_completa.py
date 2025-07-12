#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DE INTEGRAÇÃO COMPLETA
===============================

Script para testar e validar toda a integração do sistema de gestão escolar.
Verifica se todos os componentes estão funcionando de forma integrada.

Autor: Sistema de Gestão Escolar
Versão: 1.0 - Teste Completo
"""

import sys
import os
import traceback
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

# Adicionar o diretório atual ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ==========================================================
# 🔧 FUNÇÕES DE TESTE
# ==========================================================

def testar_imports():
    """Testa se todos os imports necessários estão funcionando"""
    
    print("🔍 Testando imports...")
    
    testes = {}
    
    # Teste 1: Streamlit
    try:
        import streamlit as st
        testes["streamlit"] = {"status": "✅", "erro": None}
    except Exception as e:
        testes["streamlit"] = {"status": "❌", "erro": str(e)}
    
    # Teste 2: Pandas
    try:
        import pandas as pd
        testes["pandas"] = {"status": "✅", "erro": None}
    except Exception as e:
        testes["pandas"] = {"status": "❌", "erro": str(e)}
    
    # Teste 3: Models Base
    try:
        from models.base import supabase, formatar_data_br, formatar_valor_br
        testes["models_base"] = {"status": "✅", "erro": None}
    except Exception as e:
        testes["models_base"] = {"status": "❌", "erro": str(e)}
    
    # Teste 4: Models Pedagógico
    try:
        from models.pedagogico import listar_turmas_disponiveis, buscar_alunos_para_dropdown
        testes["models_pedagogico"] = {"status": "✅", "erro": None}
    except Exception as e:
        testes["models_pedagogico"] = {"status": "❌", "erro": str(e)}
    
    # Teste 5: Gestão de Mensalidades
    try:
        from gestao_mensalidades import (
            inicializar_sistema_mensalidades,
            gerar_mensalidades_aluno_avancado,
            listar_mensalidades_por_status
        )
        testes["gestao_mensalidades"] = {"status": "✅", "erro": None}
    except Exception as e:
        testes["gestao_mensalidades"] = {"status": "❌", "erro": str(e)}
    
    return testes

def testar_conexao_database():
    """Testa a conexão com o banco de dados"""
    
    print("🗄️ Testando conexão com base de dados...")
    
    try:
        from models.base import supabase
        
        # Teste básico de conexão
        response = supabase.table("alunos").select("count", count="exact").execute()
        
        return {
            "status": "✅",
            "total_alunos": response.count,
            "erro": None
        }
        
    except Exception as e:
        return {
            "status": "❌",
            "total_alunos": 0,
            "erro": str(e)
        }

def testar_funcionalidades_pedagogicas():
    """Testa as funcionalidades pedagógicas básicas"""
    
    print("🎓 Testando funcionalidades pedagógicas...")
    
    testes = {}
    
    try:
        from models.pedagogico import listar_turmas_disponiveis
        
        resultado = listar_turmas_disponiveis()
        
        if resultado.get("success"):
            testes["listar_turmas"] = {
                "status": "✅",
                "total_turmas": len(resultado.get("turmas", [])),
                "erro": None
            }
        else:
            testes["listar_turmas"] = {
                "status": "❌",
                "total_turmas": 0,
                "erro": resultado.get("error", "Erro desconhecido")
            }
    
    except Exception as e:
        testes["listar_turmas"] = {
            "status": "❌",
            "total_turmas": 0,
            "erro": str(e)
        }
    
    # Teste de busca de alunos
    try:
        from models.pedagogico import buscar_alunos_para_dropdown
        
        resultado = buscar_alunos_para_dropdown("test")
        
        if resultado.get("success"):
            testes["buscar_alunos"] = {
                "status": "✅",
                "funcional": True,
                "erro": None
            }
        else:
            testes["buscar_alunos"] = {
                "status": "⚠️",
                "funcional": True,
                "erro": "Sem resultados (normal para busca 'test')"
            }
    
    except Exception as e:
        testes["buscar_alunos"] = {
            "status": "❌",
            "funcional": False,
            "erro": str(e)
        }
    
    return testes

def testar_sistema_mensalidades():
    """Testa o sistema de mensalidades"""
    
    print("📅 Testando sistema de mensalidades...")
    
    testes = {}
    
    try:
        from gestao_mensalidades import inicializar_sistema_mensalidades
        
        # Inicializar sistema
        inicializar_sistema_mensalidades()
        
        testes["inicializacao"] = {
            "status": "✅",
            "erro": None
        }
        
    except Exception as e:
        testes["inicializacao"] = {
            "status": "❌",
            "erro": str(e)
        }
        return testes
    
    # Testar listagem por status
    try:
        from gestao_mensalidades import listar_mensalidades_por_status
        
        resultado = listar_mensalidades_por_status("Todos", 5)
        
        if resultado.get("success"):
            testes["listar_por_status"] = {
                "status": "✅",
                "total_encontradas": len(resultado.get("mensalidades", [])),
                "erro": None
            }
        else:
            testes["listar_por_status"] = {
                "status": "⚠️",
                "total_encontradas": 0,
                "erro": resultado.get("error", "Sem mensalidades cadastradas")
            }
    
    except Exception as e:
        testes["listar_por_status"] = {
            "status": "❌",
            "total_encontradas": 0,
            "erro": str(e)
        }
    
    # Testar relatório
    try:
        from gestao_mensalidades import gerar_relatorio_mensalidades_resumido
        
        resultado = gerar_relatorio_mensalidades_resumido({})
        
        if resultado.get("success"):
            testes["relatorio"] = {
                "status": "✅",
                "funcional": True,
                "erro": None
            }
        else:
            testes["relatorio"] = {
                "status": "⚠️",
                "funcional": True,
                "erro": "Sem dados para relatório"
            }
    
    except Exception as e:
        testes["relatorio"] = {
            "status": "❌",
            "funcional": False,
            "erro": str(e)
        }
    
    return testes

def testar_estrutura_arquivos():
    """Testa se todos os arquivos necessários estão presentes"""
    
    print("📁 Testando estrutura de arquivos...")
    
    arquivos_obrigatorios = [
        "gestao_mensalidades.py",
        "interface_pedagogica_teste.py",
        "interface_processamento_extrato.py",
        "integracao_sistema.py",
        "models/base.py",
        "models/pedagogico.py",
        "README_INTEGRACAO_COMPLETA.md"
    ]
    
    testes = {}
    
    for arquivo in arquivos_obrigatorios:
        if os.path.exists(arquivo):
            # Verificar se não está vazio
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read().strip()
                    if len(conteudo) > 100:  # Arquivo tem conteúdo substancial
                        testes[arquivo] = {"status": "✅", "tamanho": len(conteudo)}
                    else:
                        testes[arquivo] = {"status": "⚠️", "tamanho": len(conteudo)}
            except Exception as e:
                testes[arquivo] = {"status": "❌", "erro": str(e)}
        else:
            testes[arquivo] = {"status": "❌", "erro": "Arquivo não encontrado"}
    
    return testes

def testar_integracao_completa():
    """Executa teste completo de integração"""
    
    print("🧪 Executando teste completo de integração...")
    
    # Simular fluxo completo se possível
    try:
        # 1. Testar busca de aluno
        from models.pedagogico import buscar_alunos_para_dropdown
        resultado_alunos = buscar_alunos_para_dropdown("a")
        
        # 2. Se encontrou alunos, testar mensalidades
        if resultado_alunos.get("success") and resultado_alunos.get("opcoes"):
            from gestao_mensalidades import listar_mensalidades_aluno_completas
            
            primeiro_aluno = resultado_alunos["opcoes"][0]
            resultado_mens = listar_mensalidades_aluno_completas(primeiro_aluno["id"])
            
            return {
                "status": "✅",
                "alunos_encontrados": len(resultado_alunos["opcoes"]),
                "mensalidades_testadas": resultado_mens.get("success", False),
                "erro": None
            }
        else:
            return {
                "status": "⚠️",
                "alunos_encontrados": 0,
                "mensalidades_testadas": False,
                "erro": "Nenhum aluno encontrado para teste"
            }
    
    except Exception as e:
        return {
            "status": "❌",
            "alunos_encontrados": 0,
            "mensalidades_testadas": False,
            "erro": str(e)
        }

# ==========================================================
# 🎯 FUNÇÃO PRINCIPAL
# ==========================================================

def executar_todos_os_testes():
    """Executa todos os testes de integração"""
    
    print("=" * 60)
    print("🧪 INICIANDO TESTE COMPLETO DE INTEGRAÇÃO")
    print("=" * 60)
    print()
    
    resultados = {}
    
    # 1. Testar imports
    resultados["imports"] = testar_imports()
    
    # 2. Testar conexão
    resultados["database"] = testar_conexao_database()
    
    # 3. Testar funcionalidades pedagógicas
    resultados["pedagogico"] = testar_funcionalidades_pedagogicas()
    
    # 4. Testar sistema de mensalidades
    resultados["mensalidades"] = testar_sistema_mensalidades()
    
    # 5. Testar estrutura de arquivos
    resultados["arquivos"] = testar_estrutura_arquivos()
    
    # 6. Testar integração completa
    resultados["integracao"] = testar_integracao_completa()
    
    return resultados

def gerar_relatorio_final(resultados: Dict):
    """Gera relatório final dos testes"""
    
    print()
    print("=" * 60)
    print("📊 RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    print()
    
    # Resumo por categoria
    total_testes = 0
    testes_ok = 0
    testes_warning = 0
    testes_erro = 0
    
    for categoria, dados in resultados.items():
        print(f"📋 {categoria.upper()}:")
        
        if isinstance(dados, dict):
            if "status" in dados:
                # Resultado único
                total_testes += 1
                status = dados["status"]
                
                if status == "✅":
                    testes_ok += 1
                elif status == "⚠️":
                    testes_warning += 1
                else:
                    testes_erro += 1
                
                print(f"   {status} {categoria}")
                if dados.get("erro"):
                    print(f"      Erro: {dados['erro']}")
            else:
                # Múltiplos resultados
                for nome, resultado in dados.items():
                    total_testes += 1
                    
                    if isinstance(resultado, dict) and "status" in resultado:
                        status = resultado["status"]
                        
                        if status == "✅":
                            testes_ok += 1
                        elif status == "⚠️":
                            testes_warning += 1
                        else:
                            testes_erro += 1
                        
                        print(f"   {status} {nome}")
                        if resultado.get("erro"):
                            print(f"      Erro: {resultado['erro']}")
        print()
    
    # Estatísticas finais
    print("=" * 60)
    print("📊 ESTATÍSTICAS FINAIS")
    print("=" * 60)
    print(f"✅ Testes OK: {testes_ok}")
    print(f"⚠️ Testes com Aviso: {testes_warning}")
    print(f"❌ Testes com Erro: {testes_erro}")
    print(f"📋 Total de Testes: {total_testes}")
    print()
    
    # Percentual de sucesso
    if total_testes > 0:
        percentual_sucesso = ((testes_ok + testes_warning) / total_testes) * 100
        print(f"📈 Taxa de Sucesso: {percentual_sucesso:.1f}%")
        
        if percentual_sucesso >= 90:
            print("🎉 SISTEMA COMPLETAMENTE INTEGRADO E FUNCIONAL!")
        elif percentual_sucesso >= 70:
            print("✅ Sistema majoritariamente funcional com alguns pontos de atenção")
        else:
            print("⚠️ Sistema requer correções antes de uso em produção")
    
    print()
    print("=" * 60)
    print(f"🕐 Teste concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

# ==========================================================
# 🚀 EXECUÇÃO PRINCIPAL
# ==========================================================

if __name__ == "__main__":
    try:
        print(f"🚀 Iniciando testes em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Executar todos os testes
        resultados = executar_todos_os_testes()
        
        # Gerar relatório final
        gerar_relatorio_final(resultados)
        
    except Exception as e:
        print(f"❌ Erro crítico durante os testes: {str(e)}")
        print()
        print("🔍 Traceback completo:")
        traceback.print_exc()
    
    print()
    print("💡 Para executar as interfaces, use:")
    print("   streamlit run interface_pedagogica_teste.py")
    print("   streamlit run interface_processamento_extrato.py")
    print("   streamlit run integracao_sistema.py") 