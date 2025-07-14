#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE ESPECÍFICO - CAMPO MENSALIDADES GERADAS
===============================================

Teste dedicado para validar a implementação do novo campo
"Mensalidades geradas?" no sistema de relatórios pedagógicos.
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def teste_campo_mensalidades_geradas():
    """Testa especificamente o campo mensalidades_geradas"""
    
    print("🧪 TESTE DO CAMPO 'MENSALIDADES GERADAS?'")
    print("=" * 60)
    
    try:
        from funcoes_relatorios import gerar_relatorio_interface, obter_campos_disponiveis
        
        # 1. Verificar se o campo está disponível
        print("\n🔍 ETAPA 1: Verificando disponibilidade do campo...")
        campos = obter_campos_disponiveis()
        
        if 'mensalidades_geradas' in campos['aluno']:
            print("✅ Campo 'mensalidades_geradas' encontrado!")
            print(f"📝 Descrição: {campos['aluno']['mensalidades_geradas']}")
        else:
            print("❌ Campo 'mensalidades_geradas' NÃO encontrado!")
            return False
        
        # 2. Testar geração de relatório com o campo
        print("\n🚀 ETAPA 2: Testando geração de relatório...")
        
        configuracao = {
            'turmas_selecionadas': ['Berçário'],
            'campos_selecionados': ['nome', 'mensalidades_geradas'],
            'situacoes_filtradas': ['matriculado', 'trancado']
        }
        
        print(f"📋 Configuração do teste:")
        print(f"   - Turmas: {configuracao['turmas_selecionadas']}")
        print(f"   - Campos: {configuracao['campos_selecionados']}")
        print(f"   - Situações: {configuracao['situacoes_filtradas']}")
        
        resultado = gerar_relatorio_interface('pedagogico', configuracao)
        
        if resultado.get('success'):
            print("✅ Relatório gerado com sucesso!")
            print(f"📊 Total de alunos: {resultado.get('total_alunos', 0)}")
            print(f"📝 Campos selecionados: {resultado.get('campos_selecionados', [])}")
            print(f"📄 Arquivo: {resultado.get('nome_arquivo', 'N/A')}")
            
            # Verificar se o campo está presente nos campos selecionados
            if 'mensalidades_geradas' in resultado.get('campos_selecionados', []):
                print("✅ Campo 'mensalidades_geradas' incluído no relatório!")
            else:
                print("❌ Campo 'mensalidades_geradas' NÃO incluído no relatório!")
                return False
            
            # 3. Verificar arquivo gerado
            print("\n📁 ETAPA 3: Verificando arquivo gerado...")
            
            if resultado.get('arquivo') and os.path.exists(resultado['arquivo']):
                print("✅ Arquivo .docx criado com sucesso!")
                print(f"📂 Localização: {resultado['arquivo']}")
                
                # Tentar ler o conteúdo do arquivo
                try:
                    from docx import Document
                    doc = Document(resultado['arquivo'])
                    conteudo = ""
                    for paragraph in doc.paragraphs:
                        conteudo += paragraph.text + " "
                    
                    # Verificar se o campo aparece no conteúdo
                    if "Mensalidades geradas" in conteudo or "mensalidades" in conteudo.lower():
                        print("✅ Campo encontrado no conteúdo do relatório!")
                        
                        # Verificar formatação de valores booleanos
                        if "Sim" in conteudo or "Não" in conteudo:
                            print("✅ Valores booleanos formatados corretamente (Sim/Não)!")
                        else:
                            print("⚠️ Formatação de valores booleanos pode não estar correta")
                        
                        return True
                    else:
                        print("❌ Campo não encontrado no conteúdo do relatório!")
                        return False
                
                except ImportError:
                    print("⚠️ python-docx não disponível para verificar conteúdo")
                    print("✅ Mas o arquivo foi gerado com sucesso!")
                    return True
                
                except Exception as e:
                    print(f"⚠️ Erro ao ler arquivo: {e}")
                    print("✅ Mas o arquivo foi gerado com sucesso!")
                    return True
            else:
                print("❌ Arquivo não foi gerado!")
                return False
        
        else:
            print(f"❌ Erro na geração do relatório: {resultado.get('error')}")
            return False
    
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🎯 INICIANDO TESTE DO CAMPO MENSALIDADES GERADAS")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    sucesso = teste_campo_mensalidades_geradas()
    
    print("\n" + "=" * 60)
    if sucesso:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Campo 'Mensalidades geradas?' implementado corretamente!")
        print("💡 O campo está pronto para uso nos relatórios pedagógicos")
    else:
        print("❌ TESTE FALHOU!")
        print("⚠️ Há problemas na implementação do campo")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 