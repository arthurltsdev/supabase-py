#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 SISTEMA DE TESTES - GESTÃO ESCOLAR
====================================

Testes organizados por domínios funcionais para garantir
a qualidade e consistência das funcionalidades.

📁 Estrutura de Testes:

🎓 test_pedagogico.py:
   - Testes de gestão de alunos, responsáveis e turmas
   - Validações de cadastros e vínculos
   - Consultas e filtros educacionais

💰 test_financeiro.py:
   - Testes de processamento de pagamentos
   - Gestão de mensalidades
   - Extrato PIX e validações financeiras

🏢 test_organizacional.py:
   - Testes de validações e consistência
   - Relatórios e estatísticas
   - Funções de manutenção

🔧 test_base.py:
   - Testes das funções utilitárias
   - Validações de estruturas de dados
   - Configurações e conexões
"""

import sys
import os

# Adicionar o diretório raiz ao path para importar os models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurações de teste
TEST_CONFIG = {
    "database": "test",
    "verbose": True,
    "cleanup_after_tests": True,
    "generate_test_data": True
}

# Dados de teste padrão
TEST_DATA = {
    "turma_teste": {
        "id": "TEST_TURMA_001",
        "nome_turma": "Teste Infantil",
        "descricao": "Turma para testes automatizados",
        "ano_letivo": "2024"
    },
    "aluno_teste": {
        "nome": "João Silva Teste",
        "turno": "Matutino",
        "data_nascimento": "2018-05-15",
        "dia_vencimento": "5",
        "valor_mensalidade": 450.0
    },
    "responsavel_teste": {
        "nome": "Maria Silva Teste",
        "cpf": "12345678901",
        "telefone": "(11) 99999-9999",
        "email": "maria.teste@email.com",
        "endereco": "Rua Teste, 123",
        "tipo_relacao": "mãe"
    },
    "pagamento_teste": {
        "valor": 450.0,
        "tipo_pagamento": "mensalidade",
        "forma_pagamento": "PIX",
        "descricao": "Pagamento de teste automatizado"
    }
}

__version__ = "1.0.0"
__author__ = "Sistema de Gestão Escolar - Testes"
