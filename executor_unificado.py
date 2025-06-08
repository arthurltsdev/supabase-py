"""
Executor Unificado - Supabase Functions
=======================================

Este módulo mapeia as chamadas de função do OpenAI Function Calling
para as funções implementadas em supabase_functions.py
"""

import json
from typing import Any, Dict
from supabase_functions import (
    identificar_responsaveis_nao_cadastrados,
    listar_responsaveis,
    listar_alunos,
    listar_turmas,
    analisar_estatisticas_extrato,
    cadastrar_responsavel_completo,
    cadastrar_responsavel_e_vincular_aluno,
    buscar_aluno_por_nome,
    vincular_aluno_responsavel,
    listar_pagamentos_nao_identificados,
    listar_registros_extrato_com_responsaveis_cadastrados,
    processar_responsaveis_extrato_pix,
    buscar_responsavel_por_nome,
    verificar_responsaveis_financeiros,
    registrar_pagamento,
    atualizar_dados_aluno,
    atualizar_dados_responsavel,
    listar_pagamentos,
    listar_mensalidades,
    consultar_extrato_pix,
    cadastrar_aluno,
    remover_pagamentos_extrato,
    atualizar_responsaveis_extrato_por_nome,
    listar_pagamentos_por_responsavel_ordenados,
    remover_aluno
)

# Mapeamento de funções disponíveis
FUNCTION_MAP = {
    "identificar_responsaveis_nao_cadastrados": identificar_responsaveis_nao_cadastrados,
    "listar_responsaveis": listar_responsaveis,
    "listar_alunos": listar_alunos,
    "listar_turmas": listar_turmas,
    "analisar_estatisticas_extrato": analisar_estatisticas_extrato,
    "cadastrar_responsavel_completo": cadastrar_responsavel_completo,
    "cadastrar_responsavel_e_vincular_aluno": cadastrar_responsavel_e_vincular_aluno,
    "buscar_aluno_por_nome": buscar_aluno_por_nome,
    "vincular_aluno_responsavel": vincular_aluno_responsavel,
    "listar_pagamentos_nao_identificados": listar_pagamentos_nao_identificados,
    "listar_registros_extrato_com_responsaveis_cadastrados": listar_registros_extrato_com_responsaveis_cadastrados,
    "processar_responsaveis_extrato_pix": processar_responsaveis_extrato_pix,
    "buscar_responsavel_por_nome": buscar_responsavel_por_nome,
    "verificar_responsaveis_financeiros": verificar_responsaveis_financeiros,
    "registrar_pagamento": registrar_pagamento,
    "atualizar_dados_aluno": atualizar_dados_aluno,
    "atualizar_dados_responsavel": atualizar_dados_responsavel,
    "listar_pagamentos": listar_pagamentos,
    "listar_mensalidades": listar_mensalidades,
    "consultar_extrato_pix": consultar_extrato_pix,
    "cadastrar_aluno": cadastrar_aluno,
    "remover_pagamentos_extrato": remover_pagamentos_extrato,
    "atualizar_responsaveis_extrato_por_nome": atualizar_responsaveis_extrato_por_nome,
    "listar_pagamentos_por_responsavel_ordenados": listar_pagamentos_por_responsavel_ordenados,
    "remover_aluno": remover_aluno
}

def executar_function(function_name: str, **kwargs) -> Dict[str, Any]:
    """
    Executa uma função do Supabase baseada no nome e parâmetros fornecidos.
    
    Args:
        function_name (str): Nome da função a ser executada
        **kwargs: Parâmetros da função
        
    Returns:
        Dict[str, Any]: Resultado da execução da função
    """
    try:
        # Verifica se a função existe
        if function_name not in FUNCTION_MAP:
            return {
                "status": "erro",
                "erro": f"Função '{function_name}' não encontrada",
                "funcoes_disponiveis": list(FUNCTION_MAP.keys())
            }
        
        # Obtém a função
        func = FUNCTION_MAP[function_name]
        
        # Executa a função com os parâmetros fornecidos
        resultado = func(**kwargs)
        
        # Garante que o resultado seja um dicionário
        if not isinstance(resultado, dict):
            resultado = {"resultado": resultado}
        
        # Adiciona status de sucesso se não existir
        if "success" not in resultado:
            resultado["status"] = "sucesso"
        else:
            # Mapeia success para status para padronização
            resultado["status"] = "sucesso" if resultado.get("success") else "erro"
        
        return resultado
        
    except Exception as e:
        return {
            "status": "erro",
            "erro": f"Erro ao executar {function_name}: {str(e)}",
            "funcao": function_name,
            "parametros": kwargs
        }

# Função para teste
if __name__ == "__main__":
    print("🧪 Testando executor...")
    
    # Teste simples
    resultado = executar_function("listar_pagamentos_nao_identificados")
    print(resultado)
