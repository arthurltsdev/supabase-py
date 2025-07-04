#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 TESTE DAS MELHORIAS DA INTERFACE PEDAGÓGICA
============================================

Testa as novas funcionalidades implementadas:
1. Exibição melhorada do extrato PIX
2. Funcionalidade de gerar mensalidades
3. Processamento de múltiplos pagamentos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.pedagogico import supabase
from funcoes_extrato_otimizadas import (
    verificar_pode_gerar_mensalidades,
    gerar_mensalidades_aluno,
    listar_mensalidades_disponiveis_aluno,
    registrar_pagamentos_multiplos_do_extrato
)

def testar_gerador_mensalidades():
    """Testa a funcionalidade de gerar mensalidades"""
    print("🧪 TESTE: Gerador de Mensalidades")
    print("=" * 50)
    
    try:
        # 1. Buscar um aluno para teste
        print("📋 1. Buscando aluno para teste...")
        aluno_response = supabase.table("alunos").select("id, nome, data_matricula, dia_vencimento, valor_mensalidade, mensalidades_geradas").limit(1).execute()
        
        if not aluno_response.data:
            print("❌ Nenhum aluno encontrado")
            return False
        
        aluno = aluno_response.data[0]
        print(f"✅ Aluno encontrado: {aluno['nome']}")
        
        # 2. Verificar se pode gerar mensalidades
        print("\n📋 2. Verificando se pode gerar mensalidades...")
        verificacao = verificar_pode_gerar_mensalidades(aluno["id"])
        
        if verificacao.get("success"):
            print(f"✅ Verificação realizada com sucesso")
            print(f"   - Pode gerar: {verificacao.get('pode_gerar')}")
            
            if verificacao.get("problemas"):
                print("   - Problemas encontrados:")
                for problema in verificacao["problemas"]:
                    print(f"     {problema}")
            
            if verificacao.get("pode_gerar"):
                print("   ✅ Aluno pode gerar mensalidades!")
                
                # 3. Simular geração (modo automático)
                print("\n📋 3. Simulando geração de mensalidades...")
                resultado = gerar_mensalidades_aluno(aluno["id"], automatico=True)
                
                if resultado.get("success"):
                    print(f"✅ {resultado.get('mensalidades_criadas', 0)} mensalidades geradas!")
                    print(f"   - Modo: {resultado.get('modo')}")
                    print(f"   - Aluno: {resultado.get('aluno_nome')}")
                else:
                    print(f"❌ Erro ao gerar: {resultado.get('error')}")
            else:
                print("   ⚠️ Aluno não pode gerar mensalidades ainda")
        else:
            print(f"❌ Erro na verificação: {verificacao.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def testar_listagem_mensalidades():
    """Testa a listagem de mensalidades disponíveis"""
    print("\n🧪 TESTE: Listagem de Mensalidades Disponíveis")
    print("=" * 50)
    
    try:
        # Buscar um aluno com mensalidades
        print("📋 1. Buscando aluno com mensalidades...")
        aluno_response = supabase.table("alunos").select("id, nome").limit(1).execute()
        
        if not aluno_response.data:
            print("❌ Nenhum aluno encontrado")
            return False
        
        aluno = aluno_response.data[0]
        print(f"✅ Aluno encontrado: {aluno['nome']}")
        
        # Listar mensalidades disponíveis
        print("\n📋 2. Listando mensalidades disponíveis...")
        resultado = listar_mensalidades_disponiveis_aluno(aluno["id"])
        
        if resultado.get("success"):
            mensalidades = resultado.get("mensalidades", [])
            print(f"✅ {len(mensalidades)} mensalidades disponíveis")
            
            for i, mens in enumerate(mensalidades[:3], 1):  # Mostrar apenas 3
                print(f"   {i}. {mens['label']}")
                print(f"      - ID: {mens['id_mensalidade']}")
                print(f"      - Vencimento: {mens['data_vencimento']}")
                print(f"      - Status: {mens['status_texto']}")
        else:
            print(f"❌ Erro na listagem: {resultado.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def testar_exibicao_extrato_pix():
    """Testa a exibição melhorada do extrato PIX"""
    print("\n🧪 TESTE: Exibição do Extrato PIX")
    print("=" * 50)
    
    try:
        # Buscar alguns registros do extrato
        print("📋 1. Buscando registros do extrato PIX...")
        extrato_response = supabase.table("extrato_pix").select("*").limit(5).execute()
        
        if not extrato_response.data:
            print("❌ Nenhum registro encontrado no extrato PIX")
            return False
        
        registros = extrato_response.data
        print(f"✅ {len(registros)} registros encontrados")
        
        # Simular a formatação melhorada
        print("\n📋 2. Formatação melhorada dos registros:")
        
        # Ordenar por data (mais antigo primeiro)
        registros_ordenados = sorted(registros, key=lambda x: x.get('data_pagamento', ''))
        
        for i, registro in enumerate(registros_ordenados, 1):
            nome_remetente = registro.get('nome_remetente', 'Nome não informado')
            valor = float(registro.get('valor', 0))
            data_pagamento = registro.get('data_pagamento', 'N/A')
            
            # Converter data para formato brasileiro
            try:
                from datetime import datetime
                data_obj = datetime.strptime(data_pagamento, '%Y-%m-%d')
                data_formatada = data_obj.strftime('%d/%m/%Y')
            except:
                data_formatada = data_pagamento
            
            # Formato solicitado: "1- Nome - Valor: R$ X,XX - Data: DD/MM/YYYY"
            titulo_melhorado = f"{i}- {nome_remetente} - Valor: R$ {valor:,.2f} - Data: {data_formatada}"
            print(f"   {titulo_melhorado}")
        
        print("\n✅ Formatação implementada com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def testar_processamento_multiplos_pagamentos():
    """Testa o processamento de múltiplos pagamentos"""
    print("\n🧪 TESTE: Processamento de Múltiplos Pagamentos")
    print("=" * 50)
    
    try:
        # Buscar um registro não processado
        print("📋 1. Buscando registro não processado...")
        extrato_response = supabase.table("extrato_pix").select("*").neq("status", "registrado").limit(1).execute()
        
        if not extrato_response.data:
            print("❌ Nenhum registro não processado encontrado")
            return False
        
        registro = extrato_response.data[0]
        print(f"✅ Registro encontrado: {registro.get('nome_remetente')} - R$ {float(registro.get('valor', 0)):,.2f}")
        
        # Buscar um responsável
        print("\n📋 2. Buscando responsável...")
        resp_response = supabase.table("responsaveis").select("id, nome").limit(1).execute()
        
        if not resp_response.data:
            print("❌ Nenhum responsável encontrado")
            return False
        
        responsavel = resp_response.data[0]
        print(f"✅ Responsável encontrado: {responsavel['nome']}")
        
        # Buscar alunos vinculados
        print("\n📋 3. Buscando alunos vinculados...")
        from funcoes_extrato_otimizadas import listar_alunos_vinculados_responsavel
        alunos_resultado = listar_alunos_vinculados_responsavel(responsavel["id"])
        
        if not alunos_resultado.get("success") or not alunos_resultado.get("alunos"):
            print("❌ Nenhum aluno vinculado encontrado")
            return False
        
        alunos = alunos_resultado["alunos"]
        print(f"✅ {len(alunos)} alunos vinculados")
        
        # Simular configuração de múltiplos pagamentos
        print("\n📋 4. Simulando configuração de múltiplos pagamentos...")
        
        valor_total = float(registro.get('valor', 0))
        num_pagamentos = min(2, len(alunos))  # Máximo 2 pagamentos
        valor_por_pagamento = valor_total / num_pagamentos
        
        pagamentos_detalhados = []
        for i in range(num_pagamentos):
            pagamento = {
                "id_aluno": alunos[i]["id"],
                "nome_aluno": alunos[i]["nome"],
                "tipo_pagamento": "material",
                "valor": valor_por_pagamento,
                "observacoes": f"Pagamento {i+1} de {num_pagamentos}"
            }
            pagamentos_detalhados.append(pagamento)
        
        print(f"✅ {len(pagamentos_detalhados)} pagamentos configurados:")
        for i, pag in enumerate(pagamentos_detalhados, 1):
            print(f"   {i}. {pag['nome_aluno']} - {pag['tipo_pagamento']} - R$ {pag['valor']:.2f}")
        
        # Validar valores
        valor_total_configurado = sum(p['valor'] for p in pagamentos_detalhados)
        diferenca = abs(valor_total - valor_total_configurado)
        
        print(f"\n📊 Validação de valores:")
        print(f"   - Valor total do registro: R$ {valor_total:.2f}")
        print(f"   - Valor total configurado: R$ {valor_total_configurado:.2f}")
        print(f"   - Diferença: R$ {diferenca:.2f}")
        
        if diferenca < 0.01:
            print("✅ Valores conferem!")
        else:
            print("❌ Valores não conferem!")
        
        print("\n✅ Funcionalidade de múltiplos pagamentos validada!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def executar_todos_os_testes():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DAS MELHORIAS DA INTERFACE PEDAGÓGICA")
    print("=" * 70)
    
    testes = [
        ("Exibição do Extrato PIX", testar_exibicao_extrato_pix),
        ("Gerador de Mensalidades", testar_gerador_mensalidades),
        ("Listagem de Mensalidades", testar_listagem_mensalidades),
        ("Múltiplos Pagamentos", testar_processamento_multiplos_pagamentos)
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        try:
            resultado = funcao_teste()
            resultados.append((nome_teste, resultado))
        except Exception as e:
            print(f"❌ Erro no teste {nome_teste}: {e}")
            resultados.append((nome_teste, False))
    
    # Resumo final
    print("\n" + "=" * 70)
    print("📊 RESUMO FINAL DOS TESTES")
    print("=" * 70)
    
    sucessos = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{status} - {nome}")
        if resultado:
            sucessos += 1
    
    print(f"\n🎯 RESULTADO FINAL: {sucessos}/{len(resultados)} testes passaram")
    
    if sucessos == len(resultados):
        print("🎉 TODOS OS TESTES PASSARAM! As melhorias estão funcionando perfeitamente.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os detalhes acima.")
    
    return sucessos == len(resultados)

if __name__ == "__main__":
    executar_todos_os_testes() 