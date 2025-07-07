#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📊 BASE - Estruturas de Dados e Configurações
============================================

Define as estruturas das tabelas do banco de dados e funções utilitárias comuns.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from supabase import create_client
from dotenv import load_dotenv
import uuid
import random

# Carrega as variáveis do .env
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================================
# 📋 ESTRUTURAS DAS TABELAS
# ==========================================================

@dataclass
class AlunoSchema:
    """Estrutura da tabela 'alunos'"""
    id: str                    # PRIMARY KEY - Formato: ALU_XXXXXX
    nome: str                  # NOT NULL - Nome completo do aluno
    id_turma: str             # FOREIGN KEY - Referência para turmas.id
    turno: Optional[str]       # Manhã, Tarde, Integral, Horário Extendido
    data_nascimento: Optional[str]  # Formato: YYYY-MM-DD
    dia_vencimento: Optional[str]   # Dia do mês (1-31)
    data_matricula: Optional[str]   # Formato: YYYY-MM-DD
    valor_mensalidade: Optional[float]  # Valor decimal
    mensalidades_geradas: Optional[bool]  # Default: False
    inserted_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]   # Timestamp de atualização
    situacao: Optional[str]     # Ativo, Inativo, Transferido, Desistente
    data_saida: Optional[str]   # Formato: YYYY-MM-DD
    motivo_saida: Optional[str] # Transferido, Desistente, Outro

@dataclass
class ResponsavelSchema:
    """Estrutura da tabela 'responsaveis'"""
    id: str                    # PRIMARY KEY - Formato: RES_XXXXXX
    nome: str                  # NOT NULL - Nome completo
    cpf: Optional[str]         # CPF (apenas números)
    telefone: Optional[str]    # Telefone de contato
    email: Optional[str]       # Email de contato
    endereco: Optional[str]    # Endereço completo
    tipo_relacao: Optional[str]  # pai, mãe, avô, avó, etc.
    responsavel_financeiro: Optional[bool]  # Default: False
    inserted_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]   # Timestamp de atualização

@dataclass
class TurmaSchema:
    """Estrutura da tabela 'turmas'"""
    id: str                    # PRIMARY KEY - Formato: INF-XXX, FUN-XXX
    nome_turma: str           # NOT NULL - Nome da turma
    descricao: Optional[str]   # Descrição adicional
    ano_letivo: Optional[str]  # Ano letivo
    capacidade_maxima: Optional[int]  # Número máximo de alunos
    inserted_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]   # Timestamp de atualização

@dataclass
class AlunoResponsavelSchema:
    """Estrutura da tabela 'alunos_responsaveis' (tabela de ligação)"""
    id: str                    # PRIMARY KEY - Formato: AR_XXXXXXXX
    id_aluno: str             # FOREIGN KEY - Referência para alunos.id
    id_responsavel: str       # FOREIGN KEY - Referência para responsaveis.id
    tipo_relacao: Optional[str]  # pai, mãe, avô, avó, etc.
    responsavel_financeiro: Optional[bool]  # Default: False
    created_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]  # Timestamp de atualização

@dataclass
class PagamentoSchema:
    """Estrutura da tabela 'pagamentos'"""
    id_pagamento: str         # PRIMARY KEY - Formato: PAG_XXXXXX
    id_responsavel: str       # FOREIGN KEY - Referência para responsaveis.id
    id_aluno: str            # FOREIGN KEY - Referência para alunos.id
    data_pagamento: str       # NOT NULL - Formato: YYYY-MM-DD
    valor: float             # NOT NULL - Valor do pagamento
    tipo_pagamento: str       # matricula, mensalidade, material, etc.
    forma_pagamento: Optional[str]  # PIX, dinheiro, cartão, etc.
    descricao: Optional[str]  # Descrição adicional
    origem_extrato: Optional[bool]  # Se veio do extrato PIX
    id_extrato: Optional[str]  # Referência para extrato_pix.id
    inserted_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]   # Timestamp de atualização

@dataclass
class MensalidadeSchema:
    """Estrutura da tabela 'mensalidades'"""
    id_mensalidade: str       # PRIMARY KEY - Formato: MENS_XXXXXX
    id_aluno: str            # FOREIGN KEY - Referência para alunos.id
    mes_referencia: str       # NOT NULL - Formato: MM/YYYY
    valor: float             # NOT NULL - Valor da mensalidade
    data_vencimento: str      # NOT NULL - Formato: YYYY-MM-DD
    status: str              # A vencer, Vencida, Pago, Pago parcial
    id_pagamento: Optional[str]  # FOREIGN KEY - Referência para pagamentos.id_pagamento
    data_pagamento: Optional[str]  # Formato: YYYY-MM-DD
    observacoes: Optional[str]  # Observações adicionais
    inserted_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]   # Timestamp de atualização

@dataclass
class ExtratoPIXSchema:
    """Estrutura da tabela 'extrato_pix'"""
    id: str                   # PRIMARY KEY - UUID
    nome_remetente: str       # NOT NULL - Nome do remetente do PIX
    valor: float             # NOT NULL - Valor do PIX
    data_pagamento: str       # NOT NULL - Formato: YYYY-MM-DD
    observacoes: Optional[str]  # Observações do PIX
    status: str              # novo, registrado, ignorado
    id_responsavel: Optional[str]  # FOREIGN KEY - Referência para responsaveis.id
    id_aluno: Optional[str]   # FOREIGN KEY - Referência para alunos.id
    tipo_pagamento: Optional[str]  # matricula, mensalidade, etc.
    atualizado_em: Optional[str]  # Timestamp de atualização
    observacoes_sistema: Optional[str]  # Observações do sistema

@dataclass
class CobrancaSchema:
    """Estrutura da tabela 'cobrancas'"""
    id_cobranca: str          # PRIMARY KEY - Formato: COB_XXXXXX
    id_aluno: str            # FOREIGN KEY - Referência para alunos.id
    id_responsavel: Optional[str]  # FOREIGN KEY - Referência para responsaveis.id
    titulo: str              # NOT NULL - Título da cobrança
    descricao: Optional[str]  # Descrição detalhada
    valor: float             # NOT NULL - Valor da cobrança
    data_vencimento: str      # NOT NULL - Formato: YYYY-MM-DD
    data_pagamento: Optional[str]  # Formato: YYYY-MM-DD (NULL se não pago)
    status: str              # Pendente, Pago, Vencido, Cancelado
    tipo_cobranca: str       # formatura, evento, taxa, material, uniforme, divida, renegociacao, outros
    grupo_cobranca: Optional[str]  # ID para agrupar parcelas relacionadas
    parcela_numero: int      # Número da parcela (padrão 1)
    parcela_total: int       # Total de parcelas (padrão 1)
    id_pagamento: Optional[str]  # FOREIGN KEY - Referência para pagamentos.id_pagamento
    observacoes: Optional[str]  # Observações adicionais
    prioridade: int          # 1=baixa, 2=normal, 3=média, 4=alta, 5=urgente
    inserted_at: Optional[str]  # Timestamp de criação
    updated_at: Optional[str]   # Timestamp de atualização

# ==========================================================
# 🛠️ FUNÇÕES UTILITÁRIAS
# ==========================================================

def gerar_id_aluno() -> str:
    """Gera ID único para aluno no formato ALU_XXXXXX"""
    return f"ALU_{random.randint(100000, 999999):06d}"

def gerar_id_responsavel() -> str:
    """Gera ID único para responsável no formato RES_XXXXXX"""
    return f"RES_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_pagamento() -> str:
    """Gera ID único para pagamento no formato PAG_XXXXXX"""
    return f"PAG_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_vinculo() -> str:
    """Gera ID único para vínculo aluno-responsável no formato AR_XXXXXXXX"""
    return f"AR_{str(uuid.uuid4().int)[:8].upper()}"

def gerar_id_mensalidade() -> str:
    """Gera ID único para mensalidade no formato MENS_XXXXXX"""
    return f"MENS_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_id_cobranca() -> str:
    """Gera ID único para cobrança no formato COB_XXXXXX"""
    return f"COB_{str(uuid.uuid4().int)[:6].upper()}"

def gerar_grupo_cobranca(tipo: str, id_aluno: str, ano: str = None) -> str:
    """
    Gera ID único para grupo de cobranças relacionadas
    
    Args:
        tipo: Tipo da cobrança (formatura, evento, etc.)
        id_aluno: ID do aluno
        ano: Ano opcional (padrão: ano atual)
        
    Returns:
        str: ID do grupo no formato TIPO_ANO_IDALUNO
    """
    if not ano:
        from datetime import datetime
        ano = str(datetime.now().year)
    
    return f"{tipo.upper()}_{ano}_{id_aluno}"

def formatar_data_br(data_iso: str) -> str:
    """Converte data ISO (YYYY-MM-DD) para formato brasileiro (DD/MM/YYYY)"""
    if not data_iso:
        return "Não informado"
    try:
        data_obj = datetime.strptime(data_iso, "%Y-%m-%d")
        return data_obj.strftime("%d/%m/%Y")
    except:
        return data_iso

def formatar_valor_br(valor: float) -> str:
    """Formata valor para formato brasileiro (R$ 1.234,56)"""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def validar_cpf(cpf: str) -> bool:
    """Valida CPF brasileiro"""
    if not cpf:
        return False
    
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se não são todos iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação dos dígitos verificadores
    def calcular_digito(cpf_parcial):
        soma = 0
        for i, digito in enumerate(cpf_parcial):
            soma += int(digito) * (len(cpf_parcial) + 1 - i)
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    # Verifica primeiro dígito
    if int(cpf[9]) != calcular_digito(cpf[:9]):
        return False
    
    # Verifica segundo dígito
    if int(cpf[10]) != calcular_digito(cpf[:10]):
        return False
    
    return True

def tratar_valores_none(dados: Dict[str, Any], schema_class) -> Dict[str, Any]:
    """Trata valores None de acordo com o schema da tabela"""
    dados_tratados = {}
    
    for field_name, field_type in schema_class.__annotations__.items():
        valor = dados.get(field_name)
        
        # Se é Optional, pode ser None
        if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            if valor is None:
                dados_tratados[field_name] = None
            else:
                dados_tratados[field_name] = valor
        else:
            # Campo obrigatório - aplicar valor padrão se None
            if valor is None:
                if field_type == str:
                    dados_tratados[field_name] = "Não informado"
                elif field_type == float:
                    dados_tratados[field_name] = 0.0
                elif field_type == bool:
                    dados_tratados[field_name] = False
                else:
                    dados_tratados[field_name] = valor
            else:
                dados_tratados[field_name] = valor
    
    return dados_tratados

def obter_timestamp() -> str:
    """Retorna timestamp atual no formato ISO"""
    return datetime.now().isoformat()

# ==========================================================
# 📊 MAPEAMENTO DE TABELAS
# ==========================================================

TABELAS_SCHEMA = {
    "alunos": AlunoSchema,
    "responsaveis": ResponsavelSchema,
    "turmas": TurmaSchema,
    "alunos_responsaveis": AlunoResponsavelSchema,
    "pagamentos": PagamentoSchema,
    "mensalidades": MensalidadeSchema,
    "extrato_pix": ExtratoPIXSchema,
    "cobrancas": CobrancaSchema
}

# Status válidos para cada tabela
STATUS_VALIDOS = {
    "mensalidades": ["A vencer", "Atrasado", "Pago", "Pago parcial","Cancelado", "Baixa"],
    "extrato_pix": ["novo", "registrado", "ignorado"],
    "pagamentos": ["pendente", "confirmado", "cancelado"],
    "cobrancas": ["Pendente", "Pago", "Vencido", "Cancelado"]
}

# Tipos de relação válidos
TIPOS_RELACAO = ["Pai", "Mãe", "Avô", "Avó", "Tio", "Tia", "Responsável Legal", "Outro"]

# Tipos de pagamento válidos
TIPOS_PAGAMENTO = ["Matrícula", "Mensalidade", "Taxa de Material","Livro Didático", "Fardamento", "Evento", "Outro"]

# Tipos de cobrança válidos
TIPOS_COBRANCA = [
    "formatura", "evento", "taxa", "material", "uniforme", 
    "divida", "renegociacao", "outros"
]

# Mapeamento de tipos de cobrança para exibição
TIPOS_COBRANCA_DISPLAY = {
    "formatura": "🎓 Formatura",
    "evento": "🎉 Evento",
    "taxa": "💰 Taxa",
    "material": "📚 Material Escolar",
    "uniforme": "👕 Uniforme",
    "divida": "⚠️ Dívida Anterior",
    "renegociacao": "🔄 Renegociação",
    "outros": "📝 Outros"
}

# Níveis de prioridade
PRIORIDADES_COBRANCA = {
    1: "🔹 Baixa",
    2: "🔸 Normal", 
    3: "🟡 Média",
    4: "🟠 Alta",
    5: "🔴 Urgente"
}

# Formas de pagamento válidas
FORMAS_PAGAMENTO = ["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Boleto", "Transferência"]

# Turnos válidos
TURNOS_VALIDOS = ["Manhã", "Tarde", "Integral", "Horário Extendido"] 