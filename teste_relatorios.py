#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DE FUNCIONALIDADE DE RELATÓRIOS
========================================

Script para testar a geração de relatórios pedagógicos e financeiros
"""

import os
from datetime import datetime

def testar_importacoes():
    """Testa se todas as importações estão funcionando"""
    print("🔍 Testando importações...")
    
    try:
        from funcoes_relatorios import (
            gerar_relatorio_interface,
            obter_campos_disponiveis,
            limpar_arquivos_temporarios,
            DOCX_AVAILABLE,
            OPENAI_AVAILABLE
        )
        print("✅ Módulo funcoes_relatorios importado com sucesso")
        
        # Testar dependências
        if DOCX_AVAILABLE:
            print("✅ python-docx disponível")
        else:
            print("❌ python-docx não disponível")
        
        if OPENAI_AVAILABLE:
            print("✅ OpenAI disponível")
        else:
            print("⚠️ OpenAI não disponível")
        
        if os.getenv("OPENAI_API_KEY"):
            print("✅ OPENAI_API_KEY configurada")
        else:
            print("⚠️ OPENAI_API_KEY não configurada")
        
        return True
    
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False

def testar_campos_disponiveis():
    """Testa a função de obter campos disponíveis"""
    print("\n🔍 Testando campos disponíveis...")
    
    try:
        from funcoes_relatorios import obter_campos_disponiveis
        
        campos = obter_campos_disponiveis()
        
        print(f"✅ Campos disponíveis carregados:")
        for categoria, campos_categoria in campos.items():
            print(f"   📊 {categoria}: {len(campos_categoria)} campos")
            for campo, descricao in list(campos_categoria.items())[:3]:  # Mostrar apenas 3 primeiros
                print(f"      - {campo}: {descricao}")
            if len(campos_categoria) > 3:
                print(f"      ... e mais {len(campos_categoria) - 3} campos")
        
        return True
    
    except Exception as e:
        print(f"❌ Erro ao carregar campos: {e}")
        return False

def testar_conexao_banco():
    """Testa conexão com banco de dados"""
    print("\n🔍 Testando conexão com banco...")
    
    try:
        from models.pedagogico import listar_turmas_disponiveis
        
        resultado = listar_turmas_disponiveis()
        
        if resultado.get("success"):
            print(f"✅ Conexão com banco OK - {resultado['count']} turmas encontradas")
            print(f"   🎓 Turmas: {', '.join(resultado['turmas'][:5])}")
            if len(resultado['turmas']) > 5:
                print(f"      ... e mais {len(resultado['turmas']) - 5} turmas")
            return True
        else:
            print(f"❌ Erro na consulta: {resultado.get('error')}")
            return False
    
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def testar_geracao_relatorio_simples():
    """Testa geração de relatório simples"""
    print("\n🔍 Testando geração de relatório simples...")
    
    try:
        from funcoes_relatorios import gerar_relatorio_interface
        from models.pedagogico import listar_turmas_disponiveis
        
        # Obter primeira turma disponível
        turmas_resultado = listar_turmas_disponiveis()
        if not turmas_resultado.get("success") or not turmas_resultado["turmas"]:
            print("❌ Nenhuma turma disponível para teste")
            return False
        
        primeira_turma = turmas_resultado["turmas"][0]
        print(f"🎓 Testando com turma: {primeira_turma}")
        
        # Configuração mínima para teste
        configuracao = {
            'turmas_selecionadas': [primeira_turma],
            'campos_selecionados': ['nome', 'turno']  # Campos básicos
        }
        
        # Gerar relatório pedagógico
        resultado = gerar_relatorio_interface('pedagogico', configuracao)
        
        if resultado.get("success"):
            print("✅ Relatório pedagógico gerado com sucesso!")
            print(f"   📁 Arquivo: {resultado['nome_arquivo']}")
            print(f"   👨‍🎓 Alunos: {resultado['total_alunos']}")
            print(f"   📋 Campos: {len(resultado['campos_selecionados'])}")
            
            # Verificar se arquivo foi criado
            if os.path.exists(resultado["arquivo"]):
                tamanho = os.path.getsize(resultado["arquivo"])
                print(f"   📊 Tamanho do arquivo: {tamanho} bytes")
                return True
            else:
                print("❌ Arquivo não foi criado")
                return False
        
        else:
            print(f"❌ Erro na geração: {resultado.get('error')}")
            return False
    
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DE RELATÓRIOS")
    print("=" * 50)
    
    testes = [
        ("Importações", testar_importacoes),
        ("Campos Disponíveis", testar_campos_disponiveis),
        ("Conexão Banco", testar_conexao_banco),
        ("Geração Relatório", testar_geracao_relatorio_simples)
    ]
    
    sucessos = 0
    total_testes = len(testes)
    
    for nome_teste, funcao_teste in testes:
        try:
            resultado = funcao_teste()
            if resultado:
                sucessos += 1
        except Exception as e:
            print(f"❌ Erro crítico em {nome_teste}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADOS DOS TESTES")
    print(f"✅ Sucessos: {sucessos}/{total_testes}")
    print(f"❌ Falhas: {total_testes - sucessos}/{total_testes}")
    print(f"📈 Taxa de Sucesso: {(sucessos/total_testes)*100:.1f}%")
    
    if sucessos == total_testes:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Funcionalidade de relatórios está operacional")
        print("💡 Acesse a interface para usar os relatórios")
    else:
        print(f"\n⚠️ {total_testes - sucessos} TESTES FALHARAM")
        print("💡 Verifique as dependências e configurações")
    
    # Limpeza
    try:
        from funcoes_relatorios import limpar_arquivos_temporarios
        limpar_arquivos_temporarios(0)  # Limpar arquivos de teste
        print("\n🧹 Arquivos de teste removidos")
    except:
        pass

if __name__ == "__main__":
    main() 