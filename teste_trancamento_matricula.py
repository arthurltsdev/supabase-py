#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔒 TESTE DE TRANCAMENTO DE MATRÍCULA
===================================

Demonstra a funcionalidade de trancamento de matrícula implementada:
- Listar mensalidades que serão canceladas
- Trancar matrícula do aluno
- Verificar alterações no banco de dados
"""

from models.pedagogico import (
    buscar_alunos_para_dropdown,
    buscar_informacoes_completas_aluno,
    listar_mensalidades_para_cancelamento,
    trancar_matricula_aluno
)
from models.base import formatar_data_br
from datetime import datetime, date

def demonstrar_trancamento():
    """Demonstra o processo completo de trancamento de matrícula"""
    
    print("🎓 DEMONSTRAÇÃO - TRANCAMENTO DE MATRÍCULA")
    print("=" * 50)
    
    # 1. Buscar alunos disponíveis
    print("\n1️⃣ Buscando alunos disponíveis...")
    resultado_busca = buscar_alunos_para_dropdown("Ana")  # Exemplo: buscar por "Ana"
    
    if not resultado_busca.get("success") or not resultado_busca.get("opcoes"):
        print("❌ Nenhum aluno encontrado para demonstração")
        return
    
    # Selecionar primeiro aluno encontrado
    aluno_exemplo = resultado_busca["opcoes"][0]
    id_aluno = aluno_exemplo["id"]
    nome_aluno = aluno_exemplo["nome"]
    
    print(f"✅ Aluno selecionado: {nome_aluno} (ID: {id_aluno})")
    
    # 2. Buscar informações completas do aluno
    print(f"\n2️⃣ Buscando informações completas de {nome_aluno}...")
    info_resultado = buscar_informacoes_completas_aluno(id_aluno)
    
    if not info_resultado.get("success"):
        print(f"❌ Erro ao buscar informações: {info_resultado.get('error')}")
        return
    
    aluno = info_resultado["aluno"]
    mensalidades = info_resultado["mensalidades"]
    
    print(f"📊 Situação atual: {aluno.get('situacao', 'ativo')}")
    print(f"💰 Valor mensalidade: R$ {aluno['valor_mensalidade']:.2f}")
    print(f"📅 Dia vencimento: {aluno.get('dia_vencimento', 'N/A')}")
    print(f"📋 Total de mensalidades: {len(mensalidades)}")
    
    # Verificar se já está trancado
    if aluno.get('situacao') == 'trancado':
        print(f"⚠️ Este aluno já está com matrícula trancada!")
        if aluno.get('data_saida'):
            print(f"📅 Data de saída: {formatar_data_br(aluno['data_saida'])}")
        if aluno.get('motivo_saida'):
            print(f"📝 Motivo: {aluno['motivo_saida']}")
        return
    
    # 3. Simular data de saída
    data_saida_exemplo = "2025-07-15"  # Data de exemplo
    print(f"\n3️⃣ Simulando trancamento com data de saída: {formatar_data_br(data_saida_exemplo)}")
    
    # 4. Listar mensalidades que serão canceladas
    print(f"\n4️⃣ Calculando mensalidades que serão canceladas...")
    preview_resultado = listar_mensalidades_para_cancelamento(id_aluno, data_saida_exemplo)
    
    if not preview_resultado.get("success"):
        print(f"❌ Erro ao calcular mensalidades: {preview_resultado.get('error')}")
        return
    
    mensalidades_cancelar = preview_resultado["mensalidades"]
    
    if mensalidades_cancelar:
        print(f"📊 {len(mensalidades_cancelar)} mensalidades serão canceladas:")
        valor_total = 0
        for i, mens in enumerate(mensalidades_cancelar, 1):
            print(f"   {i}. {mens['mes_referencia']} - R$ {mens['valor']:.2f} (vence em {formatar_data_br(mens['data_vencimento'])})")
            valor_total += mens['valor']
        print(f"💰 Valor total a ser cancelado: R$ {valor_total:,.2f}")
    else:
        print("✅ Nenhuma mensalidade futura para cancelar")
    
    # 5. Perguntar se deseja continuar com o trancamento
    print(f"\n5️⃣ Processo de trancamento preparado!")
    resposta = input("❓ Deseja realmente trancar a matrícula? (s/N): ").strip().lower()
    
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Trancamento cancelado pelo usuário")
        return
    
    # 6. Executar trancamento
    print(f"\n6️⃣ Executando trancamento de matrícula...")
    resultado_trancamento = trancar_matricula_aluno(
        id_aluno=id_aluno,
        data_saida=data_saida_exemplo,
        motivo_saida="trancamento"
    )
    
    if resultado_trancamento.get("success"):
        print("✅ MATRÍCULA TRANCADA COM SUCESSO!")
        print(f"👨‍🎓 Aluno: {resultado_trancamento['aluno_nome']}")
        print(f"📅 Data de saída: {formatar_data_br(resultado_trancamento['data_saida'])}")
        print(f"📝 Motivo: {resultado_trancamento['motivo_saida']}")
        print(f"📊 Mensalidades canceladas: {resultado_trancamento['mensalidades_canceladas']}")
        
        if resultado_trancamento.get('erros_cancelamento'):
            print(f"⚠️ Avisos: {resultado_trancamento.get('aviso')}")
            for erro in resultado_trancamento['erros_cancelamento']:
                print(f"   - {erro}")
        
        # 7. Verificar alterações
        print(f"\n7️⃣ Verificando alterações no banco de dados...")
        info_apos = buscar_informacoes_completas_aluno(id_aluno)
        
        if info_apos.get("success"):
            aluno_apos = info_apos["aluno"]
            mensalidades_apos = info_apos["mensalidades"]
            
            print(f"📊 Nova situação: {aluno_apos.get('situacao')}")
            print(f"📅 Data de saída registrada: {formatar_data_br(aluno_apos.get('data_saida'))}")
            print(f"📝 Motivo registrado: {aluno_apos.get('motivo_saida')}")
            
            # Contar mensalidades canceladas
            canceladas = [m for m in mensalidades_apos if m['status'] == 'Cancelado']
            print(f"🚫 Mensalidades canceladas no sistema: {len(canceladas)}")
            
            if canceladas:
                print("📋 Lista de mensalidades canceladas:")
                for mens in canceladas:
                    print(f"   • {mens['mes_referencia']} - Status: {mens['status']}")
        
    else:
        print(f"❌ ERRO NO TRANCAMENTO: {resultado_trancamento.get('error')}")

def listar_alunos_trancados():
    """Lista alunos com matrícula trancada"""
    
    print("\n🔒 ALUNOS COM MATRÍCULA TRANCADA")
    print("=" * 40)
    
    try:
        from models.base import supabase
        
        # Buscar alunos trancados
        response = supabase.table("alunos").select("""
            id, nome, situacao, data_saida, motivo_saida,
            turmas!inner(nome_turma)
        """).eq("situacao", "trancado").execute()
        
        if response.data:
            print(f"📊 {len(response.data)} aluno(s) com matrícula trancada:")
            
            for i, aluno in enumerate(response.data, 1):
                print(f"\n{i}. {aluno['nome']}")
                print(f"   🎓 Turma: {aluno['turmas']['nome_turma']}")
                print(f"   📅 Data saída: {formatar_data_br(aluno.get('data_saida', ''))}")
                print(f"   📝 Motivo: {aluno.get('motivo_saida', 'N/A')}")
        else:
            print("✅ Nenhum aluno com matrícula trancada encontrado")
            
    except Exception as e:
        print(f"❌ Erro ao buscar alunos trancados: {e}")

if __name__ == "__main__":
    try:
        print("🚀 Iniciando demonstração do sistema de trancamento de matrícula...\n")
        
        # Listar alunos já trancados
        listar_alunos_trancados()
        
        print("\n" + "="*60)
        
        # Demonstrar processo de trancamento
        demonstrar_trancamento()
        
        print("\n✅ Demonstração concluída!")
        
    except KeyboardInterrupt:
        print("\n❌ Demonstração interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na demonstração: {e}") 