#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from supabase_functions import analisar_estatisticas_extrato

def main():
    print("🎯 VERIFICANDO ESTATÍSTICAS DO EXTRATO PIX")
    print("=" * 50)
    
    result = analisar_estatisticas_extrato()
    
    if not result.get("success"):
        print(f"❌ Erro: {result.get('error')}")
        return
    
    stats = result["estatisticas"]
    
    print(f"📊 Total de registros: {stats['total_registros']:,}")
    print(f"✅ Identificados: {stats['total_identificados']:,}")
    print(f"❌ Não identificados: {stats['total_nao_identificados']:,}")
    print(f"📈 Percentual identificado: {stats['percentual_identificacao']:.1f}%")
    print()
    print(f"💰 Valor total: R$ {stats['valor_total']:,.2f}")
    print(f"✅ Valor identificado: R$ {stats['valor_identificado']:,.2f}")
    print(f"❌ Valor não identificado: R$ {stats['valor_nao_identificado']:,.2f}")
    print()
    
    # Status visual
    if stats['percentual_identificacao'] >= 90:
        status = "🟢 EXCELENTE"
    elif stats['percentual_identificacao'] >= 70:
        status = "🟡 BOM"
    else:
        status = "🔴 NECESSITA MELHORIA"
    
    print(f"🎯 Status: {status}")

if __name__ == "__main__":
    main() 