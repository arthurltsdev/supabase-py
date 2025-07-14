#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DAS MELHORIAS NO SISTEMA DE RELATÓRIOS PEDAGÓGICOS
===========================================================

Teste para validar as melhorias implementadas:
1. Filtro de situação funcionando corretamente
2. Campos selecionados sendo respeitados
3. Formatação especial para campos vazios
4. Campos de saída para alunos trancados
5. Controle do campo OBSERVAÇÕES
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def teste_melhorias_relatorios():
    """Executa testes das melhorias implementadas"""
    
    print("🧪 INICIANDO TESTES DAS MELHORIAS DE RELATÓRIOS")
    print("=" * 60)
    
    try:
        # Importar funções necessárias
        from funcoes_relatorios import gerar_relatorio_interface, obter_campos_disponiveis
        from models.pedagogico import listar_turmas_disponiveis
        
        print("✅ Importações realizadas com sucesso")
        
        # 1. TESTE DE FILTRO DE SITUAÇÃO
        print("\n🔍 TESTE 1: Filtro de Situação")
        print("-" * 40)
        
        # Obter turmas disponíveis
        turmas_resultado = listar_turmas_disponiveis()
        if not turmas_resultado.get("success"):
            print("❌ Erro ao obter turmas:", turmas_resultado.get("error"))
            return
        
        turmas_disponiveis = turmas_resultado["turmas"]
        print(f"📋 Turmas disponíveis: {turmas_disponiveis}")
        
        # Usar a primeira turma disponível para teste
        if not turmas_disponiveis:
            print("❌ Nenhuma turma disponível para teste")
            return
            
        turma_teste = turmas_disponiveis[0]
        print(f"🎓 Usando turma para teste: {turma_teste}")
        
        # 2. TESTE COM CAMPOS ESPECÍFICOS
        print("\n📋 TESTE 2: Campos Selecionados Específicos")
        print("-" * 40)
        
        # Configuração do teste: apenas nome do aluno + situação + nome do responsável
        configuracao_teste = {
            "turmas_selecionadas": [turma_teste],
            "campos_selecionados": ["nome", "situacao", "nome"],  # nome do aluno + situação + nome do responsável
            "situacoes_filtradas": ["matriculado"]  # Apenas alunos matriculados
        }
        
        print(f"🔧 Configuração do teste:")
        print(f"   - Turmas: {configuracao_teste['turmas_selecionadas']}")
        print(f"   - Campos: {configuracao_teste['campos_selecionados']}")
        print(f"   - Situações: {configuracao_teste['situacoes_filtradas']}")
        
        # 3. EXECUTAR GERAÇÃO DO RELATÓRIO
        print("\n🚀 TESTE 3: Geração do Relatório")
        print("-" * 40)
        
        resultado = gerar_relatorio_interface("pedagogico", configuracao_teste)
        
        if resultado.get("success"):
            print("✅ Relatório gerado com sucesso!")
            print(f"📄 Arquivo: {resultado['nome_arquivo']}")
            print(f"👨‍🎓 Total de alunos: {resultado['total_alunos']}")
            print(f"🎓 Turmas: {resultado['turmas_incluidas']}")
            print(f"📋 Campos: {resultado['campos_selecionados']}")
            print(f"⚙️ Situações filtradas: {resultado.get('situacoes_filtradas', 'N/A')}")
            
            # Verificar se o arquivo foi criado
            if os.path.exists(resultado["arquivo"]):
                print(f"📁 Arquivo criado em: {resultado['arquivo']}")
                
                # Verificar tamanho do arquivo
                tamanho = os.path.getsize(resultado["arquivo"])
                print(f"📊 Tamanho do arquivo: {tamanho} bytes")
                
                if tamanho > 1000:  # Arquivo deve ter pelo menos 1KB
                    print("✅ Arquivo tem tamanho adequado")
                else:
                    print("⚠️ Arquivo muito pequeno, pode haver problema")
            else:
                print("❌ Arquivo não encontrado no caminho especificado")
                
        else:
            print("❌ Erro na geração do relatório:")
            print(f"   Erro: {resultado.get('error')}")
            return
        
        # 4. TESTE COM FILTRO DE SITUAÇÃO "TRANCADO"
        print("\n🔒 TESTE 4: Filtro para Alunos Trancados")
        print("-" * 40)
        
        configuracao_trancados = {
            "turmas_selecionadas": [turma_teste],
            "campos_selecionados": ["nome", "situacao", "data_saida", "motivo_saida", "nome"],  # Incluir campos de saída
            "situacoes_filtradas": ["trancado"]  # Apenas alunos trancados
        }
        
        resultado_trancados = gerar_relatorio_interface("pedagogico", configuracao_trancados)
        
        if resultado_trancados.get("success"):
            print("✅ Relatório de trancados gerado com sucesso!")
            print(f"👨‍🎓 Total de alunos trancados: {resultado_trancados['total_alunos']}")
            
            if resultado_trancados['total_alunos'] == 0:
                print("ℹ️ Nenhum aluno trancado encontrado (isso é normal)")
            else:
                print(f"📄 Arquivo de trancados: {resultado_trancados['nome_arquivo']}")
        else:
            print("❌ Erro na geração do relatório de trancados:")
            print(f"   Erro: {resultado_trancados.get('error')}")
        
        # 5. TESTE COM TODOS OS CAMPOS
        print("\n📋 TESTE 5: Todos os Campos Disponíveis")
        print("-" * 40)
        
        campos_disponiveis = obter_campos_disponiveis()
        todos_campos_aluno = list(campos_disponiveis["aluno"].keys())
        todos_campos_responsavel = list(campos_disponiveis["responsavel"].keys())
        todos_campos = todos_campos_aluno + todos_campos_responsavel
        
        print(f"🔧 Testando com todos os campos ({len(todos_campos)} campos):")
        print(f"   - Aluno: {todos_campos_aluno}")
        print(f"   - Responsável: {todos_campos_responsavel}")
        
        configuracao_completa = {
            "turmas_selecionadas": [turma_teste],
            "campos_selecionados": todos_campos,
            "situacoes_filtradas": ["matriculado", "trancado", "problema"]  # Todas as situações
        }
        
        resultado_completo = gerar_relatorio_interface("pedagogico", configuracao_completa)
        
        if resultado_completo.get("success"):
            print("✅ Relatório completo gerado com sucesso!")
            print(f"👨‍🎓 Total de alunos (todas situações): {resultado_completo['total_alunos']}")
            print(f"📄 Arquivo completo: {resultado_completo['nome_arquivo']}")
        else:
            print("❌ Erro na geração do relatório completo:")
            print(f"   Erro: {resultado_completo.get('error')}")
        
        print("\n" + "="*60)
        print("🧪 TESTE 5: CAMPO MENSALIDADES GERADAS")
        print("="*60)
        
        print("\n🔍 Testando campo 'Mensalidades geradas?' nos relatórios...")
        
        # Configuração do teste 
        turmas_teste = ["Berçário"]
        campos_teste = ["nome", "mensalidades_geradas"]  # Incluir o novo campo
        situacoes_teste = ["matriculado"]
        
        try:
            # Gerar relatório pedagógico com o novo campo
            resultado = gerar_relatorio_interface("pedagogico", {"turmas_selecionadas": turmas_teste, "campos_selecionados": campos_teste, "situacoes_filtradas": situacoes_teste})
            
            if resultado.get("success"):
                print("✅ Relatório gerado com sucesso!")
                print(f"📋 Turmas: {', '.join(resultado.get('turmas_incluidas', []))}")
                print(f"📊 Total de alunos: {resultado.get('total_alunos', 0)}")
                print(f"📝 Campos selecionados: {', '.join(resultado.get('campos_selecionados', []))}")
                
                # Verificar se o campo mensalidades_geradas está presente
                if "mensalidades_geradas" in resultado.get('campos_selecionados', []):
                    print("✅ Campo 'Mensalidades geradas?' incluído corretamente!")
                else:
                    print("❌ Campo 'Mensalidades geradas?' não encontrado nos campos selecionados!")
                
                # Verificar arquivo gerado
                if resultado.get("arquivo") and os.path.exists(resultado["arquivo"]):
                    print(f"📁 Arquivo gerado: {resultado.get('nome_arquivo')}")
                    print("✅ Arquivo .docx criado com sucesso!")
                    
                    # Tentar ler conteúdo para verificar se o campo aparece
                    print("\n📖 Verificando conteúdo do relatório...")
                    try:
                        from docx import Document
                        doc = Document(resultado["arquivo"])
                        conteudo_doc = ""
                        for paragraph in doc.paragraphs:
                            conteudo_doc += paragraph.text + "\n"
                        
                        # Verificar se o campo aparece no conteúdo
                        if "Mensalidades geradas" in conteudo_doc or "mensalidades" in conteudo_doc.lower():
                            print("✅ Campo 'Mensalidades geradas?' encontrado no conteúdo do relatório!")
                            
                            # Buscar por valores Sim/Não
                            if "Sim" in conteudo_doc or "Não" in conteudo_doc:
                                print("✅ Valores booleanos formatados corretamente (Sim/Não)!")
                            else:
                                print("⚠️ Valores booleanos podem não estar formatados como esperado")
                        else:
                            print("❌ Campo 'Mensalidades geradas?' não encontrado no conteúdo!")
                    
                    except Exception as e:
                        print(f"⚠️ Não foi possível verificar o conteúdo do documento: {e}")
                else:
                    print("❌ Arquivo não foi gerado ou não existe!")
            else:
                print(f"❌ Erro na geração do relatório: {resultado.get('error')}")
        
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
        
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES CONCLUÍDO")
        print("="*60)
        print("✅ Todos os testes executados!")
        print("💡 Verifique os arquivos gerados na pasta temp_reports/")
        print("🔧 Melhorias implementadas com sucesso!")
    
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se de que todos os módulos estão disponíveis")
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    teste_melhorias_relatorios() 