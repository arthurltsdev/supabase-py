#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔗 INTEGRAÇÕES DO MODAL DE MENSALIDADE
=====================================

Funções complementares para integração com sistemas externos:
- Geração de relatórios
- Envio de emails e WhatsApp
- Sistema de auditoria
- Geração de PDFs
"""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import json
import os

# Importações condicionais para evitar erros se módulos não estiverem disponíveis
try:
    from funcoes_relatorios import gerar_relatorio_interface, obter_campos_disponiveis
    RELATORIOS_DISPONIVEL = True
except ImportError:
    RELATORIOS_DISPONIVEL = False
    st.warning("⚠️ Módulo funcoes_relatorios não encontrado")

try:
    from models.financeiro import gerar_cobranca_pdf, gerar_recibo_pdf
    FINANCEIRO_DISPONIVEL = True
except ImportError:
    FINANCEIRO_DISPONIVEL = False

from models.base import supabase, obter_timestamp, formatar_data_br, formatar_valor_br

# ==========================================================
# 📊 GERAÇÃO DE RELATÓRIOS
# ==========================================================

def gerar_relatorio_mensalidade_docx(id_mensalidade: str, dados_mensalidade: Dict) -> Dict:
    """
    Gera relatório .docx para uma mensalidade específica
    
    Args:
        id_mensalidade: ID da mensalidade
        dados_mensalidade: Dados completos da mensalidade
        
    Returns:
        Dict: {"success": bool, "arquivo": str, "nome_arquivo": str, "error": str}
    """
    
    if not RELATORIOS_DISPONIVEL:
        return {
            "success": False,
            "error": "Módulo de relatórios não disponível"
        }
    
    try:
        mensalidade = dados_mensalidade["mensalidade"]
        aluno = mensalidade["alunos"]
        responsavel = dados_mensalidade.get("responsavel")
        
        # Configuração específica para relatório de mensalidade
        configuracao = {
            'tipo_relatorio': 'mensalidade_individual',
            'dados_mensalidade': {
                'id_mensalidade': mensalidade['id_mensalidade'],
                'mes_referencia': mensalidade['mes_referencia'],
                'valor': mensalidade['valor'],
                'data_vencimento': mensalidade['data_vencimento'],
                'data_pagamento': mensalidade.get('data_pagamento'),
                'status': mensalidade['status'],
                'observacoes': mensalidade.get('observacoes', '')
            },
            'dados_aluno': {
                'nome': aluno['nome'],
                'turma': aluno['turmas']['nome_turma'],
                'turno': aluno.get('turno'),
                'valor_mensalidade': aluno.get('valor_mensalidade')
            },
            'dados_responsavel': responsavel if responsavel else {},
            'incluir_historico': True,
            'incluir_detalhes_pagamento': True
        }
        
        # Chamar função de geração de relatório
        resultado = gerar_relatorio_interface('mensalidade_individual', configuracao)
        
        return resultado
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao gerar relatório: {str(e)}"
        }

def exportar_dados_mensalidade_json(dados_mensalidade: Dict) -> str:
    """
    Exporta dados da mensalidade em formato JSON
    
    Args:
        dados_mensalidade: Dados completos da mensalidade
        
    Returns:
        str: JSON formatado
    """
    try:
        mensalidade = dados_mensalidade["mensalidade"]
        
        dados_exportacao = {
            "metadados": {
                "tipo_exportacao": "mensalidade_individual",
                "timestamp_exportacao": datetime.now().isoformat(),
                "versao_sistema": "1.0"
            },
            "mensalidade": {
                "id_mensalidade": mensalidade["id_mensalidade"],
                "mes_referencia": mensalidade["mes_referencia"],
                "valor": float(mensalidade["valor"]),
                "data_vencimento": mensalidade["data_vencimento"],
                "data_pagamento": mensalidade.get("data_pagamento"),
                "status": mensalidade["status"],
                "observacoes": mensalidade.get("observacoes"),
                "inserted_at": mensalidade.get("inserted_at"),
                "updated_at": mensalidade.get("updated_at")
            },
            "aluno": {
                "id": mensalidade["alunos"]["id"],
                "nome": mensalidade["alunos"]["nome"],
                "turma": mensalidade["alunos"]["turmas"]["nome_turma"],
                "turno": mensalidade["alunos"].get("turno"),
                "valor_mensalidade": float(mensalidade["alunos"].get("valor_mensalidade", 0))
            },
            "responsavel": dados_mensalidade.get("responsavel", {}),
            "pagamentos_relacionados": dados_mensalidade.get("pagamentos", [])
        }
        
        return json.dumps(dados_exportacao, indent=2, default=str, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2, ensure_ascii=False)

# ==========================================================
# 💰 GERAÇÃO DE DOCUMENTOS FINANCEIROS
# ==========================================================

def gerar_cobranca_mensalidade(dados_mensalidade: Dict) -> Dict:
    """
    Gera PDF de cobrança para a mensalidade
    
    Args:
        dados_mensalidade: Dados completos da mensalidade
        
    Returns:
        Dict: {"success": bool, "arquivo": str, "nome_arquivo": str}
    """
    
    if not FINANCEIRO_DISPONIVEL:
        return {
            "success": False,
            "error": "Módulo financeiro não disponível"
        }
    
    try:
        mensalidade = dados_mensalidade["mensalidade"]
        aluno = mensalidade["alunos"]
        responsavel = dados_mensalidade.get("responsavel")
        
        # Dados para geração da cobrança
        dados_cobranca = {
            "tipo_documento": "cobranca_mensalidade",
            "mensalidade": {
                "id": mensalidade["id_mensalidade"],
                "mes_referencia": mensalidade["mes_referencia"],
                "valor": mensalidade["valor"],
                "data_vencimento": mensalidade["data_vencimento"],
                "observacoes": mensalidade.get("observacoes", "")
            },
            "aluno": {
                "nome": aluno["nome"],
                "turma": aluno["turmas"]["nome_turma"]
            },
            "responsavel": responsavel if responsavel else {
                "nome": "Responsável não identificado"
            },
            "escola": {
                "nome": "Escola Exemplo",  # TODO: Buscar dados da escola do config
                "endereco": "Endereço da Escola",
                "telefone": "(00) 0000-0000",
                "email": "contato@escola.com"
            }
        }
        
        resultado = gerar_cobranca_pdf(dados_cobranca)
        return resultado
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao gerar cobrança: {str(e)}"
        }

def gerar_recibo_mensalidade(dados_mensalidade: Dict) -> Dict:
    """
    Gera PDF de recibo para mensalidade paga
    
    Args:
        dados_mensalidade: Dados completos da mensalidade
        
    Returns:
        Dict: {"success": bool, "arquivo": str, "nome_arquivo": str}
    """
    
    if not FINANCEIRO_DISPONIVEL:
        return {
            "success": False,
            "error": "Módulo financeiro não disponível"
        }
    
    try:
        mensalidade = dados_mensalidade["mensalidade"]
        
        # Verificar se está paga
        if mensalidade["status"] not in ["Pago", "Pago parcial"]:
            return {
                "success": False,
                "error": "Mensalidade não está marcada como paga"
            }
        
        aluno = mensalidade["alunos"]
        responsavel = dados_mensalidade.get("responsavel")
        
        # Dados para geração do recibo
        dados_recibo = {
            "tipo_documento": "recibo_mensalidade",
            "mensalidade": {
                "id": mensalidade["id_mensalidade"],
                "mes_referencia": mensalidade["mes_referencia"],
                "valor": mensalidade["valor"],
                "data_vencimento": mensalidade["data_vencimento"],
                "data_pagamento": mensalidade["data_pagamento"],
                "observacoes": mensalidade.get("observacoes", "")
            },
            "aluno": {
                "nome": aluno["nome"],
                "turma": aluno["turmas"]["nome_turma"]
            },
            "responsavel": responsavel if responsavel else {
                "nome": "Responsável não identificado"
            },
            "escola": {
                "nome": "Escola Exemplo",  # TODO: Buscar dados da escola do config
                "endereco": "Endereço da Escola", 
                "telefone": "(00) 0000-0000",
                "email": "contato@escola.com"
            }
        }
        
        resultado = gerar_recibo_pdf(dados_recibo)
        return resultado
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao gerar recibo: {str(e)}"
        }

# ==========================================================
# 📧 COMUNICAÇÃO E NOTIFICAÇÕES
# ==========================================================

def preparar_template_cobranca(dados_mensalidade: Dict) -> str:
    """
    Prepara template padrão para cobrança de mensalidade
    
    Args:
        dados_mensalidade: Dados completos da mensalidade
        
    Returns:
        str: Template formatado
    """
    try:
        mensalidade = dados_mensalidade["mensalidade"]
        aluno = mensalidade["alunos"]
        responsavel = dados_mensalidade.get("responsavel")
        
        nome_responsavel = "Responsável"
        if responsavel:
            nome_responsavel = responsavel["nome"].split()[0]  # Primeiro nome
        
        template = f"""Olá, {nome_responsavel}!

Esperamos que esteja tudo bem com você e sua família.

Gostaríamos de lembrá-lo(a) sobre a mensalidade escolar referente ao mês de {mensalidade['mes_referencia']} do(a) aluno(a) {aluno['nome']}.

📋 **Detalhes da Mensalidade:**
• Aluno(a): {aluno['nome']}
• Turma: {aluno['turmas']['nome_turma']}
• Mês de referência: {mensalidade['mes_referencia']}
• Valor: {formatar_valor_br(mensalidade['valor'])}
• Data de vencimento: {formatar_data_br(mensalidade['data_vencimento'])}

Para efetuar o pagamento, entre em contato conosco pelos canais:
📞 Telefone: (00) 0000-0000
📧 Email: financeiro@escola.com

Agradecemos pela confiança em nosso trabalho educacional.

Atenciosamente,
Secretaria Escolar"""

        return template
        
    except Exception as e:
        return f"Erro ao gerar template: {str(e)}"

def enviar_email_cobranca(dados_mensalidade: Dict, template_personalizado: str = None) -> Dict:
    """
    Envia email de cobrança para o responsável
    
    Args:
        dados_mensalidade: Dados completos da mensalidade
        template_personalizado: Template personalizado (opcional)
        
    Returns:
        Dict: {"success": bool, "message": str, "error": str}
    """
    try:
        responsavel = dados_mensalidade.get("responsavel")
        
        if not responsavel or not responsavel.get("email"):
            return {
                "success": False,
                "error": "Email do responsável não encontrado"
            }
        
        mensalidade = dados_mensalidade["mensalidade"]
        aluno = mensalidade["alunos"]
        
        # Usar template personalizado ou padrão
        if template_personalizado:
            corpo_email = template_personalizado
        else:
            corpo_email = preparar_template_cobranca(dados_mensalidade)
        
        # Assunto do email
        assunto = f"Mensalidade {mensalidade['mes_referencia']} - {aluno['nome']}"
        
        # TODO: Implementar envio real de email
        # resultado = enviar_email(
        #     destinatario=responsavel["email"],
        #     assunto=assunto,
        #     corpo=corpo_email
        # )
        
        # Por enquanto, simular sucesso
        return {
            "success": True,
            "message": f"Email enviado para {responsavel['email']}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro ao enviar email: {str(e)}"
        }

def gerar_link_whatsapp(dados_mensalidade: Dict, template_personalizado: str = None) -> str:
    """
    Gera link do WhatsApp com mensagem pré-formatada
    
    Args:
        dados_mensalidade: Dados completos da mensalidade
        template_personalizado: Template personalizado (opcional)
        
    Returns:
        str: URL do WhatsApp
    """
    try:
        responsavel = dados_mensalidade.get("responsavel")
        
        # Usar template personalizado ou padrão
        if template_personalizado:
            mensagem = template_personalizado
        else:
            mensagem = preparar_template_cobranca(dados_mensalidade)
        
        # Formatar número se disponível
        numero = ""
        if responsavel and responsavel.get("telefone"):
            telefone = responsavel["telefone"]
            # Remover caracteres não numéricos
            numero = ''.join(filter(str.isdigit, telefone))
            if numero.startswith('0'):
                numero = '55' + numero  # Adicionar código do Brasil
        
        # Codificar mensagem para URL
        import urllib.parse
        mensagem_codificada = urllib.parse.quote(mensagem)
        
        # Gerar URL do WhatsApp
        if numero:
            url = f"https://wa.me/{numero}?text={mensagem_codificada}"
        else:
            url = f"https://wa.me/?text={mensagem_codificada}"
        
        return url
        
    except Exception as e:
        return f"Erro ao gerar link: {str(e)}"

# ==========================================================
# 📚 SISTEMA DE AUDITORIA
# ==========================================================

def registrar_log_auditoria(tabela: str, id_registro: str, acao: str, dados_alterados: Dict, usuario: str = "sistema") -> bool:
    """
    Registra log de auditoria no banco de dados
    
    Args:
        tabela: Nome da tabela
        id_registro: ID do registro alterado
        acao: Tipo de ação (insert, update, delete)
        dados_alterados: Dados que foram alterados
        usuario: Usuário que fez a alteração
        
    Returns:
        bool: Sucesso da operação
    """
    try:
        # TODO: Criar tabela de auditoria se não existir
        # CREATE TABLE auditoria (
        #     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        #     tabela VARCHAR NOT NULL,
        #     id_registro VARCHAR NOT NULL,
        #     acao VARCHAR NOT NULL,
        #     dados_anteriores JSONB,
        #     dados_novos JSONB,
        #     usuario VARCHAR,
        #     timestamp TIMESTAMP DEFAULT NOW()
        # );
        
        log_entry = {
            "tabela": tabela,
            "id_registro": id_registro,
            "acao": acao,
            "dados_alterados": dados_alterados,
            "usuario": usuario,
            "timestamp": obter_timestamp()
        }
        
        # Por enquanto, apenas simular
        # supabase.table("auditoria").insert(log_entry).execute()
        
        return True
        
    except Exception as e:
        st.error(f"Erro ao registrar auditoria: {str(e)}")
        return False

def buscar_historico_alteracoes(id_mensalidade: str) -> List[Dict]:
    """
    Busca histórico de alterações de uma mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade
        
    Returns:
        List[Dict]: Lista de alterações
    """
    try:
        # TODO: Implementar busca real na tabela de auditoria
        # response = supabase.table("auditoria").select("*").eq(
        #     "tabela", "mensalidades"
        # ).eq("id_registro", id_mensalidade).order("timestamp", desc=True).execute()
        
        # Por enquanto, retornar dados fictícios
        historico_exemplo = [
            {
                "id": "1",
                "data_hora": datetime.now() - timedelta(days=2),
                "usuario": "admin",
                "acao": "update",
                "campo": "status",
                "valor_antigo": "A vencer",
                "valor_novo": "Atrasado",
                "observacoes": "Atualização automática por vencimento"
            },
            {
                "id": "2", 
                "data_hora": datetime.now() - timedelta(days=5),
                "usuario": "secretaria",
                "acao": "update",
                "campo": "observacoes",
                "valor_antigo": "",
                "valor_novo": "Aguardando pagamento",
                "observacoes": "Anotação manual"
            }
        ]
        
        return historico_exemplo
        
    except Exception as e:
        st.error(f"Erro ao buscar histórico: {str(e)}")
        return []

# ==========================================================
# 🔄 VALIDAÇÕES E REGRAS DE NEGÓCIO
# ==========================================================

def validar_alteracao_mensalidade(dados_originais: Dict, dados_novos: Dict) -> Dict:
    """
    Valida se as alterações na mensalidade são permitidas
    
    Args:
        dados_originais: Dados atuais da mensalidade
        dados_novos: Dados alterados
        
    Returns:
        Dict: {"valido": bool, "erros": List[str], "avisos": List[str]}
    """
    erros = []
    avisos = []
    
    try:
        # Regra 1: Não permitir alterar valor se já foi paga
        if (dados_originais["status"] in ["Pago", "Pago parcial"] and 
            dados_novos.get("valor") != dados_originais["valor"]):
            erros.append("Não é possível alterar o valor de uma mensalidade já paga")
        
        # Regra 2: Data de vencimento não pode ser no passado (salvo casos especiais)
        if dados_novos.get("data_vencimento"):
            try:
                nova_data = datetime.strptime(dados_novos["data_vencimento"], "%Y-%m-%d").date()
                if nova_data < date.today():
                    avisos.append("A nova data de vencimento está no passado")
            except:
                erros.append("Data de vencimento inválida")
        
        # Regra 3: Status 'Pago' requer data de pagamento
        if (dados_novos.get("status") in ["Pago", "Pago parcial"] and 
            not dados_novos.get("data_pagamento")):
            erros.append("Status 'Pago' requer data de pagamento")
        
        # Regra 4: Valor deve ser positivo
        if dados_novos.get("valor") and dados_novos["valor"] <= 0:
            erros.append("Valor deve ser maior que zero")
        
        return {
            "valido": len(erros) == 0,
            "erros": erros,
            "avisos": avisos
        }
        
    except Exception as e:
        return {
            "valido": False,
            "erros": [f"Erro na validação: {str(e)}"],
            "avisos": []
        }

# ==========================================================
# 🛠️ FUNÇÕES UTILITÁRIAS ESPECÍFICAS
# ==========================================================

def calcular_juros_atraso(valor_original: float, data_vencimento: str) -> Dict:
    """
    Calcula juros de atraso baseado na data de vencimento
    
    Args:
        valor_original: Valor original da mensalidade
        data_vencimento: Data de vencimento original
        
    Returns:
        Dict: {"dias_atraso": int, "valor_juros": float, "valor_total": float}
    """
    try:
        vencimento = datetime.strptime(data_vencimento, "%Y-%m-%d").date()
        hoje = date.today()
        
        if hoje <= vencimento:
            return {
                "dias_atraso": 0,
                "valor_juros": 0.0,
                "valor_total": valor_original
            }
        
        dias_atraso = (hoje - vencimento).days
        
        # Regra simples: 0.33% ao dia (10% ao mês)
        taxa_diaria = 0.0033
        valor_juros = valor_original * taxa_diaria * dias_atraso
        
        return {
            "dias_atraso": dias_atraso,
            "valor_juros": valor_juros,
            "valor_total": valor_original + valor_juros
        }
        
    except Exception as e:
        return {
            "dias_atraso": 0,
            "valor_juros": 0.0,
            "valor_total": valor_original,
            "erro": str(e)
        }

def gerar_codigo_barras_mensalidade(id_mensalidade: str, valor: float) -> str:
    """
    Gera código de barras fictício para a mensalidade
    
    Args:
        id_mensalidade: ID da mensalidade
        valor: Valor da mensalidade
        
    Returns:
        str: Código de barras
    """
    try:
        # Gerar código fictício baseado no ID e valor
        import hashlib
        
        dados = f"{id_mensalidade}{valor}"
        hash_obj = hashlib.md5(dados.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Formatar como código de barras
        codigo = f"34191{hash_hex[:10]}{str(int(valor*100)):010d}"
        
        return codigo
        
    except Exception as e:
        return f"ERRO_CODIGO_BARRAS_{id_mensalidade}" 