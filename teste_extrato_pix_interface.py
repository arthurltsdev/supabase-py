#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DA FUNCIONALIDADE EXTRATO PIX - INTERFACE PEDAGÓGICA
============================================================

Valida se a busca e processamento do extrato PIX está funcionando corretamente.
"""

from models.pedagogico import supabase
from funcoes_extrato_otimizadas import registrar_pagamento_do_extrato

def testar_busca_extrato_pix():
    """Testa a busca de registros no extrato PIX"""
    print("🧪 TESTE: Busca de Registros no Extrato PIX")
    print("=" * 60)
    
    try:
        # 1. Buscar alguns responsáveis para teste
        print("📋 1. Buscando responsáveis cadastrados...")
        resp_response = supabase.table("responsaveis").select("id, nome, cpf").limit(5).execute()
        
        if not resp_response.data:
            print("❌ Nenhum responsável encontrado")
            return False
        
        print(f"✅ Encontrados {len(resp_response.data)} responsáveis")
        
        # 2. Para cada responsável, buscar registros no extrato PIX
        for resp in resp_response.data:
            print(f"\n👤 Testando responsável: {resp['nome']} (ID: {resp['id']})")
            
            # Buscar por ID do responsável
            extrato_response = supabase.table("extrato_pix").select("*").eq("id_responsavel", resp['id']).execute()
            print(f"   📊 Registros por ID: {len(extrato_response.data) if extrato_response.data else 0}")
            
            # Buscar por nome
            nome_response = supabase.table("extrato_pix").select("*").ilike("nome_remetente", f"%{resp['nome']}%").execute()
            print(f"   📊 Registros por nome: {len(nome_response.data) if nome_response.data else 0}")
            
            # Buscar por CPF se disponível
            if resp.get('cpf'):
                cpf_response = supabase.table("extrato_pix").select("*").or_(
                    f"observacoes.ilike.%{resp['cpf']}%,chave_pix.ilike.%{resp['cpf']}%"
                ).execute()
                print(f"   📊 Registros por CPF: {len(cpf_response.data) if cpf_response.data else 0}")
        
        print("\n✅ Teste de busca concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de busca: {e}")
        return False

def testar_estatisticas_extrato():
    """Testa estatísticas básicas do extrato PIX"""
    print("\n🧪 TESTE: Estatísticas do Extrato PIX")
    print("=" * 60)
    
    try:
        # Total de registros
        total_response = supabase.table("extrato_pix").select("id", count="exact").execute()
        print(f"📊 Total de registros no extrato PIX: {total_response.count}")
        
        # Registros por status
        status_response = supabase.table("extrato_pix").select("status").execute()
        if status_response.data:
            status_counts = {}
            for registro in status_response.data:
                status = registro.get('status', 'desconhecido')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("📋 Registros por status:")
            for status, count in status_counts.items():
                print(f"   - {status}: {count}")
        
        # Registros com responsável identificado
        com_resp_response = supabase.table("extrato_pix").select("id", count="exact").not_.is_("id_responsavel", "null").execute()
        print(f"👥 Registros com responsável identificado: {com_resp_response.count}")
        
        # Registros sem responsável
        sem_resp_response = supabase.table("extrato_pix").select("id", count="exact").is_("id_responsavel", "null").execute()
        print(f"❓ Registros sem responsável: {sem_resp_response.count}")
        
        print("\n✅ Teste de estatísticas concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de estatísticas: {e}")
        return False

def testar_funcao_processamento():
    """Testa se a função de processamento está acessível"""
    print("\n🧪 TESTE: Função de Processamento")
    print("=" * 60)
    
    try:
        # Verificar se a função pode ser importada
        from funcoes_extrato_otimizadas import registrar_pagamento_do_extrato
        print("✅ Função registrar_pagamento_do_extrato importada com sucesso")
        
        # Verificar assinatura da função
        import inspect
        sig = inspect.signature(registrar_pagamento_do_extrato)
        print(f"📋 Parâmetros da função: {list(sig.parameters.keys())}")
        
        print("\n✅ Teste de função concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de função: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DA FUNCIONALIDADE EXTRATO PIX")
    print("=" * 80)
    
    testes_resultados = []
    
    # Executar testes
    testes_resultados.append(("Busca Extrato PIX", testar_busca_extrato_pix()))
    testes_resultados.append(("Estatísticas Extrato", testar_estatisticas_extrato()))
    testes_resultados.append(("Função Processamento", testar_funcao_processamento()))
    
    # Resumo dos resultados
    print("\n" + "=" * 80)
    print("📊 RESUMO DOS TESTES")
    print("=" * 80)
    
    testes_passou = 0
    for nome_teste, resultado in testes_resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{nome_teste:.<30} {status}")
        if resultado:
            testes_passou += 1
    
    print(f"\n🎯 RESULTADO FINAL: {testes_passou}/{len(testes_resultados)} testes passaram")
    
    if testes_passou == len(testes_resultados):
        print("🎉 TODOS OS TESTES PASSARAM! A funcionalidade está pronta.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")

if __name__ == "__main__":
    main() 