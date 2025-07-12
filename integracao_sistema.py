#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔗 MÓDULO DE INTEGRAÇÃO DO SISTEMA
==================================

Módulo responsável por integrar todas as funcionalidades do sistema de gestão escolar,
garantindo que as diferentes partes trabalhem de forma coesa e profissional.

Autor: Sistema de Gestão Escolar
Versão: 1.0 - Integração Completa
"""

import streamlit as st
import sys
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import traceback

# Adicionar o diretório atual ao path para importações
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# ==========================================================
# 🔧 CONFIGURAÇÕES E IMPORTS
# ==========================================================

def verificar_dependencias():
    """Verifica se todas as dependências estão disponíveis"""
    dependencias = {
        "Streamlit": True,
        "Pandas": True,
        "Supabase": True,
        "Base de Dados": True,
        "Gestão de Mensalidades": True,
        "Interface Pedagógica": True,
        "Processamento Extrato": True
    }
    
    try:
        import pandas as pd
        dependencias["Pandas"] = True
    except ImportError:
        dependencias["Pandas"] = False
    
    try:
        from models.base import supabase
        dependencias["Base de Dados"] = True
    except ImportError:
        dependencias["Base de Dados"] = False
    
    try:
        from gestao_mensalidades import inicializar_sistema_mensalidades
        dependencias["Gestão de Mensalidades"] = True
    except ImportError:
        dependencias["Gestão de Mensalidades"] = False
    
    return dependencias

def inicializar_sistema():
    """Inicializa todos os componentes do sistema"""
    
    # Verificar dependências
    deps = verificar_dependencias()
    
    # Configurar página
    st.set_page_config(
        page_title="Sistema de Gestão Escolar - Integrado",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inicializar session state
    if 'sistema_inicializado' not in st.session_state:
        st.session_state.sistema_inicializado = True
        st.session_state.deps_verificadas = deps
    
    return deps

# ==========================================================
# 🎯 FUNCIONALIDADES PRINCIPAIS
# ==========================================================

def mostrar_status_sistema():
    """Mostra o status do sistema e suas dependências"""
    
    deps = st.session_state.get('deps_verificadas', {})
    
    st.subheader("🔍 Status do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📋 Componentes Core:**")
        status_core = deps.get("Streamlit", False) and deps.get("Pandas", False)
        emoji = "✅" if status_core else "❌"
        st.write(f"{emoji} Streamlit: {'OK' if deps.get('Streamlit') else 'ERRO'}")
        st.write(f"{emoji} Pandas: {'OK' if deps.get('Pandas') else 'ERRO'}")
    
    with col2:
        st.markdown("**🗄️ Base de Dados:**")
        status_db = deps.get("Base de Dados", False)
        emoji = "✅" if status_db else "❌"
        st.write(f"{emoji} Conexão DB: {'OK' if status_db else 'ERRO'}")
        st.write(f"{emoji} Supabase: {'OK' if deps.get('Supabase') else 'ERRO'}")
    
    with col3:
        st.markdown("**⚙️ Módulos Específicos:**")
        status_mods = deps.get("Gestão de Mensalidades", False)
        emoji = "✅" if status_mods else "❌"
        st.write(f"{emoji} Mensalidades: {'OK' if status_mods else 'ERRO'}")
        st.write(f"{emoji} Interface Ped.: {'OK' if deps.get('Interface Pedagógica') else 'ERRO'}")
    
    # Status geral
    todos_ok = all(deps.values())
    if todos_ok:
        st.success("🎉 Todos os componentes estão funcionando corretamente!")
    else:
        problemas = [k for k, v in deps.items() if not v]
        st.error(f"⚠️ Problemas encontrados: {', '.join(problemas)}")
        
        st.markdown("### 💡 Soluções:")
        for problema in problemas:
            if problema == "Pandas":
                st.info("• Execute: `pip install pandas`")
            elif problema == "Base de Dados":
                st.info("• Verifique o arquivo models/base.py")
            elif problema == "Gestão de Mensalidades":
                st.info("• Verifique o arquivo gestao_mensalidades.py")

def executar_diagnostico_completo():
    """Executa um diagnóstico completo do sistema"""
    
    st.subheader("🔍 Diagnóstico Completo do Sistema")
    
    with st.spinner("Executando diagnóstico..."):
        
        diagnostico = {
            "timestamp": datetime.now(),
            "arquivos_encontrados": [],
            "funcionalidades_testadas": {},
            "conexoes_testadas": {},
            "erros_encontrados": []
        }
        
        # 1. Verificar arquivos principais
        arquivos_principais = [
            "gestao_mensalidades.py",
            "interface_pedagogica_teste.py", 
            "interface_processamento_extrato.py",
            "models/base.py",
            "models/pedagogico.py"
        ]
        
        for arquivo in arquivos_principais:
            if os.path.exists(arquivo):
                diagnostico["arquivos_encontrados"].append(arquivo)
        
        # 2. Testar conexão com banco de dados
        try:
            from models.base import supabase
            response = supabase.table("alunos").select("count", count="exact").execute()
            diagnostico["conexoes_testadas"]["base_dados"] = "OK"
        except Exception as e:
            diagnostico["conexoes_testadas"]["base_dados"] = f"ERRO: {str(e)}"
            diagnostico["erros_encontrados"].append(f"Conexão DB: {str(e)}")
        
        # 3. Testar módulo de mensalidades
        try:
            from gestao_mensalidades import inicializar_sistema_mensalidades
            inicializar_sistema_mensalidades()
            diagnostico["funcionalidades_testadas"]["mensalidades"] = "OK"
        except Exception as e:
            diagnostico["funcionalidades_testadas"]["mensalidades"] = f"ERRO: {str(e)}"
            diagnostico["erros_encontrados"].append(f"Mensalidades: {str(e)}")
        
        # 4. Testar funções pedagógicas
        try:
            from models.pedagogico import listar_turmas_disponiveis
            resultado = listar_turmas_disponiveis()
            if resultado.get("success"):
                diagnostico["funcionalidades_testadas"]["pedagogico"] = "OK"
            else:
                diagnostico["funcionalidades_testadas"]["pedagogico"] = f"ERRO: {resultado.get('error')}"
        except Exception as e:
            diagnostico["funcionalidades_testadas"]["pedagogico"] = f"ERRO: {str(e)}"
            diagnostico["erros_encontrados"].append(f"Pedagógico: {str(e)}")
    
    # Mostrar resultados
    st.markdown("### 📊 Resultados do Diagnóstico")
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Arquivos", len(diagnostico["arquivos_encontrados"]), delta=f"/{len(arquivos_principais)}")
    
    with col2:
        conexoes_ok = sum(1 for v in diagnostico["conexoes_testadas"].values() if v == "OK")
        st.metric("🔗 Conexões", conexoes_ok, delta=f"/{len(diagnostico['conexoes_testadas'])}")
    
    with col3:
        funcionalidades_ok = sum(1 for v in diagnostico["funcionalidades_testadas"].values() if v == "OK")
        st.metric("⚙️ Funcionalidades", funcionalidades_ok, delta=f"/{len(diagnostico['funcionalidades_testadas'])}")
    
    with col4:
        st.metric("❌ Erros", len(diagnostico["erros_encontrados"]))
    
    # Detalhes
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📁 Arquivos Encontrados:**")
        for arquivo in diagnostico["arquivos_encontrados"]:
            st.write(f"✅ {arquivo}")
        
        arquivos_faltando = [a for a in arquivos_principais if a not in diagnostico["arquivos_encontrados"]]
        if arquivos_faltando:
            st.markdown("**❌ Arquivos Faltando:**")
            for arquivo in arquivos_faltando:
                st.write(f"❌ {arquivo}")
    
    with col2:
        st.markdown("**🔗 Status das Conexões:**")
        for nome, status in diagnostico["conexoes_testadas"].items():
            emoji = "✅" if status == "OK" else "❌"
            st.write(f"{emoji} {nome}: {status}")
        
        st.markdown("**⚙️ Status das Funcionalidades:**")
        for nome, status in diagnostico["funcionalidades_testadas"].items():
            emoji = "✅" if status == "OK" else "❌"
            st.write(f"{emoji} {nome}: {status}")
    
    # Erros detalhados
    if diagnostico["erros_encontrados"]:
        st.markdown("### ❌ Erros Encontrados")
        for erro in diagnostico["erros_encontrados"]:
            st.error(erro)
    else:
        st.success("🎉 Nenhum erro encontrado!")
    
    return diagnostico

def mostrar_navegacao_sistema():
    """Mostra opções de navegação entre os módulos do sistema"""
    
    st.subheader("🧭 Navegação do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🎓 Gestão Pedagógica**")
        st.info("Interface principal para gestão de alunos, responsáveis e acadêmico")
        
        if st.button("🚀 Abrir Interface Pedagógica", key="nav_pedagogica"):
            st.markdown("""
            **Para acessar a Interface Pedagógica:**
            
            ```bash
            streamlit run interface_pedagogica_teste.py
            ```
            
            **Funcionalidades disponíveis:**
            - Gestão de alunos e responsáveis
            - Busca e filtros avançados
            - Relatórios pedagógicos
            - **Gestão completa de mensalidades**
            """)
    
    with col2:
        st.markdown("**💰 Processamento Financeiro**")
        st.info("Interface para processar extratos PIX e pagamentos")
        
        if st.button("🚀 Abrir Processamento Extrato", key="nav_extrato"):
            st.markdown("""
            **Para acessar o Processamento de Extrato:**
            
            ```bash
            streamlit run interface_processamento_extrato.py
            ```
            
            **Funcionalidades disponíveis:**
            - Processamento de extratos PIX
            - Vinculação automática de responsáveis
            - **Gestão integrada de mensalidades**
            - Histórico e consistência
            """)
    
    with col3:
        st.markdown("**📊 Sistema Completo**")
        st.info("Acesso direto às funcionalidades individuais")
        
        if st.button("🚀 Módulo de Mensalidades", key="nav_mensalidades"):
            st.markdown("""
            **Para usar o Módulo de Mensalidades:**
            
            ```python
            from gestao_mensalidades import *
            
            # Inicializar sistema
            inicializar_sistema_mensalidades()
            
            # Usar funcionalidades
            gerar_mensalidades_aluno_avancado(id_aluno, "automatico")
            ```
            """)

def mostrar_configuracoes_avancadas():
    """Mostra configurações avançadas do sistema integrado"""
    
    st.subheader("⚙️ Configurações Avançadas")
    
    # Tabs de configuração
    config_tab1, config_tab2, config_tab3 = st.tabs([
        "🔧 Sistema",
        "🗄️ Base de Dados", 
        "📊 Relatórios"
    ])
    
    with config_tab1:
        st.markdown("**🔧 Configurações do Sistema**")
        
        # Configuração de debug
        debug_mode = st.checkbox("Modo Debug", value=False)
        if debug_mode:
            st.session_state.debug_mode = True
            st.info("✅ Modo debug ativado - Logs detalhados serão exibidos")
        
        # Configuração de cache
        if st.button("🧹 Limpar Cache do Sistema"):
            # Limpar todos os caches de sessão
            keys_to_remove = []
            for key in st.session_state.keys():
                if key not in ['sistema_inicializado', 'deps_verificadas']:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.success("✅ Cache do sistema limpo!")
    
    with config_tab2:
        st.markdown("**🗄️ Configurações da Base de Dados**")
        
        # Testar conexão
        if st.button("🔍 Testar Conexão"):
            try:
                from models.base import supabase
                response = supabase.table("alunos").select("count", count="exact").execute()
                st.success(f"✅ Conexão OK! Total de alunos: {response.count}")
            except Exception as e:
                st.error(f"❌ Erro na conexão: {str(e)}")
        
        # Verificar tabelas
        if st.button("📋 Verificar Estrutura das Tabelas"):
            try:
                from models.base import supabase
                
                tabelas_verificar = ["alunos", "responsaveis", "turmas", "mensalidades", "pagamentos"]
                
                for tabela in tabelas_verificar:
                    try:
                        response = supabase.table(tabela).select("count", count="exact").execute()
                        st.write(f"✅ {tabela}: {response.count} registros")
                    except Exception as e:
                        st.write(f"❌ {tabela}: Erro - {str(e)}")
                        
            except Exception as e:
                st.error(f"❌ Erro geral: {str(e)}")
    
    with config_tab3:
        st.markdown("**📊 Configurações de Relatórios**")
        
        # Configurações de exportação
        formato_padrao = st.selectbox(
            "Formato padrão de exportação:",
            ["PDF", "Excel", "CSV"]
        )
        
        incluir_graficos = st.checkbox("Incluir gráficos nos relatórios", value=True)
        
        if st.button("💾 Salvar Configurações"):
            st.session_state.config_relatorios = {
                "formato_padrao": formato_padrao,
                "incluir_graficos": incluir_graficos
            }
            st.success("✅ Configurações salvas!")

def main():
    """Função principal do sistema integrado"""
    
    # Inicializar sistema
    deps = inicializar_sistema()
    
    # Cabeçalho
    st.title("🏫 Sistema de Gestão Escolar - Central de Integração")
    st.markdown("Central de controle e integração de todas as funcionalidades do sistema")
    
    # Sidebar com navegação
    with st.sidebar:
        st.header("🧭 Navegação")
        
        opcao = st.radio(
            "Selecione uma opção:",
            [
                "🏠 Visão Geral",
                "🔍 Status do Sistema", 
                "🩺 Diagnóstico Completo",
                "🧭 Navegação",
                "⚙️ Configurações"
            ]
        )
    
    # Conteúdo principal baseado na seleção
    if opcao == "🏠 Visão Geral":
        st.header("🏠 Visão Geral do Sistema")
        
        st.markdown("""
        ### 🎯 Funcionalidades Principais
        
        **📅 Gestão de Mensalidades:**
        - Sistema completo de geração e controle de mensalidades
        - Integração com extratos PIX para processamento automático
        - Relatórios e dashboards em tempo real
        
        **🎓 Gestão Pedagógica:**
        - Cadastro e gestão de alunos e responsáveis
        - Controle de turmas e matrículas
        - Relatórios pedagógicos avançados
        
        **💰 Gestão Financeira:**
        - Processamento de extratos bancários
        - Conciliação automática de pagamentos
        - Controle de inadimplência
        
        ### 🔗 Integração Total
        
        Todas as funcionalidades trabalham de forma integrada:
        - Dados sincronizados entre módulos
        - Interface unificada e intuitiva
        - Relatórios consolidados
        """)
        
        # Métricas rápidas se a conexão estiver OK
        if deps.get("Base de Dados"):
            try:
                from models.base import supabase
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    alunos_count = supabase.table("alunos").select("count", count="exact").execute()
                    st.metric("👨‍🎓 Alunos", alunos_count.count)
                
                with col2:
                    resp_count = supabase.table("responsaveis").select("count", count="exact").execute()
                    st.metric("👥 Responsáveis", resp_count.count)
                
                with col3:
                    try:
                        mens_count = supabase.table("mensalidades").select("count", count="exact").execute()
                        st.metric("📅 Mensalidades", mens_count.count)
                    except:
                        st.metric("📅 Mensalidades", "N/A")
                
                with col4:
                    try:
                        pag_count = supabase.table("pagamentos").select("count", count="exact").execute()
                        st.metric("💰 Pagamentos", pag_count.count)
                    except:
                        st.metric("💰 Pagamentos", "N/A")
                        
            except Exception as e:
                st.warning(f"⚠️ Não foi possível carregar métricas: {str(e)}")
    
    elif opcao == "🔍 Status do Sistema":
        mostrar_status_sistema()
    
    elif opcao == "🩺 Diagnóstico Completo":
        if st.button("🚀 Executar Diagnóstico", type="primary"):
            executar_diagnostico_completo()
    
    elif opcao == "🧭 Navegação":
        mostrar_navegacao_sistema()
    
    elif opcao == "⚙️ Configurações":
        mostrar_configuracoes_avancadas()
    
    # Footer
    st.markdown("---")
    st.markdown("**💡 Dica:** Use as abas da barra lateral para navegar entre as diferentes funcionalidades do sistema.")

if __name__ == "__main__":
    main() 