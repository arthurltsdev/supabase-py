"""
Exemplo de uso das funções do Supabase para gestão escolar
Demonstra como processar responsáveis do extrato PIX e cadastrá-los automaticamente
"""

from supabase_functions import (
    identificar_responsaveis_nao_cadastrados,
    processar_responsaveis_extrato_pix,
    cadastrar_responsavel_completo,
    listar_responsaveis,
    listar_alunos,
    cadastrar_aluno,
    vincular_aluno_responsavel,
    registrar_pagamento,
    analisar_estatisticas_extrato,
    listar_pagamentos_nao_identificados,
    buscar_responsavel_por_nome,
    atualizar_responsavel_extrato_pix
)

def exemplo_fluxo_completo():
    """Demonstra o fluxo completo de processamento do extrato PIX"""
    print("=== FLUXO COMPLETO DE PROCESSAMENTO DO EXTRATO PIX ===\n")
    
    # 1. Analisar estatísticas do extrato antes do processamento
    print("1. Analisando estatísticas do extrato PIX...")
    stats = analisar_estatisticas_extrato()
    if stats["success"]:
        est = stats["estatisticas"]
        print(f"   • Total de registros: {est['total_registros']}")
        print(f"   • Identificados: {est['total_identificados']}")
        print(f"   • Não identificados: {est['total_nao_identificados']}")
        print(f"   • Percentual de identificação: {est['percentual_identificacao']}%")
        print(f"   • Valor total: R$ {est['valor_total']:.2f}")
        print(f"   • Valor não identificado: R$ {est['valor_nao_identificado']:.2f}")
    else:
        print(f"   ❌ Erro: {stats['error']}")
    
    print("\n" + "="*60 + "\n")
    
    # 2. Identificar responsáveis não cadastrados
    print("2. Identificando responsáveis não cadastrados...")
    resultado_identificacao = identificar_responsaveis_nao_cadastrados()
    
    if resultado_identificacao["success"]:
        count = resultado_identificacao["count"]
        print(f"   ✅ Encontrados {count} responsáveis não cadastrados:")
        
        for detalhe in resultado_identificacao["detalhes"]:
            nome = detalhe["nome"]
            qtd = detalhe["quantidade_pagamentos"]
            valor = detalhe["valor_total"]
            print(f"      • {nome}: {qtd} pagamentos, R$ {valor:.2f}")
        
        if count == 0:
            print("   ℹ️  Todos os responsáveis já estão cadastrados!")
            return
            
    else:
        print(f"   ❌ Erro: {resultado_identificacao['error']}")
        return
    
    print("\n" + "="*60 + "\n")
    
    # 3. Processar responsáveis automaticamente
    print("3. Processando responsáveis automaticamente...")
    resultado_processamento = processar_responsaveis_extrato_pix()
    
    if resultado_processamento["success"]:
        cadastrados = resultado_processamento["total_cadastrados"]
        print(f"   ✅ Cadastrados {cadastrados} responsáveis com sucesso:")
        
        for resp in resultado_processamento["responsaveis_cadastrados"]:
            nome = resp["nome"]
            id_resp = resp["id_responsavel"]
            registros = resp["registros_atualizados"]
            print(f"      • {nome} (ID: {id_resp}) - {registros} registros atualizados")
        
        if resultado_processamento.get("erros"):
            print("   ⚠️  Erros encontrados:")
            for erro in resultado_processamento["erros"]:
                print(f"      • {erro}")
                
    else:
        print(f"   ❌ Erro: {resultado_processamento['error']}")
        return
    
    print("\n" + "="*60 + "\n")
    
    # 4. Verificar estatísticas após processamento
    print("4. Verificando estatísticas após processamento...")
    stats_final = analisar_estatisticas_extrato()
    if stats_final["success"]:
        est_final = stats_final["estatisticas"]
        print(f"   • Total identificados: {est_final['total_identificados']}")
        print(f"   • Não identificados: {est_final['total_nao_identificados']}")
        print(f"   • Novo percentual: {est_final['percentual_identificacao']}%")
        print(f"   • Valor ainda não identificado: R$ {est_final['valor_nao_identificado']:.2f}")
    
    print("\n✅ Processamento concluído!")

def exemplo_cadastro_manual():
    """Demonstra cadastro manual de responsável e aluno"""
    print("=== EXEMPLO DE CADASTRO MANUAL ===\n")
    
    # 1. Cadastrar responsável
    print("1. Cadastrando responsável...")
    resultado_resp = cadastrar_responsavel_completo(
        nome="João Silva Santos",
        cpf="123.456.789-00",
        telefone="(11) 99999-9999",
        email="joao.silva@email.com",
        endereco="Rua das Flores, 123",
        tipo_relacao="pai"
    )
    
    if resultado_resp["success"]:
        id_responsavel = resultado_resp["id_responsavel"]
        print(f"   ✅ Responsável cadastrado: {id_responsavel}")
    else:
        print(f"   ❌ Erro: {resultado_resp['error']}")
        return
    
    print()
    
    # 2. Cadastrar aluno
    print("2. Cadastrando aluno...")
    resultado_aluno = cadastrar_aluno(
        nome="Maria Silva Santos",
        nome_turma="Infantil III",  # Precisa existir na tabela turmas
        data_nascimento="15/03/2018",
        dia_vencimento=10,
        valor_mensalidade=350.00,
        data_matricula="01/02/2024",
        turno="Manhã"
    )
    
    if resultado_aluno["success"]:
        id_aluno = resultado_aluno["id_aluno"]
        print(f"   ✅ Aluno cadastrado: {id_aluno}")
    else:
        print(f"   ❌ Erro: {resultado_aluno['error']}")
        return
    
    print()
    
    # 3. Vincular responsável ao aluno
    print("3. Vinculando responsável ao aluno...")
    resultado_vinculo = vincular_aluno_responsavel(
        id_aluno=id_aluno,
        id_responsavel=id_responsavel,
        responsavel_financeiro=True,
        tipo_relacao="pai"
    )
    
    if resultado_vinculo["success"]:
        print(f"   ✅ Vinculação criada: {resultado_vinculo['id_vinculo']}")
    else:
        print(f"   ❌ Erro: {resultado_vinculo['error']}")
        return
    
    print()
    
    # 4. Registrar um pagamento
    print("4. Registrando pagamento...")
    resultado_pagamento = registrar_pagamento(
        id_responsavel=id_responsavel,
        id_aluno=id_aluno,
        data_pagamento="15/01/2024",
        valor=350.00,
        tipo_pagamento="mensalidade",
        forma_pagamento="PIX",
        descricao="Mensalidade Janeiro 2024"
    )
    
    if resultado_pagamento["success"]:
        print(f"   ✅ Pagamento registrado: {resultado_pagamento['id_pagamento']}")
    else:
        print(f"   ❌ Erro: {resultado_pagamento['error']}")
    
    print("\n✅ Cadastro manual concluído!")

def exemplo_consultas():
    """Demonstra diferentes tipos de consultas"""
    print("=== EXEMPLOS DE CONSULTAS ===\n")
    
    # 1. Listar todos os responsáveis
    print("1. Listando todos os responsáveis...")
    responsaveis = listar_responsaveis()
    if responsaveis["success"]:
        print(f"   ✅ Encontrados {responsaveis['count']} responsáveis")
        for resp in responsaveis["data"][:3]:  # Mostra apenas os 3 primeiros
            print(f"      • {resp['nome']} (ID: {resp['id']})")
        if responsaveis['count'] > 3:
            print(f"      ... e mais {responsaveis['count'] - 3} responsáveis")
    else:
        print(f"   ❌ Erro: {responsaveis['error']}")
    
    print()
    
    # 2. Buscar alunos por nome
    print("2. Buscando alunos com 'Maria' no nome...")
    alunos = listar_alunos(filtro_nome="Maria")
    if alunos["success"]:
        print(f"   ✅ Encontrados {alunos['count']} alunos")
        for aluno in alunos["data"]:
            turma = aluno.get("turmas", {}).get("nome_turma", "N/A")
            print(f"      • {aluno['nome']} - Turma: {turma}")
    else:
        print(f"   ❌ Erro: {alunos['error']}")
    
    print()
    
    # 3. Listar pagamentos não identificados
    print("3. Consultando pagamentos não identificados...")
    nao_identificados = listar_pagamentos_nao_identificados(limite=5, formato_resumido=True)
    if nao_identificados["success"]:
        print("   ✅ Resumo dos não identificados:")
        for nome, info in nao_identificados["resumo"].items():
            print(f"      • {nome}: {info['quantidade']} pagamentos, R$ {info['valor_total']:.2f}")
    else:
        print(f"   ❌ Erro: {nao_identificados['error']}")

def exemplo_busca_especifica():
    """Demonstra busca específica por responsável"""
    print("=== EXEMPLO DE BUSCA ESPECÍFICA ===\n")
    
    nome_para_buscar = "João Silva Santos"  # Nome que você quer buscar
    
    print(f"Buscando responsável: {nome_para_buscar}")
    resultado = buscar_responsavel_por_nome(nome_para_buscar)
    
    if resultado["success"]:
        if resultado["encontrado"]:
            resp = resultado["data"]
            print(f"✅ Responsável encontrado:")
            print(f"   • ID: {resp['id']}")
            print(f"   • Nome: {resp['nome']}")
            print(f"   • CPF: {resp.get('cpf', 'N/A')}")
            print(f"   • Telefone: {resp.get('telefone', 'N/A')}")
            print(f"   • Email: {resp.get('email', 'N/A')}")
            
            # Se encontrou, pode atualizar o extrato PIX
            print(f"\nAtualizando registros do extrato PIX...")
            resultado_update = atualizar_responsavel_extrato_pix(nome_para_buscar, resp['id'])
            if resultado_update["success"]:
                print(f"✅ {resultado_update['registros_atualizados']} registros atualizados")
            else:
                print(f"❌ Erro ao atualizar: {resultado_update['error']}")
        else:
            print("❌ Responsável não encontrado")
    else:
        print(f"❌ Erro na busca: {resultado['error']}")

if __name__ == "__main__":
    print("SISTEMA DE GESTÃO ESCOLAR - EXEMPLOS DE USO")
    print("=" * 60)
    
    try:
        # Escolha qual exemplo executar:
        
        # 1. Fluxo completo (recomendado para primeiro uso)
        exemplo_fluxo_completo()
        
        print("\n" + "="*60 + "\n")
        
        # 2. Exemplos de consultas
        exemplo_consultas()
        
        # Descomente abaixo para testar outros exemplos:
        
        # print("\n" + "="*60 + "\n")
        # exemplo_cadastro_manual()
        
        # print("\n" + "="*60 + "\n") 
        # exemplo_busca_especifica()
        
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        print("Verifique se:")
        print("- O arquivo .env está configurado corretamente")
        print("- A conexão com o Supabase está funcionando")
        print("- As tabelas necessárias existem no banco") 