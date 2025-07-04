#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste para verificar o funcionamento da busca por turmas
"""

from funcoes_extrato_otimizadas import listar_turmas_disponiveis, buscar_alunos_por_turmas, supabase

def teste_busca_turmas():
    """Testa a funcionalidade de busca por turmas"""
    
    print("="*60)
    print("🧪 TESTE: Busca por Turmas")
    print("="*60)
    
    # 1. Listar turmas disponíveis
    print("\n1️⃣ Listando turmas disponíveis...")
    turmas_resultado = listar_turmas_disponiveis()
    
    if turmas_resultado.get("success"):
        turmas = turmas_resultado["turmas"]
        print(f"✅ {len(turmas)} turmas encontradas: {turmas}")
    else:
        print(f"❌ Erro ao listar turmas: {turmas_resultado.get('error')}")
        return
    
    # 2. Buscar IDs das turmas
    print("\n2️⃣ Buscando IDs das turmas...")
    try:
        turmas_response = supabase.table("turmas").select("id, nome_turma").order("nome_turma").execute()
        turmas_com_id = {turma["nome_turma"]: turma["id"] for turma in turmas_response.data}
        print(f"✅ IDs das turmas mapeados:")
        for nome, id_turma in turmas_com_id.items():
            print(f"   - {nome}: {id_turma}")
    except Exception as e:
        print(f"❌ Erro ao buscar IDs: {str(e)}")
        return
    
    # 3. Testar busca por turmas específicas
    print("\n3️⃣ Testando busca por turmas específicas...")
    
    # Selecionar algumas turmas para teste (usando nomes corretos do banco)
    turmas_teste = ["Berçário", "Infantil I", "Infantil II", "Infantil III"]
    ids_teste = [turmas_com_id[nome] for nome in turmas_teste if nome in turmas_com_id]
    
    print(f"🔍 Buscando alunos das turmas: {turmas_teste}")
    print(f"🔍 IDs correspondentes: {ids_teste}")
    
    resultado = buscar_alunos_por_turmas(ids_teste)
    
    if resultado.get("success"):
        print(f"✅ Busca concluída com sucesso!")
        print(f"📊 Total de alunos: {resultado.get('total_alunos', 0)}")
        print(f"📊 Total de turmas: {resultado.get('total_turmas', 0)}")
        
        alunos_por_turma = resultado.get("alunos_por_turma", {})
        
        for turma_nome, dados in alunos_por_turma.items():
            print(f"\n🎓 {turma_nome}: {len(dados['alunos'])} alunos")
            for aluno in dados['alunos']:
                print(f"   - {aluno['nome']} (ID: {aluno['id']})")
                print(f"     Responsáveis: {aluno['total_responsaveis']}")
                for resp in aluno.get('responsaveis', []):
                    badge = "💰" if resp.get('responsavel_financeiro') else "👤"
                    print(f"       {badge} {resp['nome']} - {resp['tipo_relacao']}")
    else:
        print(f"❌ Erro na busca: {resultado.get('error')}")
    
    # 4. Verificar dados específicos
    print("\n4️⃣ Verificando dados específicos...")
    
    # Buscar todos os alunos para comparar
    todos_alunos = supabase.table("alunos").select("""
        id, nome, id_turma,
        turmas!inner(nome_turma)
    """).execute()
    
    print(f"📊 Total de alunos no banco: {len(todos_alunos.data)}")
    
    # Agrupar por turma
    alunos_por_turma_real = {}
    for aluno in todos_alunos.data:
        turma_nome = aluno["turmas"]["nome_turma"]
        if turma_nome not in alunos_por_turma_real:
            alunos_por_turma_real[turma_nome] = []
        alunos_por_turma_real[turma_nome].append(aluno)
    
    print(f"📊 Distribuição real dos alunos por turma:")
    for turma, alunos in alunos_por_turma_real.items():
        print(f"   - {turma}: {len(alunos)} alunos")
        if turma in turmas_teste:
            print(f"     IDs dos alunos: {[a['id'] for a in alunos]}")
    
    print("\n" + "="*60)
    print("🏁 TESTE CONCLUÍDO")
    print("="*60)

if __name__ == "__main__":
    teste_busca_turmas() 