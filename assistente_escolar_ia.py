#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 ASSISTENTE ESCOLAR IA - SUPABASE EDITION
==========================================

Assistente inteligente para gestão escolar usando Supabase como backend.
- ✅ OpenAI Function Calling integrado com Supabase
- ✅ Identificação automática de responsáveis não cadastrados  
- ✅ Filtragem avançada por turma, nome e outros critérios
- ✅ Cadastro inteligente de responsáveis e alunos
- ✅ Vinculação automática de relacionamentos

👉 Uso:
    python assistente_escolar_ia.py
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from executor_unificado import executar_function
from datetime import datetime

# 🌱 Carregar variáveis de ambiente
load_dotenv()

# 🔑 Configuração da OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY não encontrada no arquivo .env")
    print("💡 Para usar IA, adicione sua chave OpenAI no arquivo .env")
    print("💡 Você ainda pode usar as funções manualmente")

try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except ImportError:
    print("⚠️ OpenAI não instalado. Execute: pip install openai")
    client = None
except Exception as e:
    print(f"❌ Erro ao inicializar OpenAI: {e}")
    client = None

# ==========================================================
# 🔧 Carregar Tools
# ==========================================================

def load_tools() -> List[Dict[str, Any]]:
    """Carrega tools do functions.json"""
    try:
        with open("functions.json", encoding="utf-8") as f:
            data = json.load(f)
            tools = data["tools"]
            
            print(f"✅ Carregadas {len(tools)} funções")
            return tools
    except Exception as e:
        print(f"❌ Erro ao carregar functions.json: {e}")
        return []

# ==========================================================
# 🧠 Sistema de Prompt Avançado
# ==========================================================

SYSTEM_PROMPT = """
🎓 Você é um Assistente Escolar IA especializado em gestão educacional.

🎯 MISSÃO:
- Analisar extratos PIX e identificar responsáveis não cadastrados
- Gerenciar alunos, responsáveis e relacionamentos no Supabase
- Facilitar cadastros e vinculações de forma inteligente
- Fornecer relatórios e análises financeiras educacionais

⚡ CAPACIDADES ESPECIAIS:
- Identificação automática de responsáveis não cadastrados no extrato PIX
- Filtragem avançada por turma, nome, ausência de dados
- Cadastro inteligente com validação de dados
- Vinculação automática de relacionamentos familiares
- Análise contextual de padrões de pagamento

🔧 DIRETRIZES DE EXECUÇÃO:
1. Sempre confirme antes de cadastrar ou modificar dados importantes
2. Use múltiplas funções quando necessário para obter contexto completo
3. Forneça resumos claros após operações complexas
4. Identifique e sugira correções para dados inconsistentes
5. Mantenha foco na experiência do usuário educacional

📊 PADRÕES DE RESPOSTA:
- Português brasileiro profissional e acessível
- Emojis para clareza visual e organização
- Tabelas e listas organizadas para dados
- Confirmações antes de ações críticas
- Sugestões proativas baseadas em análises

💡 INTELIGÊNCIA CONTEXTUAL:
- Identifique padrões de nomes similares entre responsáveis e alunos
- Detecte inconsistências em dados de matrícula e vencimento
- Sugira relacionamentos familiares baseados em nomes
- Analise padrões de pagamento para identificar anomalias

🔐 SEGURANÇA:
- Nunca modifique dados sem confirmação explícita
- Valide CPFs, datas e outros dados críticos
- Mantenha privacidade de informações sensíveis
"""

# ==========================================================
# 🤖 Assistente Escolar IA
# ==========================================================

class AssistenteEscolarIA:
    def __init__(self, use_ai: bool = True):
        self.tools = load_tools()
        self.conversation_history = []
        self.use_ai = use_ai and client is not None
        self.max_history = 25  # Controle de contexto aumentado para melhor sequência
        
        # Validação das ferramentas
        if not self.tools:
            raise ValueError("❌ Nenhuma ferramenta carregada. Verifique functions.json")
            
        print(f"🚀 Assistente inicializado com {len(self.tools)} ferramentas")
        if not self.use_ai:
            print("⚠️ Modo manual ativado (sem IA)")

    def add_to_history(self, role: str, content: str):
        """Adiciona mensagem ao histórico da conversa"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        
        # Mantém apenas as últimas mensagens
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def format_welcome_message(self) -> str:
        """Mensagem de boas-vindas personalizada"""
        ai_status = "✅ IA ATIVADA" if self.use_ai else "⚠️ MODO MANUAL"
        
        return f"""
🎓 **ASSISTENTE ESCOLAR IA - SUPABASE EDITION**
==============================================

{ai_status}

🚀 **FUNCIONALIDADES PRINCIPAIS:**
- 🔍 Identificar responsáveis não cadastrados no extrato PIX
- 👥 Gerenciar alunos e responsáveis com filtros avançados
- 🔗 Vincular relacionamentos familiares automaticamente
- 📊 Analisar estatísticas financeiras e educacionais
- 📝 Cadastrar novos alunos e responsáveis

💡 **COMANDOS INTELIGENTES:**
• "Liste responsáveis do extrato PIX não cadastrados"
• "Mostre alunos da turma Infantil III sem data de matrícula" 
• "Cadastre responsável João Silva como pai do aluno Maria Silva"
• "Analise estatísticas do extrato PIX"
• "Processe automaticamente responsáveis não cadastrados"

🎯 **COMANDOS MANUAIS:**
• 'menu' - Mostrar menu de funções
• 'ajuda' - Mostrar comandos disponíveis
• 'sair' - Encerrar sessão

👉 **Como posso ajudar na gestão escolar hoje?**
"""

    def show_manual_menu(self) -> str:
        """Mostra menu manual de funções"""
        return """
📋 **MENU DE FUNÇÕES DISPONÍVEIS:**

🔍 **ANÁLISE E IDENTIFICAÇÃO:**
1. Identificar responsáveis não cadastrados
2. Analisar estatísticas do extrato PIX
3. Listar pagamentos não identificados

👥 **CONSULTAS:**
4. Listar responsáveis
5. Listar alunos
6. Listar turmas
7. Buscar aluno por nome

📝 **CADASTROS:**
8. Cadastrar responsável
9. Vincular aluno a responsável

🚀 **PROCESSAMENTO:**
10. Processar responsáveis do extrato automaticamente

Digite o número da função ou use comandos em linguagem natural.
"""

    def execute_manual_function(self, choice: str) -> str:
        """Executa função manual baseada na escolha do usuário"""
        try:
            choice = choice.strip()
            
            if choice == "1":
                resultado = executar_function("identificar_responsaveis_nao_cadastrados")
                return self.format_response_for_display(resultado, "identificar_responsaveis_nao_cadastrados")
            
            elif choice == "2":
                resultado = executar_function("analisar_estatisticas_extrato")
                return self.format_response_for_display(resultado, "analisar_estatisticas_extrato")
            
            elif choice == "3":
                resultado = executar_function("listar_pagamentos_nao_identificados", formato_resumido=True)
                return self.format_response_for_display(resultado, "listar_pagamentos_nao_identificados")
            
            elif choice == "4":
                nome = input("🔍 Nome para filtrar (deixe vazio para todos): ").strip()
                if nome:
                    resultado = executar_function("listar_responsaveis", filtro_nome=nome)
                else:
                    resultado = executar_function("listar_responsaveis")
                return self.format_response_for_display(resultado, "listar_responsaveis")
            
            elif choice == "5":
                print("🔍 Filtros disponíveis:")
                nome = input("Nome do aluno (deixe vazio para ignorar): ").strip()
                turma = input("Turma (deixe vazio para ignorar): ").strip()
                sem_matricula = input("Mostrar apenas sem data de matrícula? (s/n): ").strip().lower() == 's'
                
                filtros = {}
                if nome:
                    filtros["filtro_nome"] = nome
                if turma:
                    filtros["filtro_turma"] = turma
                if sem_matricula:
                    filtros["sem_data_matricula"] = True
                
                resultado = executar_function("listar_alunos", **filtros)
                return self.format_response_for_display(resultado, "listar_alunos")
            
            elif choice == "6":
                resultado = executar_function("listar_turmas")
                return self.format_response_for_display(resultado, "listar_turmas")
            
            elif choice == "7":
                nome = input("🔍 Nome do aluno para buscar: ").strip()
                if not nome:
                    return "❌ Nome é obrigatório para busca"
                resultado = executar_function("buscar_aluno_por_nome", nome=nome)
                return self.format_response_for_display(resultado, "buscar_aluno_por_nome")
            
            elif choice == "8":
                nome = input("📝 Nome completo do responsável: ").strip()
                if not nome:
                    return "❌ Nome é obrigatório"
                
                cpf = input("CPF (opcional): ").strip() or None
                telefone = input("Telefone (opcional): ").strip() or None
                email = input("Email (opcional): ").strip() or None
                endereco = input("Endereço (opcional): ").strip() or None
                tipo_relacao = input("Tipo de relação (pai, mãe, avô, etc.): ").strip() or None
                
                resultado = executar_function("cadastrar_responsavel_completo",
                                            nome=nome, cpf=cpf, telefone=telefone,
                                            email=email, endereco=endereco, tipo_relacao=tipo_relacao)
                return self.format_response_for_display(resultado, "cadastrar_responsavel_completo")
            
            elif choice == "9":
                id_aluno = input("📝 ID do aluno: ").strip()
                id_responsavel = input("ID do responsável: ").strip()
                tipo_relacao = input("Tipo de relação (pai, mãe, etc.): ").strip()
                
                if not id_aluno or not id_responsavel:
                    return "❌ ID do aluno e responsável são obrigatórios"
                
                resultado = executar_function("vincular_aluno_responsavel",
                                            id_aluno=id_aluno, id_responsavel=id_responsavel,
                                            tipo_relacao=tipo_relacao, responsavel_financeiro=True)
                return self.format_response_for_display(resultado, "vincular_aluno_responsavel")
            
            elif choice == "10":
                print("🚀 ATENÇÃO: Isso irá cadastrar automaticamente todos os responsáveis não cadastrados do extrato PIX!")
                confirmacao = input("Confirma? (s/n): ").strip().lower()
                if confirmacao == 's':
                    resultado = executar_function("processar_responsaveis_extrato_pix")
                    return self.format_response_for_display(resultado, "processar_responsaveis_extrato_pix")
                else:
                    return "❌ Operação cancelada pelo usuário"
            
            else:
                return "❌ Opção inválida. Digite 'menu' para ver as opções disponíveis."
                
        except Exception as e:
            return f"❌ Erro ao executar função: {str(e)}"

    def format_response_for_display(self, resultado: Dict[str, Any], function_name: str) -> str:
        """Formata resposta para exibição amigável"""
        try:
            if resultado.get("status") == "erro" or not resultado.get("success", True):
                return f"❌ Erro: {resultado.get('erro', resultado.get('error', 'Erro desconhecido'))}"
            
            # Formatação específica por função
            if function_name == "identificar_responsaveis_nao_cadastrados":
                count = resultado.get("count", 0)
                detalhes = resultado.get("detalhes", [])
                if count == 0:
                    return "✅ Todos os responsáveis do extrato PIX já estão cadastrados!"
                
                resposta = f"📊 **{count} RESPONSÁVEIS NÃO CADASTRADOS ENCONTRADOS:**\n\n"
                for i, detalhe in enumerate(detalhes[:20], 1):  # Limita a 20
                    nome = detalhe.get("nome", "Nome não disponível")
                    qtd = detalhe.get("quantidade_pagamentos", 0)
                    valor = detalhe.get("valor_total", 0)
                    resposta += f"{i:2d}. {nome}\n"
                    resposta += f"    📄 {qtd} pagamento(s) • 💰 R$ {valor:.2f}\n\n"
                
                if count > 20:
                    resposta += f"... e mais {count - 20} responsáveis\n\n"
                
                resposta += "💡 **Dica:** Use 'processar responsáveis automaticamente' para cadastrá-los"
                return resposta
            
            elif function_name == "analisar_estatisticas_extrato":
                stats = resultado.get("estatisticas", {})
                total = stats.get("total_registros", 0)
                identificados = stats.get("total_identificados", 0)
                percentual = stats.get("percentual_identificacao", 0)
                valor_total = stats.get("valor_total", 0)
                valor_nao_identificado = stats.get("valor_nao_identificado", 0)
                
                return f"""📊 **ESTATÍSTICAS DO EXTRATO PIX:**

📈 **Registros:**
• Total de registros: {total:,}
• Identificados: {identificados:,}
• Percentual identificado: {percentual:.1f}%

💰 **Valores:**
• Valor total: R$ {valor_total:,.2f}
• Valor identificado: R$ {(valor_total - valor_nao_identificado):,.2f}
• Valor não identificado: R$ {valor_nao_identificado:,.2f}

📊 **Status:** {'🟢 Boa identificação' if percentual > 70 else '🟡 Identificação média' if percentual > 40 else '🔴 Baixa identificação'}"""
            
            elif function_name == "processar_responsaveis_extrato_pix":
                total_cadastrados = resultado.get("total_cadastrados", 0)
                if total_cadastrados == 0:
                    return "ℹ️ Nenhum responsável novo foi cadastrado (todos já estavam no sistema)"
                
                return f"🚀 **{total_cadastrados} responsáveis cadastrados com sucesso!**\n💡 Execute 'analisar estatísticas' para ver o novo status!"
            
            # Formatação genérica para outras funções
            else:
                count = resultado.get("count", len(resultado.get("data", [])))
                return f"✅ Operação executada com sucesso!\n📊 {count} registro(s) processado(s)"
        
        except Exception as e:
            return f"❌ Erro ao formatar resposta: {str(e)}"

    def send_message_to_ai(self, user_message: str) -> str:
        """Envia mensagem para IA e processa resposta"""
        if not self.use_ai:
            return "❌ IA não disponível. Use comandos manuais ou configure OPENAI_API_KEY"
        
        try:
            # Adiciona mensagem do usuário ao histórico
            self.add_to_history("user", user_message)
            
            # Prepara mensagens para a API incluindo histórico
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(self.conversation_history)
            
            # Faz chamada para OpenAI
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.2,  # Reduzido para mais consistência
                max_tokens=4000
            )
            
            return self.handle_ai_response(response)
                
        except Exception as e:
            return f"❌ Erro na comunicação com IA: {str(e)}"

    def handle_ai_response(self, response) -> str:
        """Trata resposta da IA"""
        try:
            message = response.choices[0].message
            
            # Resposta sem tool calls
            if not message.tool_calls:
                response_content = message.content
                self.add_to_history("assistant", response_content)
                return response_content
            
            # Resposta com tool calls
            return self.handle_tool_calls(message)
            
        except Exception as e:
            return f"❌ Erro ao processar resposta da IA: {str(e)}"

    def handle_tool_calls(self, message) -> str:
        """Trata chamadas de funções da IA seguindo o padrão OpenAI Function Calling"""
        try:
            # Adiciona mensagem do assistente com tool calls ao histórico
            tool_calls_data = []
            for tool_call in message.tool_calls:
                tool_calls_data.append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })
            
            assistant_message = {
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls_data
            }
            self.conversation_history.append(assistant_message)
            
            # Execução das funções
            print(f"🔧 Executando {len(message.tool_calls)} função(ões)...")
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    print(f"⚡ Executando: {function_name}")
                    
                    # Execução da função
                    function_response = executar_function(function_name, **arguments)
                    
                    # Adiciona resultado como mensagem tool ao histórico
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_response, ensure_ascii=False, default=str)
                    }
                    self.conversation_history.append(tool_message)
                    
                    print(f"✅ {function_name} executada")
                    
                except Exception as e:
                    error_response = {"erro": f"Erro na função {function_name}: {str(e)}"}
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(error_response, ensure_ascii=False, default=str)
                    }
                    self.conversation_history.append(tool_message)
                    print(f"❌ Erro em {function_name}: {str(e)}")
            
            # Solicita resposta final da IA baseada nos resultados
            try:
                follow_up_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history[-20:],
                    temperature=0.2,
                    max_tokens=4000
                )
                
                final_content = follow_up_response.choices[0].message.content
                self.add_to_history("assistant", final_content)
                
                return final_content
                
            except Exception as api_error:
                print(f"⚠️ Erro na IA após executar funções: {str(api_error)}")
                
                # Recuperação manual - cria resposta baseada nos resultados
                recovery_message = "✅ **Funções executadas com sucesso!**\n\n"
                recovery_message += "💡 Use 'estatisticas' ou 'identificar' para verificar os resultados.\n"
                recovery_message += "📝 Posso ajudar com mais alguma operação?"
                
                self.add_to_history("assistant", recovery_message)
                return recovery_message
                
        except Exception as e:
            return f"❌ Erro ao processar chamadas de função: {str(e)}"

    def show_help(self) -> str:
        """Mostra comandos de ajuda"""
        ai_commands = """
🤖 **COMANDOS COM IA:**
• "Liste responsáveis não cadastrados no extrato PIX"
• "Mostre alunos da turma Infantil III sem data de matrícula"
• "Cadastre responsável João Silva como pai da aluna Maria Silva"
• "Analise estatísticas do extrato PIX e sugira ações"
• "Processe automaticamente todos os responsáveis não identificados"
• "Mostre responsáveis com nome Silva"
• "Liste alunos sem valor de mensalidade definido"
""" if self.use_ai else ""
        
        return f"""
🆘 **COMANDOS DISPONÍVEIS:**
{ai_commands}
📋 **COMANDOS MANUAIS:**
• 'menu' - Menu de funções disponíveis
• 'identificar' - Responsáveis não cadastrados
• 'estatisticas' - Análise do extrato PIX
• 'responsaveis' - Listar responsáveis
• 'alunos' - Listar alunos
• 'turmas' - Listar turmas disponíveis

🔧 **UTILITÁRIOS:**
• 'ajuda' / 'help' - Esta mensagem
• 'sair' / 'exit' - Encerrar sessão
• 'limpar' - Limpar histórico de conversa

💡 **Dicas:**
- Use linguagem natural com a IA
- Combine múltiplas operações em uma solicitação
- Seja específico com filtros e critérios
"""

    def run(self):
        """Loop principal da aplicação"""
        print(self.format_welcome_message())
        
        while True:
            try:
                user_input = input("\n💬 Você: ").strip()
                
                # Comandos especiais
                if user_input.lower() in ["sair", "exit", "quit"]:
                    print("\n👋 Encerrando sessão. Até logo!")
                    break
                    
                elif user_input.lower() in ["ajuda", "help"]:
                    print(self.show_help())
                    continue
                    
                elif user_input.lower() == "menu":
                    print(self.show_manual_menu())
                    continue
                
                elif user_input.lower() in ["identificar", "1"]:
                    print("\n🔄 Processando...")
                    response = self.execute_manual_function("1")
                    print(f"\n📊 Resultado:\n{response}")
                    continue
                
                elif user_input.lower() in ["estatisticas", "2"]:
                    print("\n🔄 Processando...")
                    response = self.execute_manual_function("2")
                    print(f"\n📊 Resultado:\n{response}")
                    continue
                
                elif user_input.isdigit() and 1 <= int(user_input) <= 10:
                    print("\n🔄 Processando...")
                    response = self.execute_manual_function(user_input)
                    print(f"\n📊 Resultado:\n{response}")
                    continue
                    
                elif not user_input:
                    print("💭 Por favor, digite uma pergunta, comando ou número do menu.")
                    continue
                
                # Processamento com IA ou manual
                print("\n🔄 Processando...")
                if self.use_ai:
                    response = self.send_message_to_ai(user_input)
                else:
                    response = "🤖 IA não disponível. Use 'menu' para funções manuais ou configure OPENAI_API_KEY."
                
                print(f"\n🤖 Assistente:\n{response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Encerrando por interrupção. Até logo!")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {str(e)}")
                continue

# ==========================================================
# 🚀 Função Principal
# ==========================================================

def main():
    """Função principal"""
    try:
        print("🎓 Inicializando Assistente Escolar IA...")
        
        assistente = AssistenteEscolarIA(use_ai=True)
        assistente.run()
        
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")

if __name__ == "__main__":
    main()
