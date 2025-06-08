"""
Arquivo de teste para verificar a conexão e funcionamento básico do sistema
Execute este arquivo para verificar se tudo está configurado corretamente
"""

from supabase_functions import (
    supabase,
    listar_turmas,
    analisar_estatisticas_extrato,
    identificar_responsaveis_nao_cadastrados
)

def testar_conexao():
    """Testa a conexão básica com o Supabase"""
    print("🔗 Testando conexão com Supabase...")
    try:
        # Teste simples de conexão
        response = supabase.table("responsaveis").select("id").limit(1).execute()
        print("✅ Conexão com Supabase estabelecida com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        print("Verifique:")
        print("- Se o arquivo .env está configurado corretamente")
        print("- Se as credenciais do Supabase estão corretas")
        print("- Se a tabela 'responsaveis' existe no banco")
        return False

def testar_tabelas():
    """Verifica se as tabelas principais existem"""
    print("\n📋 Verificando tabelas...")
    
    tabelas_necessarias = [
        "alunos",
        "responsaveis", 
        "turmas",
        "extrato_pix",
        "pagamentos",
        "alunos_responsaveis",
        "mensalidades"
    ]
    
    tabelas_ok = []
    tabelas_erro = []
    
    for tabela in tabelas_necessarias:
        try:
            response = supabase.table(tabela).select("*").limit(1).execute()
            tabelas_ok.append(tabela)
        except Exception as e:
            tabelas_erro.append((tabela, str(e)))
    
    print(f"✅ Tabelas funcionando: {len(tabelas_ok)}")
    for tabela in tabelas_ok:
        print(f"   • {tabela}")
    
    if tabelas_erro:
        print(f"\n❌ Tabelas com problema: {len(tabelas_erro)}")
        for tabela, erro in tabelas_erro:
            print(f"   • {tabela}: {erro}")
        return False
    
    return True

def testar_funcoes_basicas():
    """Testa algumas funções básicas do sistema"""
    print("\n🔧 Testando funções básicas...")
    
    # Teste 1: Listar turmas
    print("1. Testando listar_turmas()...")
    try:
        resultado = listar_turmas()
        if resultado["success"]:
            print(f"   ✅ Encontradas {resultado['count']} turmas")
            if resultado["count"] > 0:
                print(f"   Exemplo: {resultado['data'][0]['nome_turma']}")
        else:
            print(f"   ❌ Erro: {resultado['error']}")
    except Exception as e:
        print(f"   ❌ Exceção: {str(e)}")
    
    # Teste 2: Analisar estatísticas do extrato
    print("\n2. Testando analisar_estatisticas_extrato()...")
    try:
        resultado = analisar_estatisticas_extrato()
        if resultado["success"]:
            stats = resultado["estatisticas"]
            print(f"   ✅ Estatísticas obtidas:")
            print(f"   • Total de registros: {stats['total_registros']}")
            print(f"   • Identificados: {stats['total_identificados']}")
            print(f"   • Não identificados: {stats['total_nao_identificados']}")
            print(f"   • Percentual: {stats['percentual_identificacao']}%")
        else:
            print(f"   ❌ Erro: {resultado['error']}")
    except Exception as e:
        print(f"   ❌ Exceção: {str(e)}")
    
    # Teste 3: Identificar responsáveis não cadastrados
    print("\n3. Testando identificar_responsaveis_nao_cadastrados()...")
    try:
        resultado = identificar_responsaveis_nao_cadastrados()
        if resultado["success"]:
            print(f"   ✅ Análise concluída:")
            print(f"   • Responsáveis não cadastrados: {resultado['count']}")
            if resultado['count'] > 0:
                print("   • Exemplos:")
                for detalhe in resultado['detalhes'][:3]:  # Mostra só os 3 primeiros
                    print(f"     - {detalhe['nome']}: {detalhe['quantidade_pagamentos']} pagamentos")
        else:
            print(f"   ❌ Erro: {resultado['error']}")
    except Exception as e:
        print(f"   ❌ Exceção: {str(e)}")

def verificar_dados_essenciais():
    """Verifica se existem dados essenciais para o funcionamento"""
    print("\n📊 Verificando dados essenciais...")
    
    # Verificar se existem turmas
    try:
        turmas = supabase.table("turmas").select("*").execute()
        if turmas.data:
            print(f"✅ Turmas: {len(turmas.data)} cadastradas")
        else:
            print("⚠️  Nenhuma turma cadastrada - será necessário cadastrar turmas primeiro")
    except Exception as e:
        print(f"❌ Erro ao verificar turmas: {str(e)}")
    
    # Verificar se existem dados no extrato PIX
    try:
        extrato = supabase.table("extrato_pix").select("*").limit(1).execute()
        if extrato.data:
            print("✅ Extrato PIX: Contém dados para processamento")
        else:
            print("ℹ️  Extrato PIX vazio - importe dados PIX primeiro")
    except Exception as e:
        print(f"❌ Erro ao verificar extrato PIX: {str(e)}")
    
    # Verificar responsáveis e alunos
    try:
        responsaveis = supabase.table("responsaveis").select("*").limit(1).execute()
        alunos = supabase.table("alunos").select("*").limit(1).execute()
        
        print(f"ℹ️  Responsáveis: {'Existem cadastros' if responsaveis.data else 'Nenhum cadastrado ainda'}")
        print(f"ℹ️  Alunos: {'Existem cadastros' if alunos.data else 'Nenhum cadastrado ainda'}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {str(e)}")

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTE DO SISTEMA DE GESTÃO ESCOLAR")
    print("=" * 60)
    
    # Teste 1: Conexão
    if not testar_conexao():
        print("\n❌ Interrompendo testes devido a erro de conexão")
        return
    
    # Teste 2: Tabelas
    if not testar_tabelas():
        print("\n⚠️  Alguns problemas com tabelas foram encontrados")
        print("O sistema pode não funcionar completamente")
    
    # Teste 3: Funções
    testar_funcoes_basicas()
    
    # Teste 4: Dados
    verificar_dados_essenciais()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMO DOS TESTES")
    print("=" * 60)
    print("✅ Se todos os testes passaram, o sistema está pronto para uso!")
    print("⚠️  Se houve avisos, verifique se você tem os dados necessários")
    print("❌ Se houve erros, corrija-os antes de usar o sistema")
    
    print("\n📚 PRÓXIMOS PASSOS:")
    print("1. Se tudo está OK, execute: python exemplo_uso_supabase.py")
    print("2. Para processamento manual, use as funções em supabase_functions.py")
    print("3. Consulte o README_SISTEMA_GESTAO.md para documentação completa")

if __name__ == "__main__":
    main() 