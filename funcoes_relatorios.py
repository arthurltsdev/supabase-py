#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📊 MÓDULO DE GERAÇÃO DE RELATÓRIOS
==================================

Funcionalidades para gerar relatórios pedagógicos e financeiros
usando OpenAI para formatação inteligente e python-docx para .docx
"""

import os
import io
import base64
from datetime import datetime, date
from typing import Dict, List, Optional, Union
import pandas as pd

# Dependências necessárias
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Importar funções do modelo pedagógico
from models.pedagogico import (
    listar_turmas_disponiveis,
    obter_mapeamento_turmas,
    buscar_alunos_por_turmas,
    supabase
)

# ==========================================================
# 🔧 CONFIGURAÇÕES E CONSTANTES
# ==========================================================

# Configuração OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None

if OPENAI_AVAILABLE and OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"❌ Erro ao inicializar OpenAI: {e}")

# Campos disponíveis para relatórios
CAMPOS_ALUNO = {
    'nome': 'Nome do Aluno',
    'turno': 'Turno',
    'data_nascimento': 'Data de Nascimento',
    'dia_vencimento': 'Dia de Vencimento',
    'data_matricula': 'Data de Matrícula',
    'valor_mensalidade': 'Valor da Mensalidade'
}

CAMPOS_RESPONSAVEL = {
    'nome': 'Nome do Responsável',
    'cpf': 'CPF',
    'telefone': 'Telefone/Contato',
    'email': 'Email',
    'endereco': 'Endereço',
    'tipo_relacao': 'Tipo de Relação',
    'responsavel_financeiro': 'Responsável Financeiro'
}

CAMPOS_MENSALIDADE = {
    'mes_referencia': 'Mês de Referência',
    'data_vencimento': 'Data de Vencimento',
    'valor': 'Valor',
    'status': 'Status',
    'data_pagamento': 'Data de Pagamento',
    'observacoes': 'Observações'
}

CAMPOS_PAGAMENTO = {
    'data_pagamento': 'Data do Pagamento',
    'valor': 'Valor',
    'tipo_pagamento': 'Tipo de Pagamento',
    'forma_pagamento': 'Forma de Pagamento',
    'observacoes': 'Observações'
}

CAMPOS_EXTRATO_PIX = {
    'data_pagamento': 'Data do Pagamento',
    'valor': 'Valor',
    'nome_remetente': 'Nome do Remetente',
    'descricao': 'Descrição',
    'status': 'Status'
}

# ==========================================================
# 🤖 FUNÇÕES DE INTELIGÊNCIA ARTIFICIAL
# ==========================================================

def formatar_relatorio_com_ia(dados_brutos: Dict, tipo_relatorio: str, campos_selecionados: List[str]) -> str:
    """
    Usa OpenAI para formatar o relatório de forma inteligente e profissional
    """
    if not openai_client:
        return formatar_relatorio_basico(dados_brutos, tipo_relatorio, campos_selecionados)
    
    try:
        if tipo_relatorio == 'pedagogico':
            exemplo_formato = """
Lista de Alunos

Berçário
1.	Alice Nascimento Rafael
Turno: Integral
Data de Matrícula: 24/01/2025
Dia de Vencimento: 5
Valor Mensalidade: R$ 990,00
Responsável Financeiro:
Nome: Mayra Ferreira Nascimento
CPF: 075.046.734-71
Tipo de relação: Mãe
Contato: (83) 99631-0062
Email: ferreiramayra73@gmail.com
Responsável 2
Nome: Itiel Rafael Figueredo Santos
CPF: AUSENTE
Tipo de relação: Pai
Contato: (83) 99654-6308
Email: AUSENTE
**OBSERVAÇÃO:**

2.	Ian Duarte Rolim
Turno: Tarde
Data de Matrícula: 26/12/2024
Dia de Vencimento: 5
Valor Mensalidade: R$ 705,00
Responsável Financeiro:
Nome: Pedro Henrique Rolim de Oliveira
CPF: 084.085.394-77
Tipo de relação: Pai
Contato: AUSENTE
Email: AUSENTE
Responsável 2
Nome: Kamila Duarte de Sousa
CPF: AUSENTE
Tipo de relação: Mãe
Contato: AUSENTE
Email: AUSENTE
**OBSERVAÇÃO:**
"""
            
            prompt = f"""
Você é um assistente especializado em relatórios pedagógicos para escolas brasileiras.

INSTRUÇÕES ESPECÍFICAS:
1. Use EXATAMENTE o formato do exemplo abaixo
2. Organize por turma, depois por aluno numerado
3. Para valores que são realmente NULL, None, vazios ou "Não informado", use "AUSENTE"
4. NÃO use "AUSENTE" se o valor existe no banco de dados - apenas para campos realmente vazios
5. Formate datas como DD/MM/YYYY
6. Formate valores monetários como R$ X.XXX,XX
7. Liste responsáveis como "Responsável Financeiro" primeiro, depois "Responsável 2, 3..." 
8. SEMPRE inclua "**OBSERVAÇÃO:**" em negrito após o último responsável de cada aluno
9. Mantenha formatação limpa e profissional
10. Use apenas os campos selecionados: {', '.join(campos_selecionados)}

EXEMPLO DE FORMATO:
{exemplo_formato}

DADOS PARA FORMATAÇÃO:
{dados_brutos}

Gere o relatório seguindo EXATAMENTE o padrão do exemplo, incluindo a seção OBSERVAÇÃO para cada aluno.
"""
        else:  # financeiro
            prompt = f"""
Você é um assistente especializado em relatórios financeiros para escolas brasileiras.

INSTRUÇÕES ESPECÍFICAS:
1. Organize os dados de forma clara e estruturada
2. Para valores NULL, None ou vazios, use "AUSENTE"  
3. Formate datas como DD/MM/YYYY
4. Formate valores monetários como R$ X.XXX,XX
5. Agrupe informações relacionadas logicamente
6. Inclua subtotais quando relevante
7. Use apenas os campos selecionados: {', '.join(campos_selecionados)}

DADOS PARA FORMATAÇÃO:
{dados_brutos}

Gere um relatório financeiro detalhado e bem estruturado.
"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em geração de relatórios educacionais profissionais em português brasileiro."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"❌ Erro na formatação com IA: {e}")
        return formatar_relatorio_basico(dados_brutos, tipo_relatorio, campos_selecionados)

def formatar_relatorio_basico(dados_brutos: Dict, tipo_relatorio: str, campos_selecionados: List[str]) -> str:
    """
    Formatação básica sem IA como fallback
    """
    texto = f"RELATÓRIO {tipo_relatorio.upper()}\n"
    texto += f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    if tipo_relatorio == 'pedagogico':
        texto += "Lista de Alunos\n\n"
        
        for turma_nome, dados_turma in dados_brutos.get('dados_por_turma', {}).items():
            texto += f"{turma_nome}\n"
            
            for i, aluno in enumerate(dados_turma.get('alunos', []), 1):
                texto += f"{i}.\t{aluno.get('nome', 'AUSENTE')}\n"
                
                # Adicionar campos selecionados do aluno
                for campo in campos_selecionados:
                    if campo in CAMPOS_ALUNO and campo != 'nome':
                        valor = aluno.get(campo)
                        # Verificar se é realmente NULL/None/vazio
                        if valor is None or valor == "" or valor == "Não informado":
                            valor = 'AUSENTE'
                        elif campo == 'valor_mensalidade' and valor != 'AUSENTE':
                            valor = f"R$ {float(valor):,.2f}"
                        elif 'data' in campo and valor != 'AUSENTE':
                            try:
                                data_obj = datetime.strptime(str(valor), '%Y-%m-%d')
                                valor = data_obj.strftime('%d/%m/%Y')
                            except:
                                pass
                        
                        texto += f"{CAMPOS_ALUNO[campo]}: {valor}\n"
                
                # Adicionar responsáveis se selecionados
                responsaveis = aluno.get('responsaveis', [])
                resp_financeiro = next((r for r in responsaveis if r.get('responsavel_financeiro')), None)
                outros_resp = [r for r in responsaveis if not r.get('responsavel_financeiro')]
                
                # Responsável financeiro primeiro
                if resp_financeiro:
                    texto += "Responsável Financeiro:\n"
                    for campo in campos_selecionados:
                        if campo in CAMPOS_RESPONSAVEL:
                            valor = resp_financeiro.get(campo)
                            # Verificar se é realmente NULL/None/vazio
                            if valor is None or valor == "" or valor == "Não informado":
                                valor = 'AUSENTE'
                            texto += f"{CAMPOS_RESPONSAVEL[campo]}: {valor}\n"
                
                # Outros responsáveis
                for j, resp in enumerate(outros_resp, 2):
                    texto += f"Responsável {j}:\n"
                    for campo in campos_selecionados:
                        if campo in CAMPOS_RESPONSAVEL:
                            valor = resp.get(campo)
                            # Verificar se é realmente NULL/None/vazio
                            if valor is None or valor == "" or valor == "Não informado":
                                valor = 'AUSENTE'
                            texto += f"{CAMPOS_RESPONSAVEL[campo]}: {valor}\n"
                
                # Adicionar campo OBSERVAÇÃO em negrito
                texto += "**OBSERVAÇÃO:**\n\n"
                texto += "\n"
            
            texto += "\n"
    
    return texto

# ==========================================================
# 📊 FUNÇÕES DE COLETA DE DADOS
# ==========================================================

def coletar_dados_pedagogicos(turmas_selecionadas: List[str], campos_selecionados: List[str]) -> Dict:
    """
    Coleta dados pedagógicos conforme os filtros selecionados
    """
    try:
        # Obter IDs das turmas
        mapeamento_resultado = obter_mapeamento_turmas()
        if not mapeamento_resultado.get("success"):
            return {"success": False, "error": "Erro ao obter mapeamento de turmas"}
        
        ids_turmas = []
        for nome_turma in turmas_selecionadas:
            if nome_turma in mapeamento_resultado["mapeamento"]:
                ids_turmas.append(mapeamento_resultado["mapeamento"][nome_turma])
        
        if not ids_turmas:
            return {"success": False, "error": "Nenhuma turma válida selecionada"}
        
        # Buscar alunos das turmas selecionadas
        resultado_alunos = buscar_alunos_por_turmas(ids_turmas)
        if not resultado_alunos.get("success"):
            return {"success": False, "error": f"Erro ao buscar alunos: {resultado_alunos.get('error')}"}
        
        dados_organizados = {
            "success": True,
            "dados_por_turma": {},
            "total_alunos": resultado_alunos.get("total_alunos", 0),
            "turmas_incluidas": turmas_selecionadas,
            "campos_selecionados": campos_selecionados,
            "data_geracao": datetime.now().isoformat()
        }
        
        # Organizar dados por turma
        for turma_nome, dados_turma in resultado_alunos.get("alunos_por_turma", {}).items():
            dados_organizados["dados_por_turma"][turma_nome] = {
                "alunos": dados_turma.get("alunos", []),
                "total_alunos": len(dados_turma.get("alunos", []))
            }
        
        return dados_organizados
    
    except Exception as e:
        return {"success": False, "error": f"Erro na coleta de dados pedagógicos: {e}"}

def coletar_dados_financeiros(turmas_selecionadas: List[str], campos_selecionados: List[str], 
                             filtros: Dict) -> Dict:
    """
    Coleta dados financeiros conforme os filtros selecionados
    """
    try:
        # Primeiro, obter alunos das turmas selecionadas
        dados_base = coletar_dados_pedagogicos(turmas_selecionadas, [])
        if not dados_base.get("success"):
            return dados_base
        
        # Coletar IDs de todos os alunos
        ids_alunos = []
        for turma_nome, dados_turma in dados_base["dados_por_turma"].items():
            for aluno in dados_turma["alunos"]:
                ids_alunos.append(aluno["id"])
        
        dados_financeiros = {
            "success": True,
            "alunos": [],
            "mensalidades": [],
            "pagamentos": [],
            "extrato_pix": [],
            "filtros_aplicados": filtros,
            "campos_selecionados": campos_selecionados,
            "data_geracao": datetime.now().isoformat()
        }
        
        # Buscar dados de cada aluno
        for id_aluno in ids_alunos:
            aluno_response = supabase.table("alunos").select("""
                *, turmas!inner(nome_turma)
            """).eq("id", id_aluno).execute()
            
            if aluno_response.data:
                aluno_data = aluno_response.data[0]
                aluno_data["turma_nome"] = aluno_data["turmas"]["nome_turma"]
                
                # Buscar responsáveis
                responsaveis_response = supabase.table("alunos_responsaveis").select("""
                    *, responsaveis!inner(*)
                """).eq("id_aluno", id_aluno).execute()
                
                responsaveis = []
                for vinculo in responsaveis_response.data:
                    resp_data = vinculo["responsaveis"]
                    resp_data.update({
                        "tipo_relacao": vinculo["tipo_relacao"],
                        "responsavel_financeiro": vinculo["responsavel_financeiro"]
                    })
                    responsaveis.append(resp_data)
                
                aluno_data["responsaveis"] = responsaveis
                dados_financeiros["alunos"].append(aluno_data)
        
        # Buscar dados adicionais conforme campos selecionados
        periodo_inicio = filtros.get('periodo_inicio')
        periodo_fim = filtros.get('periodo_fim')
        
        # Mensalidades
        if any('mensalidade' in campo for campo in campos_selecionados):
            status_mensalidades = filtros.get('status_mensalidades', [])
            
            query = supabase.table("mensalidades").select("*").in_("id_aluno", ids_alunos)
            
            if periodo_inicio:
                query = query.gte("data_vencimento", periodo_inicio)
            if periodo_fim:
                query = query.lte("data_vencimento", periodo_fim)
            if status_mensalidades:
                query = query.in_("status", status_mensalidades)
            
            mensalidades_response = query.execute()
            dados_financeiros["mensalidades"] = mensalidades_response.data
        
        # Pagamentos
        if any('pagamento' in campo for campo in campos_selecionados):
            query = supabase.table("pagamentos").select("*").in_("id_aluno", ids_alunos)
            
            if periodo_inicio:
                query = query.gte("data_pagamento", periodo_inicio)
            if periodo_fim:
                query = query.lte("data_pagamento", periodo_fim)
            
            pagamentos_response = query.execute()
            dados_financeiros["pagamentos"] = pagamentos_response.data
        
        # Extrato PIX
        if any('extrato_pix' in campo for campo in campos_selecionados):
            incluir_processados = filtros.get('extrato_pix_processados', False)
            incluir_nao_processados = filtros.get('extrato_pix_nao_processados', False)
            
            # Obter IDs dos responsáveis
            ids_responsaveis = []
            for aluno_data in dados_financeiros["alunos"]:
                for resp in aluno_data.get("responsaveis", []):
                    if resp["id"] not in ids_responsaveis:
                        ids_responsaveis.append(resp["id"])
            
            if ids_responsaveis:
                query = supabase.table("extrato_pix").select("*").in_("id_responsavel", ids_responsaveis)
                
                if periodo_inicio:
                    query = query.gte("data_pagamento", periodo_inicio)
                if periodo_fim:
                    query = query.lte("data_pagamento", periodo_fim)
                
                status_filtros = []
                if incluir_processados:
                    status_filtros.append("registrado")
                if incluir_nao_processados:
                    status_filtros.append("novo")
                
                if status_filtros:
                    query = query.in_("status", status_filtros)
                
                extrato_response = query.execute()
                dados_financeiros["extrato_pix"] = extrato_response.data
        
        return dados_financeiros
    
    except Exception as e:
        return {"success": False, "error": f"Erro na coleta de dados financeiros: {e}"}

# ==========================================================
# 📄 FUNÇÕES DE GERAÇÃO DE DOCUMENTOS
# ==========================================================

def criar_documento_docx(titulo: str, conteudo: str) -> Optional[Document]:
    """
    Cria um documento .docx formatado profissionalmente
    """
    if not DOCX_AVAILABLE:
        return None
    
    try:
        doc = Document()
        
        # Configurar margens (A4, orientação vertical)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Título principal
        titulo_para = doc.add_heading(titulo, level=1)
        titulo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Data de geração
        data_para = doc.add_paragraph(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        data_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Separador
        doc.add_paragraph("_" * 60).alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Adicionar conteúdo
        linhas = conteudo.split('\n')
        for linha in linhas:
            if linha.strip():
                if linha.strip().endswith(':') and len(linha) < 50:
                    # Títulos de seção
                    para = doc.add_paragraph()
                    run = para.add_run(linha)
                    run.bold = True
                elif linha.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    # Numeração de alunos
                    para = doc.add_paragraph()
                    run = para.add_run(linha)
                    run.bold = True
                    run.font.size = Pt(12)
                else:
                    doc.add_paragraph(linha)
            else:
                doc.add_paragraph()
        
        return doc
    
    except Exception as e:
        print(f"❌ Erro ao criar documento: {e}")
        return None

def salvar_documento_temporario(doc: Document, nome_arquivo: str) -> Optional[str]:
    """
    Salva documento temporariamente e retorna o caminho
    """
    try:
        pasta_temp = "temp_reports"
        if not os.path.exists(pasta_temp):
            os.makedirs(pasta_temp)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_completo = f"{nome_arquivo}_{timestamp}.docx"
        caminho_arquivo = os.path.join(pasta_temp, nome_completo)
        
        doc.save(caminho_arquivo)
        return caminho_arquivo
    
    except Exception as e:
        print(f"❌ Erro ao salvar documento: {e}")
        return None

# ==========================================================
# 🎯 FUNÇÕES PRINCIPAIS DE GERAÇÃO
# ==========================================================

def gerar_relatorio_pedagogico(turmas_selecionadas: List[str], campos_selecionados: List[str]) -> Dict:
    """
    Gera relatório pedagógico completo
    """
    try:
        if not DOCX_AVAILABLE:
            return {
                "success": False, 
                "error": "python-docx não disponível. Execute: pip install python-docx"
            }
        
        # Coletar dados
        dados = coletar_dados_pedagogicos(turmas_selecionadas, campos_selecionados)
        if not dados.get("success"):
            return dados
        
        # Formatar com IA
        conteudo_formatado = formatar_relatorio_com_ia(dados, "pedagogico", campos_selecionados)
        
        # Criar documento
        titulo = f"Relatório Pedagógico - {', '.join(turmas_selecionadas)}"
        doc = criar_documento_docx(titulo, conteudo_formatado)
        
        if not doc:
            return {"success": False, "error": "Erro ao criar documento Word"}
        
        # Salvar temporariamente
        nome_arquivo = f"relatorio_pedagogico_{'_'.join(turmas_selecionadas)}"
        nome_arquivo = nome_arquivo.replace(' ', '_').replace('/', '_')
        
        caminho_arquivo = salvar_documento_temporario(doc, nome_arquivo)
        
        if not caminho_arquivo:
            return {"success": False, "error": "Erro ao salvar documento"}
        
        return {
            "success": True,
            "arquivo": caminho_arquivo,
            "nome_arquivo": os.path.basename(caminho_arquivo),
            "titulo": titulo,
            "total_alunos": dados["total_alunos"],
            "turmas_incluidas": dados["turmas_incluidas"],
            "campos_selecionados": dados["campos_selecionados"],
            "data_geracao": dados["data_geracao"]
        }
    
    except Exception as e:
        return {"success": False, "error": f"Erro na geração do relatório pedagógico: {e}"}

def gerar_relatorio_financeiro(turmas_selecionadas: List[str], campos_selecionados: List[str], 
                              filtros: Dict) -> Dict:
    """
    Gera relatório financeiro completo
    """
    try:
        if not DOCX_AVAILABLE:
            return {
                "success": False, 
                "error": "python-docx não disponível. Execute: pip install python-docx"
            }
        
        # Coletar dados
        dados = coletar_dados_financeiros(turmas_selecionadas, campos_selecionados, filtros)
        if not dados.get("success"):
            return dados
        
        # Formatar com IA
        conteudo_formatado = formatar_relatorio_com_ia(dados, "financeiro", campos_selecionados)
        
        # Criar documento
        titulo = f"Relatório Financeiro - {', '.join(turmas_selecionadas)}"
        doc = criar_documento_docx(titulo, conteudo_formatado)
        
        if not doc:
            return {"success": False, "error": "Erro ao criar documento Word"}
        
        # Salvar temporariamente
        nome_arquivo = f"relatorio_financeiro_{'_'.join(turmas_selecionadas)}"
        nome_arquivo = nome_arquivo.replace(' ', '_').replace('/', '_')
        
        caminho_arquivo = salvar_documento_temporario(doc, nome_arquivo)
        
        if not caminho_arquivo:
            return {"success": False, "error": "Erro ao salvar documento"}
        
        return {
            "success": True,
            "arquivo": caminho_arquivo,
            "nome_arquivo": os.path.basename(caminho_arquivo),
            "titulo": titulo,
            "total_alunos": len(dados.get("alunos", [])),
            "turmas_incluidas": turmas_selecionadas,
            "campos_selecionados": campos_selecionados,
            "filtros_aplicados": filtros,
            "data_geracao": dados["data_geracao"]
        }
    
    except Exception as e:
        return {"success": False, "error": f"Erro na geração do relatório financeiro: {e}"}

# ==========================================================
# 🧹 FUNÇÕES AUXILIARES
# ==========================================================

def limpar_arquivos_temporarios(max_idade_horas: int = 24):
    """Remove arquivos temporários antigos"""
    try:
        pasta_temp = "temp_reports"
        if not os.path.exists(pasta_temp):
            return
        
        agora = datetime.now()
        arquivos_removidos = 0
        
        for arquivo in os.listdir(pasta_temp):
            caminho_arquivo = os.path.join(pasta_temp, arquivo)
            tempo_modificacao = datetime.fromtimestamp(os.path.getmtime(caminho_arquivo))
            idade_horas = (agora - tempo_modificacao).total_seconds() / 3600
            
            if idade_horas > max_idade_horas:
                os.remove(caminho_arquivo)
                arquivos_removidos += 1
        
        if arquivos_removidos > 0:
            print(f"🧹 {arquivos_removidos} arquivos temporários removidos")
    
    except Exception as e:
        print(f"❌ Erro ao limpar arquivos temporários: {e}")

def obter_campos_disponiveis() -> Dict:
    """Retorna todos os campos disponíveis para relatórios"""
    return {
        "aluno": CAMPOS_ALUNO,
        "responsavel": CAMPOS_RESPONSAVEL,
        "mensalidade": CAMPOS_MENSALIDADE,
        "pagamento": CAMPOS_PAGAMENTO,
        "extrato_pix": CAMPOS_EXTRATO_PIX
    }

# ==========================================================
# 🎯 FUNÇÃO PRINCIPAL PARA INTERFACE
# ==========================================================

def gerar_relatorio_interface(tipo_relatorio: str, configuracao: Dict) -> Dict:
    """
    Função principal para ser chamada pela interface Streamlit
    """
    try:
        # Validar tipo de relatório
        if tipo_relatorio not in ['pedagogico', 'financeiro']:
            return {"success": False, "error": "Tipo de relatório inválido"}
        
        # Extrair configurações
        turmas_selecionadas = configuracao.get('turmas_selecionadas', [])
        campos_selecionados = configuracao.get('campos_selecionados', [])
        
        # Validar turmas
        if not turmas_selecionadas:
            return {"success": False, "error": "Nenhuma turma selecionada"}
        
        # Validar campos
        if not campos_selecionados:
            return {"success": False, "error": "Nenhum campo selecionado"}
        
        # Limpar arquivos antigos
        limpar_arquivos_temporarios()
        
        # Gerar relatório conforme o tipo
        if tipo_relatorio == 'pedagogico':
            return gerar_relatorio_pedagogico(turmas_selecionadas, campos_selecionados)
        else:
            filtros = configuracao.get('filtros', {})
            return gerar_relatorio_financeiro(turmas_selecionadas, campos_selecionados, filtros)
    
    except Exception as e:
        return {"success": False, "error": f"Erro na geração do relatório: {e}"} 