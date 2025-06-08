#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from supabase_functions import listar_alunos

def main():
    print("🎓 AUDITORIA RÁPIDA DE ALUNOS")
    print("=" * 40)
    
    # Total de alunos
    total = listar_alunos()
    print(f"📊 Total de alunos: {total.get('count', 0)}")
    
    # Alunos sem data de matrícula
    sem_matricula = listar_alunos(sem_data_matricula=True)
    print(f"❌ Sem data matrícula: {sem_matricula.get('count', 0)}")
    
    # Alunos sem valor de mensalidade
    sem_mensalidade = listar_alunos(sem_valor_mensalidade=True)
    print(f"❌ Sem valor mensalidade: {sem_mensalidade.get('count', 0)}")
    
    # Alunos sem dia de vencimento
    sem_vencimento = listar_alunos(sem_dia_vencimento=True)
    print(f"❌ Sem dia vencimento: {sem_vencimento.get('count', 0)}")
    
    print("\n🎯 RESUMO:")
    total_count = total.get('count', 0)
    problemas = sem_matricula.get('count', 0) + sem_mensalidade.get('count', 0) + sem_vencimento.get('count', 0)
    
    if total_count > 0:
        percentual_completo = ((total_count * 3 - problemas) / (total_count * 3)) * 100
        print(f"✅ Dados completos: {percentual_completo:.1f}%")
        print(f"❌ Dados faltantes: {100 - percentual_completo:.1f}%")
        
        if percentual_completo >= 80:
            status = "🟢 BOM"
        elif percentual_completo >= 50:
            status = "🟡 MÉDIO"
        else:
            status = "🔴 CRÍTICO"
        
        print(f"📊 Status: {status}")
    else:
        print("❌ Nenhum aluno encontrado")

if __name__ == "__main__":
    main() 