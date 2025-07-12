#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔄 ATUALIZADOR AUTOMÁTICO DE STATUS - MENSALIDADES
===================================================

Script para atualizar automaticamente o status das mensalidades de "A vencer" 
para "Atrasado" quando a data de vencimento for anterior à data atual.

Este script pode ser executado:
- Manualmente quando necessário
- Via cron job diariamente
- Antes de gerar relatórios
- Como parte de rotinas de manutenção

Uso:
    python atualizador_status_mensalidades.py
    python atualizador_status_mensalidades.py --verificar
    python atualizador_status_mensalidades.py --limite 500
"""

import sys
import argparse
from datetime import datetime, date
from typing import Dict

def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(
        description="Atualiza automaticamente os status das mensalidades"
    )
    parser.add_argument(
        "--verificar", 
        action="store_true", 
        help="Apenas verifica quantas mensalidades precisam ser atualizadas, sem executar a atualização"
    )
    parser.add_argument(
        "--limite", 
        type=int, 
        default=1000, 
        help="Limite de registros para processar por vez (padrão: 1000)"
    )
    parser.add_argument(
        "--silencioso", 
        action="store_true", 
        help="Executa sem output detalhado"
    )
    
    args = parser.parse_args()
    
    # Importar função após parser para permitir --help mesmo se houver problemas de import
    try:
        from funcoes_extrato_otimizadas import (
            atualizar_status_mensalidades_automatico, 
            verificar_mensalidades_precisam_atualizacao
        )
    except ImportError as e:
        print(f"❌ Erro ao importar módulos necessários: {e}")
        print("💡 Certifique-se de que o arquivo funcoes_extrato_otimizadas.py está disponível")
        sys.exit(1)
    
    # Header do script
    if not args.silencioso:
        print("🔄 ATUALIZADOR AUTOMÁTICO DE STATUS - MENSALIDADES")
        print("=" * 50)
        print(f"⏰ Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print()
    
    if args.verificar:
        # Modo verificação apenas
        if not args.silencioso:
            print("🔍 MODO VERIFICAÇÃO - Apenas verificando...")
        
        resultado = verificar_mensalidades_precisam_atualizacao()
        
        if resultado.get("success"):
            count = resultado.get("count", 0)
            
            if count > 0:
                print(f"⚠️  {count} mensalidades precisam ser atualizadas de 'A vencer' para 'Atrasado'")
                
                if not args.silencioso and count > 0:
                    print("\n📋 Mensalidades que precisam ser atualizadas:")
                    mensalidades = resultado.get("mensalidades", [])
                    
                    # Mostrar apenas as primeiras 10 para não poluir o output
                    for i, mensalidade in enumerate(mensalidades[:10], 1):
                        mes = mensalidade.get("mes_referencia", "N/A")
                        data_venc = mensalidade.get("data_vencimento", "N/A")
                        print(f"   {i}. {mes} - Vencimento: {data_venc}")
                    
                    if len(mensalidades) > 10:
                        print(f"   ... e mais {len(mensalidades) - 10} mensalidades")
                
                print(f"\n💡 Para executar a atualização, execute:")
                print(f"   python {sys.argv[0]}")
                
            else:
                print("✅ Todas as mensalidades estão com status correto!")
        else:
            print(f"❌ Erro na verificação: {resultado.get('error')}")
            sys.exit(1)
    
    else:
        # Modo atualização
        if not args.silencioso:
            print("🔄 EXECUTANDO ATUALIZAÇÃO AUTOMÁTICA...")
            print(f"📊 Limite por execução: {args.limite} registros")
            print()
        
        resultado = atualizar_status_mensalidades_automatico(limite_registros=args.limite)
        
        if resultado.get("success"):
            atualizadas = resultado.get("atualizadas", 0)
            total_encontradas = resultado.get("total_encontradas", 0)
            
            if atualizadas > 0:
                print(f"✅ {atualizadas} mensalidades atualizadas com sucesso!")
                
                if not args.silencioso:
                    print(f"📊 Total encontradas: {total_encontradas}")
                    print(f"📊 Total atualizadas: {atualizadas}")
                    
                    # Mostrar detalhes das mensalidades atualizadas
                    detalhes = resultado.get("detalhes", [])
                    if detalhes:
                        print("\n📋 Mensalidades atualizadas:")
                        for i, detalhe in enumerate(detalhes[:10], 1):
                            mes = detalhe.get("mes_referencia", "N/A")
                            data_venc = detalhe.get("data_vencimento", "N/A")
                            print(f"   {i}. {mes} - Vencimento: {data_venc} - Status: A vencer → Atrasado")
                        
                        if len(detalhes) > 10:
                            print(f"   ... e mais {len(detalhes) - 10} atualizações")
                
                # Verificar se há erros
                erros = resultado.get("erros", [])
                if erros:
                    print(f"\n⚠️  {len(erros)} erros encontrados:")
                    for erro in erros[:5]:
                        print(f"   • {erro}")
                    if len(erros) > 5:
                        print(f"   ... e mais {len(erros) - 5} erros")
            
            else:
                print("✅ Nenhuma mensalidade precisava ser atualizada - Todas em dia!")
                
                if not args.silencioso:
                    message = resultado.get("message", "")
                    if message:
                        print(f"💡 {message}")
        
        else:
            print(f"❌ Erro na atualização: {resultado.get('error')}")
            sys.exit(1)
    
    # Footer
    if not args.silencioso:
        print()
        print("=" * 50)
        print(f"✅ Operação concluída em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

def executar_atualizacao_simples() -> Dict:
    """
    Função simplificada para ser chamada por outros scripts
    
    Returns:
        Dict: Resultado da atualização
    """
    try:
        from funcoes_extrato_otimizadas import atualizar_status_mensalidades_automatico
        return atualizar_status_mensalidades_automatico()
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao executar atualização: {str(e)}",
            "atualizadas": 0
        }

if __name__ == "__main__":
    main() 