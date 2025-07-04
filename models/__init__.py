#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📚 SISTEMA DE MODELS - GESTÃO ESCOLAR
====================================

Organização modular das funcionalidades do sistema por domínios:

🎓 PEDAGÓGICO (pedagogico.py):
   - Gestão de alunos, responsáveis, turmas
   - Matrículas, vínculos, cadastros
   - Consultas e filtros educacionais

💰 FINANCEIRO (financeiro.py):
   - Processamento de pagamentos
   - Gestão de mensalidades
   - Extratos PIX e cobranças

🏢 ORGANIZACIONAL (organizacional.py):
   - Configurações do sistema
   - Relatórios e estatísticas
   - Validações e consistência

📊 BASE (base.py):
   - Estruturas de dados das tabelas
   - Funções utilitárias comuns
   - Configurações de conexão
"""

from .base import *
from .pedagogico import *
from .financeiro import *
from .organizacional import *

__version__ = "1.0.0"
__author__ = "Sistema de Gestão Escolar"

# Metadados dos modelos
MODELS_INFO = {
    "pedagogico": {
        "description": "Gestão de alunos, responsáveis e estrutura educacional",
        "tables": ["alunos", "responsaveis", "alunos_responsaveis", "turmas"],
        "main_functions": [
            "buscar_alunos_por_turmas",
            "cadastrar_responsavel_e_vincular", 
            "buscar_informacoes_completas_aluno"
        ]
    },
    "financeiro": {
        "description": "Processamento de pagamentos e gestão financeira",
        "tables": ["pagamentos", "mensalidades", "extrato_pix"],
        "main_functions": [
            "registrar_pagamento_do_extrato",
            "registrar_pagamentos_multiplos_do_extrato",
            "listar_mensalidades_disponiveis_aluno"
        ]
    },
    "organizacional": {
        "description": "Relatórios, validações e configurações do sistema",
        "tables": ["*"],
        "main_functions": [
            "verificar_consistencia_extrato_pagamentos",
            "obter_estatisticas_extrato",
            "atualizar_responsaveis_extrato_pix"
        ]
    }
} 