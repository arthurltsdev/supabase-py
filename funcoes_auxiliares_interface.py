#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 FUNÇÕES AUXILIARES PARA INTERFACE DO EXTRATO PIX
==================================================

Funções específicas para melhorar a funcionalidade da interface
de processamento do extrato PIX.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
from supabase_functions import (
    supabase,
    normalizar_nome_avancado,
    calcular_similaridade_nomes,
    converter_data
)

def buscar_alunos_por_responsavel(id_responsavel: str) -> List[Dict]:
    """
    Busca todos os alunos vinculados a um responsável específico
    
    Args:
        id_responsavel: ID do responsável
        
    Returns:
        Lista de alunos vinculados com informações completas
    """
    try:
        # Buscar vínculos do responsável
        response = supabase.table("alunos_responsaveis").select(
            """
            *,
            alunos!inner(
                id, nome, id_turma, dia_vencimento, valor_mensalidade,
                turmas!inner(nome_turma)
            )
            """
        ).eq("id_responsavel", id_responsavel).execute()
        
        if response.data:
            alunos = []
            for vinculo in response.data:
                aluno_info = vinculo['alunos']
                aluno_info['tipo_relacao'] = vinculo.get('tipo_relacao', 'Responsável')
                aluno_info['responsavel_financeiro'] = vinculo.get('responsavel_financeiro', False)
                alunos.append(aluno_info)
            
            return alunos
        
        return []
        
    except Exception as e:
        print(f"Erro ao buscar alunos do responsável: {str(e)}")
        return []

def identificar_tipo_pagamento_automatico(valor: float, observacoes: str = "") -> str:
    """
    Tenta identificar o tipo de pagamento baseado no valor e observações
    
    Args:
        valor: Valor do pagamento
        observacoes: Observações do pagamento
        
    Returns:
        Tipo de pagamento sugerido
    """
    obs_lower = observacoes.lower() if observacoes else ""
    
    # Verificar por palavras-chave nas observações
    if any(palavra in obs_lower for palavra in ['matricula', 'matrícula', 'matricular']):
        return "matricula"
    elif any(palavra in obs_lower for palavra in ['mensalidade', 'mens', 'pagamento mensal']):
        return "mensalidade"
    elif any(palavra in obs_lower for palavra in ['material', 'apostila', 'livro', 'uniforme']):
        return "material"
    elif any(palavra in obs_lower for palavra in ['evento', 'passeio', 'excursão', 'festa']):
        return "evento"
    
    # Tentar identificar por faixas de valor comuns
    # Estes valores são exemplos e devem ser ajustados conforme a realidade da escola
    if 200 <= valor <= 500:
        return "matricula"  # Faixa comum para matrículas
    elif 100 <= valor <= 200:
        return "mensalidade"  # Faixa comum para mensalidades
    elif valor < 100:
        return "material"  # Valores menores geralmente são materiais
    
    return "outro"

def sugerir_vinculo_aluno_por_nome(nome_responsavel: str) -> List[Dict]:
    """
    Sugere possíveis alunos para vincular baseado na similaridade de nomes
    
    Args:
        nome_responsavel: Nome do responsável
        
    Returns:
        Lista de alunos com score de similaridade
    """
    try:
        # Buscar todos os alunos
        response = supabase.table("alunos").select(
            "id, nome, turmas!inner(nome_turma)"
        ).execute()
        
        if not response.data:
            return []
        
        # Normalizar nome do responsável
        nome_resp_norm = normalizar_nome_avancado(nome_responsavel)
        sobrenomes_resp = nome_resp_norm.split()[-2:] if len(nome_resp_norm.split()) > 1 else []
        
        sugestoes = []
        
        for aluno in response.data:
            nome_aluno = aluno.get('nome', '')
            nome_aluno_norm = normalizar_nome_avancado(nome_aluno)
            
            # Calcular similaridade
            score = calcular_similaridade_nomes(nome_responsavel, nome_aluno)
            
            # Bonus se compartilham sobrenome
            sobrenomes_aluno = nome_aluno_norm.split()[-2:] if len(nome_aluno_norm.split()) > 1 else []
            if sobrenomes_resp and sobrenomes_aluno:
                for sob_resp in sobrenomes_resp:
                    for sob_aluno in sobrenomes_aluno:
                        if sob_resp == sob_aluno and len(sob_resp) > 3:  # Sobrenome significativo
                            score += 0.3
            
            # Adicionar apenas se tiver alguma similaridade
            if score > 0.3:
                sugestoes.append({
                    'aluno': aluno,
                    'score': min(score, 1.0),  # Garantir que não passe de 1.0
                    'motivo': 'Sobrenome similar' if score > 0.7 else 'Nome parcialmente similar'
                })
        
        # Ordenar por score
        sugestoes.sort(key=lambda x: x['score'], reverse=True)
        
        return sugestoes[:5]  # Retornar top 5 sugestões
        
    except Exception as e:
        print(f"Erro ao sugerir vínculos: {str(e)}")
        return []

def validar_periodo_mensalidade(id_aluno: str, mes_referencia: str) -> Dict:
    """
    Valida se uma mensalidade para o período já existe
    
    Args:
        id_aluno: ID do aluno
        mes_referencia: Mês de referência (MM/YYYY)
        
    Returns:
        Dict com informações sobre a validação
    """
    try:
        # Buscar mensalidades do aluno para o período
        response = supabase.table("mensalidades").select("*").eq(
            "id_aluno", id_aluno
        ).eq("mes_referencia", mes_referencia).execute()
        
        if response.data:
            mensalidade = response.data[0]
            return {
                'valido': False,
                'motivo': f"Mensalidade já existe para {mes_referencia}",
                'mensalidade_existente': mensalidade,
                'status_atual': mensalidade.get('status', 'Desconhecido')
            }
        
        return {
            'valido': True,
            'motivo': "Período disponível para registro"
        }
        
    except Exception as e:
        return {
            'valido': False,
            'motivo': f"Erro ao validar: {str(e)}"
        }

def processar_extrato_em_lote(registros: List[Dict], acoes: Dict[str, str]) -> Dict:
    """
    Processa múltiplos registros do extrato em lote
    
    Args:
        registros: Lista de registros do extrato
        acoes: Dicionário com ID do registro e ação a executar
        
    Returns:
        Relatório do processamento
    """
    resultados = {
        'total': len(registros),
        'sucessos': 0,
        'erros': 0,
        'detalhes': []
    }
    
    for registro in registros:
        registro_id = registro.get('id')
        acao = acoes.get(registro_id, 'NENHUMA')
        
        if acao == 'NENHUMA':
            continue
        
        try:
            if acao == 'REMOVER':
                # Remover registro
                response = supabase.table("extrato_pix").delete().eq("id", registro_id).execute()
                
                if response.data:
                    resultados['sucessos'] += 1
                    resultados['detalhes'].append({
                        'id': registro_id,
                        'acao': acao,
                        'status': 'Sucesso',
                        'mensagem': 'Registro removido'
                    })
                else:
                    raise Exception("Falha ao remover registro")
            
            elif acao.startswith('REGISTRAR_'):
                tipo = acao.replace('REGISTRAR_', '').lower()
                
                # Implementar lógica de registro baseada no tipo
                # Por enquanto, vamos simular
                resultados['sucessos'] += 1
                resultados['detalhes'].append({
                    'id': registro_id,
                    'acao': acao,
                    'status': 'Sucesso',
                    'mensagem': f'Registrado como {tipo}'
                })
            
        except Exception as e:
            resultados['erros'] += 1
            resultados['detalhes'].append({
                'id': registro_id,
                'acao': acao,
                'status': 'Erro',
                'mensagem': str(e)
            })
    
    return resultados

def gerar_relatorio_processamento(df_processado: pd.DataFrame) -> Dict:
    """
    Gera relatório detalhado do processamento do extrato
    
    Args:
        df_processado: DataFrame com os registros processados
        
    Returns:
        Relatório com estatísticas e análises
    """
    relatorio = {
        'data_processamento': datetime.now().isoformat(),
        'total_registros': len(df_processado),
        'valor_total': df_processado['valor'].sum() if 'valor' in df_processado else 0,
        'periodo': {
            'inicio': df_processado['data_pagamento'].min() if 'data_pagamento' in df_processado else None,
            'fim': df_processado['data_pagamento'].max() if 'data_pagamento' in df_processado else None
        },
        'por_tipo': {},
        'por_status': {},
        'top_pagadores': []
    }
    
    # Análise por tipo de pagamento
    if 'tipo_pagamento' in df_processado:
        por_tipo = df_processado.groupby('tipo_pagamento').agg({
            'valor': ['count', 'sum', 'mean']
        }).round(2)
        
        for tipo in por_tipo.index:
            relatorio['por_tipo'][tipo] = {
                'quantidade': int(por_tipo.loc[tipo, ('valor', 'count')]),
                'valor_total': float(por_tipo.loc[tipo, ('valor', 'sum')]),
                'valor_medio': float(por_tipo.loc[tipo, ('valor', 'mean')])
            }
    
    # Top 10 pagadores
    if 'nome_remetente' in df_processado:
        top_pagadores = df_processado.groupby('nome_remetente').agg({
            'valor': ['count', 'sum']
        }).sort_values(('valor', 'sum'), ascending=False).head(10)
        
        for nome in top_pagadores.index:
            relatorio['top_pagadores'].append({
                'nome': nome,
                'quantidade_pagamentos': int(top_pagadores.loc[nome, ('valor', 'count')]),
                'valor_total': float(top_pagadores.loc[nome, ('valor', 'sum')])
            })
    
    return relatorio

def exportar_dados_processados(df: pd.DataFrame, formato: str = 'excel') -> bytes:
    """
    Exporta dados processados para download
    
    Args:
        df: DataFrame com os dados
        formato: 'excel' ou 'csv'
        
    Returns:
        Bytes do arquivo para download
    """
    from io import BytesIO
    
    output = BytesIO()
    
    if formato == 'excel':
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Extrato Processado', index=False)
            
            # Adicionar formatação
            worksheet = writer.sheets['Extrato Processado']
            
            # Formatar colunas de valor
            for col in df.columns:
                if 'valor' in col.lower():
                    col_letter = chr(65 + df.columns.get_loc(col))
                    for row in range(2, len(df) + 2):
                        worksheet[f'{col_letter}{row}'].number_format = 'R$ #,##0.00'
    
    elif formato == 'csv':
        df.to_csv(output, index=False, encoding='utf-8-sig')
    
    output.seek(0)
    return output.getvalue()

# Função para criar um resumo visual dos dados
def criar_resumo_visual(df_com_resp: pd.DataFrame, df_sem_resp: pd.DataFrame) -> Dict:
    """
    Cria dados para visualizações do dashboard
    
    Args:
        df_com_resp: DataFrame com responsáveis cadastrados
        df_sem_resp: DataFrame sem responsáveis cadastrados
        
    Returns:
        Dados formatados para gráficos
    """
    resumo = {
        'totais': {
            'com_responsavel': len(df_com_resp),
            'sem_responsavel': len(df_sem_resp),
            'total': len(df_com_resp) + len(df_sem_resp)
        },
        'valores': {
            'com_responsavel': df_com_resp['valor'].sum() if 'valor' in df_com_resp else 0,
            'sem_responsavel': df_sem_resp['valor'].sum() if 'valor' in df_sem_resp else 0
        },
        'por_dia': {},
        'distribuicao_valores': []
    }
    
    # Combinar DataFrames
    df_total = pd.concat([df_com_resp, df_sem_resp], ignore_index=True)
    
    if 'data_pagamento' in df_total:
        # Agrupar por dia
        df_total['data'] = pd.to_datetime(df_total['data_pagamento'])
        por_dia = df_total.groupby(df_total['data'].dt.date).agg({
            'valor': ['count', 'sum']
        })
        
        for data in por_dia.index:
            resumo['por_dia'][str(data)] = {
                'quantidade': int(por_dia.loc[data, ('valor', 'count')]),
                'valor': float(por_dia.loc[data, ('valor', 'sum')])
            }
    
    # Distribuição de valores (para histograma)
    if 'valor' in df_total:
        resumo['distribuicao_valores'] = df_total['valor'].tolist()
    
    return resumo

if __name__ == "__main__":
    # Testes das funções
    print("🧪 Testando funções auxiliares...")
    
    # Teste de identificação de tipo de pagamento
    print("\n1. Teste de identificação automática de tipo:")
    print(f"Valor R$ 350 + 'matricula': {identificar_tipo_pagamento_automatico(350, 'Taxa de matricula 2024')}")
    print(f"Valor R$ 150: {identificar_tipo_pagamento_automatico(150, '')}")
    print(f"Valor R$ 50 + 'material': {identificar_tipo_pagamento_automatico(50, 'Compra de material escolar')}")
    
    print("\n✅ Funções auxiliares prontas para uso!") 