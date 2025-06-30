#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 SCRIPT DE CORREÇÃO: ID_EXTRATO EM PAGAMENTOS
==============================================

Script para corrigir a coluna id_extrato vazia na tabela pagamentos,
buscando correspondências precisas com registros da tabela extrato_pix.

Critérios de correspondência:
1. id_responsavel (mesmo responsável)
2. valor (mesmo valor, tolerância de centavos)
3. data_pagamento (mesma data)
4. origem_extrato = True (pagamento originado do extrato)

Autor: Sistema de Gestão Escolar
Data: 2024
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from supabase import create_client
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# Configurações do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ ERRO: Variáveis SUPABASE_URL e SUPABASE_KEY devem estar configuradas no .env")
    sys.exit(1)

supabase = create_client(url, key)

def log_info(mensagem: str):
    """Log com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ℹ️  {mensagem}")

def log_success(mensagem: str):
    """Log de sucesso"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ✅ {mensagem}")

def log_warning(mensagem: str):
    """Log de aviso"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ⚠️  {mensagem}")

def log_error(mensagem: str):
    """Log de erro"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ❌ {mensagem}")

def buscar_pagamentos_sem_id_extrato() -> List[Dict]:
    """
    Busca pagamentos que têm origem_extrato=True mas id_extrato está vazio
    
    Returns:
        Lista de pagamentos sem id_extrato
    """
    try:
        log_info("Buscando pagamentos com origem_extrato=True e id_extrato vazio...")
        
        # Buscar pagamentos sem id_extrato ou com id_extrato null
        response = supabase.table("pagamentos").select("""
            id_pagamento, id_responsavel, id_aluno, valor, data_pagamento, 
            tipo_pagamento, descricao, origem_extrato, id_extrato,
            inserted_at, updated_at
        """).eq("origem_extrato", True).execute()
        
        if not response.data:
            log_warning("Nenhum pagamento com origem_extrato=True encontrado")
            return []
        
        # Filtrar apenas os que têm id_extrato vazio/null
        pagamentos_sem_id = []
        for pagamento in response.data:
            id_extrato = pagamento.get("id_extrato")
            if not id_extrato or id_extrato == "" or id_extrato is None:
                pagamentos_sem_id.append(pagamento)
        
        log_info(f"Encontrados {len(pagamentos_sem_id)} pagamentos sem id_extrato (de {len(response.data)} com origem_extrato=True)")
        
        return pagamentos_sem_id
        
    except Exception as e:
        log_error(f"Erro ao buscar pagamentos: {str(e)}")
        return []

def buscar_registros_extrato_pix() -> List[Dict]:
    """
    Busca todos os registros da tabela extrato_pix para correspondência
    
    Returns:
        Lista de registros do extrato PIX
    """
    try:
        log_info("Carregando registros da tabela extrato_pix...")
        
        response = supabase.table("extrato_pix").select("""
            id, nome_remetente, valor, data_pagamento, id_responsavel,
            status, tipo_pagamento, observacoes, inserted_at
        """).execute()
        
        if not response.data:
            log_warning("Nenhum registro encontrado na tabela extrato_pix")
            return []
        
        log_info(f"Carregados {len(response.data)} registros do extrato PIX")
        
        return response.data
        
    except Exception as e:
        log_error(f"Erro ao buscar registros do extrato: {str(e)}")
        return []

def valores_sao_iguais(valor1: float, valor2: float, tolerancia: float = 0.01) -> bool:
    """
    Verifica se dois valores são iguais considerando uma tolerância
    
    Args:
        valor1: Primeiro valor
        valor2: Segundo valor
        tolerancia: Tolerância permitida (padrão: 1 centavo)
    
    Returns:
        True se os valores são considerados iguais
    """
    return abs(float(valor1) - float(valor2)) <= tolerancia

def buscar_correspondencia_no_extrato(pagamento: Dict, registros_extrato: List[Dict]) -> Optional[Dict]:
    """
    Busca correspondência de um pagamento nos registros do extrato PIX
    
    Args:
        pagamento: Dados do pagamento
        registros_extrato: Lista de registros do extrato PIX
    
    Returns:
        Registro do extrato correspondente ou None se não encontrado
    """
    
    id_responsavel_pag = pagamento.get("id_responsavel")
    valor_pag = float(pagamento.get("valor", 0))
    data_pag = pagamento.get("data_pagamento")
    
    log_info(f"  🔍 Buscando correspondência para pagamento {pagamento.get('id_pagamento')}")
    log_info(f"     - Responsável: {id_responsavel_pag}")
    log_info(f"     - Valor: R$ {valor_pag:.2f}")
    log_info(f"     - Data: {data_pag}")
    
    # Lista para armazenar possíveis correspondências
    candidatos = []
    
    for extrato in registros_extrato:
        id_responsavel_ext = extrato.get("id_responsavel")
        valor_ext = float(extrato.get("valor", 0))
        data_ext = extrato.get("data_pagamento")
        
        # Critério 1: Mesmo responsável
        if id_responsavel_pag != id_responsavel_ext:
            continue
        
        # Critério 2: Mesma data
        if data_pag != data_ext:
            continue
        
        # Critério 3: Mesmo valor (com tolerância)
        if not valores_sao_iguais(valor_pag, valor_ext):
            continue
        
        # Se chegou até aqui, é um candidato forte
        candidatos.append({
            "extrato": extrato,
            "score": 100,  # Score base para correspondência perfeita
            "motivo": "Responsável, data e valor coincidem"
        })
    
    if not candidatos:
        log_info(f"     ❌ Nenhuma correspondência encontrada")
        return None
    
    if len(candidatos) == 1:
        candidato = candidatos[0]
        log_info(f"     ✅ Correspondência única encontrada:")
        log_info(f"        - ID Extrato: {candidato['extrato']['id']}")
        log_info(f"        - Nome Remetente: {candidato['extrato'].get('nome_remetente')}")
        log_info(f"        - Status: {candidato['extrato'].get('status')}")
        log_info(f"        - Motivo: {candidato['motivo']}")
        return candidato["extrato"]
    
    # Múltiplos candidatos - preferir registrado
    log_warning(f"     ⚠️  {len(candidatos)} correspondências encontradas - analisando...")
    
    # Preferir registros com status 'registrado'
    candidatos_registrados = [c for c in candidatos if c["extrato"].get("status") == "registrado"]
    
    if len(candidatos_registrados) == 1:
        candidato = candidatos_registrados[0]
        log_info(f"     ✅ Selecionado registro com status 'registrado':")
        log_info(f"        - ID Extrato: {candidato['extrato']['id']}")
        return candidato["extrato"]
    
    # Se ainda há empate, pegar o primeiro
    candidato = candidatos[0]
    log_warning(f"     ⚠️  Múltiplas correspondências - selecionando a primeira:")
    log_info(f"        - ID Extrato: {candidato['extrato']['id']}")
    
    return candidato["extrato"]

def atualizar_id_extrato_pagamento(id_pagamento: str, id_extrato: str) -> bool:
    """
    Atualiza o id_extrato de um pagamento
    
    Args:
        id_pagamento: ID do pagamento a ser atualizado
        id_extrato: ID do extrato a ser vinculado
    
    Returns:
        True se a atualização foi bem-sucedida
    """
    try:
        response = supabase.table("pagamentos").update({
            "id_extrato": id_extrato,
            "updated_at": datetime.now().isoformat()
        }).eq("id_pagamento", id_pagamento).execute()
        
        return bool(response.data)
        
    except Exception as e:
        log_error(f"Erro ao atualizar pagamento {id_pagamento}: {str(e)}")
        return False

def executar_correcao(modo_teste: bool = True) -> Dict:
    """
    Executa a correção dos IDs do extrato nos pagamentos
    
    Args:
        modo_teste: Se True, apenas simula as correções sem fazer alterações
    
    Returns:
        Relatório da execução
    """
    
    log_info("🚀 INICIANDO CORREÇÃO DE ID_EXTRATO EM PAGAMENTOS")
    log_info(f"   Modo: {'TESTE (sem alterações)' if modo_teste else 'PRODUÇÃO (com alterações)'}")
    print("=" * 80)
    
    # 1. Buscar pagamentos sem id_extrato
    pagamentos = buscar_pagamentos_sem_id_extrato()
    
    if not pagamentos:
        log_success("Nenhum pagamento precisa de correção!")
        return {
            "total_pagamentos": 0,
            "correspondencias_encontradas": 0,
            "atualizacoes_realizadas": 0,
            "falhas": 0
        }
    
    # 2. Buscar registros do extrato PIX
    registros_extrato = buscar_registros_extrato_pix()
    
    if not registros_extrato:
        log_error("Não há registros no extrato PIX para fazer correspondências!")
        return {
            "total_pagamentos": len(pagamentos),
            "correspondencias_encontradas": 0,
            "atualizacoes_realizadas": 0,
            "falhas": len(pagamentos)
        }
    
    # 3. Processar cada pagamento
    print("=" * 80)
    log_info("PROCESSANDO CORRESPONDÊNCIAS...")
    print("=" * 80)
    
    estatisticas = {
        "total_pagamentos": len(pagamentos),
        "correspondencias_encontradas": 0,
        "atualizacoes_realizadas": 0,
        "falhas": 0,
        "detalhes": []
    }
    
    for i, pagamento in enumerate(pagamentos, 1):
        id_pagamento = pagamento.get("id_pagamento")
        log_info(f"📄 Processando {i}/{len(pagamentos)}: {id_pagamento}")
        
        # Buscar correspondência
        extrato_correspondente = buscar_correspondencia_no_extrato(pagamento, registros_extrato)
        
        if extrato_correspondente:
            estatisticas["correspondencias_encontradas"] += 1
            id_extrato = extrato_correspondente["id"]
            
            # Registrar detalhes
            detalhe = {
                "id_pagamento": id_pagamento,
                "id_extrato": id_extrato,
                "valor": pagamento.get("valor"),
                "data": pagamento.get("data_pagamento"),
                "responsavel": pagamento.get("id_responsavel"),
                "nome_remetente": extrato_correspondente.get("nome_remetente"),
                "status_extrato": extrato_correspondente.get("status")
            }
            
            if not modo_teste:
                # Fazer a atualização
                sucesso = atualizar_id_extrato_pagamento(id_pagamento, id_extrato)
                
                if sucesso:
                    estatisticas["atualizacoes_realizadas"] += 1
                    detalhe["atualizado"] = True
                    log_success(f"     ✅ Pagamento {id_pagamento} atualizado com id_extrato={id_extrato}")
                else:
                    estatisticas["falhas"] += 1
                    detalhe["atualizado"] = False
                    log_error(f"     ❌ Falha ao atualizar pagamento {id_pagamento}")
            else:
                detalhe["atualizado"] = "SIMULADO"
                log_info(f"     🧪 SIMULAÇÃO: {id_pagamento} seria atualizado com id_extrato={id_extrato}")
            
            estatisticas["detalhes"].append(detalhe)
        else:
            estatisticas["falhas"] += 1
            log_warning(f"     ❌ Correspondência não encontrada para {id_pagamento}")
        
        print("-" * 80)
    
    # 4. Relatório final
    print("=" * 80)
    log_info("📊 RELATÓRIO FINAL")
    print("=" * 80)
    
    log_info(f"Total de pagamentos processados: {estatisticas['total_pagamentos']}")
    log_info(f"Correspondências encontradas: {estatisticas['correspondencias_encontradas']}")
    
    if not modo_teste:
        log_info(f"Atualizações realizadas: {estatisticas['atualizacoes_realizadas']}")
        log_info(f"Falhas: {estatisticas['falhas']}")
        
        if estatisticas['atualizacoes_realizadas'] > 0:
            log_success(f"✅ {estatisticas['atualizacoes_realizadas']} pagamentos corrigidos com sucesso!")
    else:
        log_info(f"Atualizações que seriam feitas: {estatisticas['correspondencias_encontradas']}")
        log_info("🧪 MODO TESTE - Nenhuma alteração foi feita no banco")
    
    if estatisticas['falhas'] > 0:
        log_warning(f"⚠️  {estatisticas['falhas']} pagamentos não puderam ser corrigidos")
    
    return estatisticas

def main():
    """Função principal"""
    
    print("🔧 SCRIPT DE CORREÇÃO: ID_EXTRATO EM PAGAMENTOS")
    print("=" * 80)
    
    # Perguntar ao usuário sobre o modo
    while True:
        resposta = input("Executar em modo TESTE (sem alterações) ou PRODUÇÃO? [T/P]: ").strip().upper()
        if resposta in ['T', 'TESTE']:
            modo_teste = True
            break
        elif resposta in ['P', 'PRODUÇÃO', 'PRODUCAO']:
            modo_teste = False
            print("⚠️  ATENÇÃO: Executando em modo PRODUÇÃO - alterações serão feitas no banco!")
            confirmacao = input("Tem certeza? [S/N]: ").strip().upper()
            if confirmacao in ['S', 'SIM']:
                break
            else:
                print("Operação cancelada.")
                return
        else:
            print("Por favor, digite T para Teste ou P para Produção")
    
    print("=" * 80)
    
    # Executar correção
    resultado = executar_correcao(modo_teste=modo_teste)
    
    # Salvar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"relatorio_correcao_id_extrato_{timestamp}.txt"
    
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            f.write(f"RELATÓRIO DE CORREÇÃO ID_EXTRATO - {datetime.now()}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Modo: {'TESTE' if modo_teste else 'PRODUÇÃO'}\n")
            f.write(f"Total processados: {resultado['total_pagamentos']}\n")
            f.write(f"Correspondências: {resultado['correspondencias_encontradas']}\n")
            
            if not modo_teste:
                f.write(f"Atualizados: {resultado['atualizacoes_realizadas']}\n")
            
            f.write(f"Falhas: {resultado['falhas']}\n")
            f.write("\nDETALHES:\n")
            f.write("-" * 80 + "\n")
            
            for detalhe in resultado.get('detalhes', []):
                f.write(f"Pagamento: {detalhe['id_pagamento']}\n")
                f.write(f"Extrato: {detalhe['id_extrato']}\n")
                f.write(f"Valor: R$ {detalhe['valor']}\n")
                f.write(f"Data: {detalhe['data']}\n")
                f.write(f"Nome: {detalhe['nome_remetente']}\n")
                f.write(f"Status: {detalhe['atualizado']}\n")
                f.write("-" * 40 + "\n")
        
        log_success(f"Relatório salvo em: {nome_arquivo}")
        
    except Exception as e:
        log_error(f"Erro ao salvar relatório: {str(e)}")
    
    print("=" * 80)
    log_success("Script finalizado!")

if __name__ == "__main__":
    main() 