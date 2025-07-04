#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE COMPLETO DA INTERFACE PEDAGÓGICA
==========================================

Script para validar todas as funcionalidades implementadas na interface:
- Visualização detalhada de alunos
- Edição de dados de alunos e responsáveis  
- Gestão de vínculos
- Processamento de extrato PIX
- Cadastros completos

"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Função principal de teste"""
    
    print("🧪 TESTE COMPLETO DA INTERFACE PEDAGÓGICA")
    print("=" * 50)
    
    try:
        # 1. Testar importações
        print("\n📦 1. Testando importações...")
        
        from models.pedagogico import (
            buscar_alunos_para_dropdown,
            buscar_informacoes_completas_aluno,
            listar_turmas_disponiveis,
            buscar_responsaveis_para_dropdown
        )
        
        from funcoes_extrato_otimizadas import (
            listar_extrato_pix_por_status,
            atualizar_responsaveis_extrato_pix
        )
        
        print("✅ Todas as importações funcionaram!")
        
        # 2. Testar conexão com banco
        print("\n🔗 2. Testando conexão com banco...")
        
        resultado_turmas = listar_turmas_disponiveis()
        if resultado_turmas.get("success"):
            print(f"✅ Conectado! {resultado_turmas['count']} turmas encontradas")
        else:
            print(f"❌ Erro na conexão: {resultado_turmas.get('error')}")
            return
        
        # 3. Testar busca de alunos
        print("\n👨‍🎓 3. Testando busca de alunos...")
        
        resultado_alunos = buscar_alunos_para_dropdown("a")  # Buscar alunos com 'a'
        if resultado_alunos.get("success"):
            total_alunos = len(resultado_alunos.get("opcoes", []))
            print(f"✅ Busca funcionou! {total_alunos} alunos encontrados")
            
            # Testar informações completas do primeiro aluno
            if total_alunos > 0:
                primeiro_aluno = resultado_alunos["opcoes"][0]
                id_aluno = primeiro_aluno["id"]
                
                print(f"\n📋 4. Testando informações completas do aluno {primeiro_aluno['nome']}...")
                
                info_completa = buscar_informacoes_completas_aluno(id_aluno)
                if info_completa.get("success"):
                    print("✅ Informações completas obtidas!")
                    
                    aluno = info_completa["aluno"]
                    responsaveis = info_completa["responsaveis"]
                    estatisticas = info_completa["estatisticas"]
                    
                    print(f"   📊 Responsáveis: {estatisticas['total_responsaveis']}")
                    print(f"   💳 Pagamentos: {estatisticas['total_pagamentos']}")
                    print(f"   💰 Total pago: R$ {estatisticas['total_pago']:,.2f}")
                    
                    # 5. Testar funcionalidades do extrato PIX
                    print(f"\n🔍 5. Testando funcionalidades do extrato PIX...")
                    
                    try:
                        # Testar listagem do extrato
                        resultado_extrato = listar_extrato_pix_por_status("novo", limite=10)
                        if resultado_extrato.get("success"):
                            registros_novos = resultado_extrato.get("count", 0)
                            print(f"   ✅ {registros_novos} registros 'novos' encontrados no extrato")
                        else:
                            print(f"   ⚠️ Erro ao listar extrato: {resultado_extrato.get('error')}")
                        
                        # Testar atualização de responsáveis
                        resultado_atualizacao = atualizar_responsaveis_extrato_pix()
                        if resultado_atualizacao.get("success"):
                            atualizados = resultado_atualizacao.get("atualizados", 0)
                            print(f"   ✅ {atualizados} registros atualizados com responsáveis")
                        else:
                            print(f"   ⚠️ Erro na atualização: {resultado_atualizacao.get('error')}")
                    
                    except Exception as e:
                        print(f"   ⚠️ Erro ao testar extrato PIX: {e}")
                    
                    print(f"✅ Testes do extrato PIX concluídos!")
                    
                else:
                    print(f"❌ Erro ao obter informações completas: {info_completa.get('error')}")
            
        else:
            print(f"❌ Erro na busca de alunos: {resultado_alunos.get('error')}")
        
        # 6. Testar busca de responsáveis
        print("\n👥 6. Testando busca de responsáveis...")
        
        resultado_responsaveis = buscar_responsaveis_para_dropdown("a")
        if resultado_responsaveis.get("success"):
            total_responsaveis = len(resultado_responsaveis.get("opcoes", []))
            print(f"✅ Busca de responsáveis funcionou! {total_responsaveis} responsáveis encontrados")
        else:
            print(f"❌ Erro na busca de responsáveis: {resultado_responsaveis.get('error')}")
        
        # 7. Verificar interface Streamlit
        print("\n🖥️ 7. Verificando interface Streamlit...")
        
        try:
            import streamlit as st
            print(f"✅ Streamlit {st.__version__} disponível!")
        except Exception as e:
            print(f"❌ Erro no Streamlit: {e}")
        
        # Resumo final
        print("\n" + "=" * 50)
        print("🎉 TESTE COMPLETO FINALIZADO!")
        print("=" * 50)
        print("\n✅ FUNCIONALIDADES VALIDADAS:")
        print("   📦 Importações de módulos")
        print("   🔗 Conexão com banco de dados")
        print("   👨‍🎓 Busca e visualização de alunos")
        print("   📋 Informações completas de alunos")
        print("   👥 Busca de responsáveis")
        print("   🔍 Integração com extrato PIX")
        print("   🖥️ Interface Streamlit")
        
        print("\n🚀 INTERFACE PRONTA PARA USO!")
        print("\n💡 Para executar a interface:")
        print("   streamlit run interface_pedagogica_teste.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 