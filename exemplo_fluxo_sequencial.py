#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exemplo do Fluxo Sequencial do Assistente Escolar IA
===================================================

Este script demonstra como a IA mantém contexto e executa operações 
em sequência conforme solicitado pelo usuário.
"""

from assistente_escolar_ia import AssistenteEscolarIA

def demonstrar_fluxo_sequencial():
    """Demonstra o fluxo sequencial de operações"""
    print("🎓 **DEMONSTRAÇÃO DO FLUXO SEQUENCIAL**")
    print("=" * 60)
    
    print("\n🚀 Inicializando assistente...")
    assistente = AssistenteEscolarIA(use_ai=True)
    
    # Simula uma conversa sequencial
    comandos_sequenciais = [
        # 1. Identificar responsáveis não cadastrados
        "Liste todos os responsáveis do extrato PIX que não estão cadastrados na tabela responsáveis",
        
        # 2. Se houvesse não cadastrados, cadastraria um (exemplo hipotético)
        # "cadastre Maria Silva com CPF 123.456.789-00 como mãe do aluno João Silva",
        
        # 3. Listar registros que já têm responsáveis cadastrados
        "Liste todos os registros em extrato_pix que estão cadastrados em responsaveis",
        
        # 4. Analisar estatísticas para acompanhar evolução
        "Analise as estatísticas do extrato PIX e me dê um resumo da situação atual"
    ]
    
    print(f"\n📝 Executando {len(comandos_sequenciais)} comandos em sequência...\n")
    
    for i, comando in enumerate(comandos_sequenciais, 1):
        print(f"\n{'='*60}")
        print(f"🔄 **PASSO {i}/{len(comandos_sequenciais)}**")
        print(f"💬 Usuário: {comando}")
        print("-" * 60)
        
        try:
            resposta = assistente.send_message_to_ai(comando)
            print(f"🤖 Assistente:\n{resposta}")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
        
        print("\n" + "⏱️  Aguardando próximo comando...")
    
    print(f"\n{'='*60}")
    print("✅ **DEMONSTRAÇÃO CONCLUÍDA!**")
    print("\n💡 **O que foi demonstrado:**")
    print("1. 🧠 Contexto mantido entre comandos")
    print("2. 🔄 Execução sequencial de operações")
    print("3. 📊 Análise progressiva dos dados")
    print("4. 🤖 Respostas inteligentes baseadas em resultados anteriores")
    
    print(f"\n🎯 **Fluxo típico de uso:**")
    print("1. Identificar → 2. Cadastrar → 3. Vincular → 4. Registrar Pagamentos")

def demonstrar_comando_cadastro():
    """Demonstra um comando de cadastro com vinculação"""
    print("\n" + "="*60)
    print("📝 **EXEMPLO DE COMANDO DE CADASTRO + VINCULAÇÃO**")
    print("="*60)
    
    print("""
🗣️ **Comando de exemplo:**
"cadastre Maria Santos com CPF 123.456.789-00 como mãe do aluno João Silva"

🔄 **O que aconteceria:**
1. 🔍 IA identificaria os parâmetros:
   - Nome responsável: "Maria Santos"
   - CPF: "123.456.789-00"
   - Tipo relação: "mãe"
   - Nome aluno: "João Silva"

2. 🎯 IA executaria sequencialmente:
   - buscar_aluno_por_nome("João Silva")
   - cadastrar_responsavel_e_vincular_aluno(...)
   
3. ✅ IA confirmaria:
   - "Responsável Maria Santos cadastrado com sucesso!"
   - "Vinculado como mãe do aluno João Silva"
   - "ID do responsável: RES_XXXXXX"

4. 🤖 IA aguardaria próximas instruções mantendo contexto
""")

if __name__ == "__main__":
    try:
        print("🎓 **SISTEMA DE FLUXO SEQUENCIAL - ASSISTENTE ESCOLAR IA**")
        print("Este exemplo demonstra como a IA mantém contexto entre comandos.\n")
        
        # Pergunta se quer executar a demonstração completa
        resposta = input("🚀 Executar demonstração completa? (s/n): ").strip().lower()
        
        if resposta == 's':
            demonstrar_fluxo_sequencial()
        else:
            demonstrar_comando_cadastro()
            
        print(f"\n💡 **Para usar o assistente interativo:**")
        print("   python assistente_escolar_ia.py")
        
    except Exception as e:
        print(f"❌ Erro durante demonstração: {str(e)}")
        print("💡 Verifique se as configurações estão corretas no .env") 