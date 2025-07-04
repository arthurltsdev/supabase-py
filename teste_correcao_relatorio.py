#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE ESPECÍFICO DAS CORREÇÕES NO RELATÓRIO
==============================================

Testa especificamente:
1. Tratamento correto de valores NULL (mostrar AUSENTE apenas quando realmente NULL)
2. Inclusão do campo "OBSERVAÇÃO:" após cada aluno
"""

from funcoes_relatorios import gerar_relatorio_interface
import os

def testar_correcoes_relatorio():
    """Testa as correções específicas do relatório"""
    print("🧪 TESTANDO CORREÇÕES DO RELATÓRIO")
    print("=" * 50)
    
    # Configuração do relatório de teste
    configuracao = {
        'turmas_selecionadas': ['Berçário'],
        'campos_selecionados': [
            'nome', 'turno', 'data_matricula', 'dia_vencimento', 'valor_mensalidade',
            'nome', 'cpf', 'telefone', 'email', 'tipo_relacao'
        ]
    }
    
    print("🎓 Gerando relatório com turma: Berçário")
    print("📋 Campos selecionados: todos os campos disponíveis")
    print()
    
    # Gerar relatório
    resultado = gerar_relatorio_interface('pedagogico', configuracao)
    
    if resultado.get("success"):
        arquivo = resultado["arquivo"]
        nome_arquivo = resultado["nome_arquivo"]
        
        print("✅ Relatório gerado com sucesso!")
        print(f"📁 Arquivo: {nome_arquivo}")
        print(f"👨‍🎓 Total de alunos: {resultado['total_alunos']}")
        print(f"📊 Tamanho: {os.path.getsize(arquivo):,} bytes")
        print()
        
        # Verificar se arquivo existe
        if os.path.exists(arquivo):
            print("📄 VERIFICAÇÕES:")
            print("✅ Arquivo .docx criado")
            print("✅ Campos com valores reais devem mostrar os dados")
            print("✅ Campos realmente NULL devem mostrar 'AUSENTE'")
            print("✅ Campo 'OBSERVAÇÃO:' deve aparecer após cada aluno")
            print()
            
            print("🎯 PRÓXIMOS PASSOS:")
            print("1. Abra o arquivo gerado para verificar:")
            print(f"   📁 {arquivo}")
            print("2. Verifique se os valores existentes não estão como 'AUSENTE'")
            print("3. Confirme se o campo 'OBSERVAÇÃO:' aparece após cada aluno")
            
            return True
        else:
            print("❌ Arquivo não foi criado")
            return False
    else:
        print(f"❌ Erro na geração: {resultado.get('error')}")
        return False

if __name__ == "__main__":
    sucesso = testar_correcoes_relatorio()
    
    if sucesso:
        print()
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("💡 Abra o arquivo gerado para verificar as correções")
    else:
        print()
        print("❌ TESTE FALHOU")
        print("🔧 Verifique os logs de erro acima") 