#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 PROCESSAMENTO AUTOMATIZADO SIMPLIFICADO
========================================

Versão simplificada que foca nas turmas específicas (berçário, infantil i, ii, iii)
e usa as tabelas originais com identificação especial para dados de teste.

Processo em 2 etapas:
1. Gerar mensalidades automaticamente para alunos elegíveis
2. Correlacionar com pagamentos do extrato PIX
"""

from models.base import supabase, gerar_id_mensalidade, gerar_id_pagamento, obter_timestamp
from gestao_mensalidades import _gerar_mensalidades_automatico
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import uuid

# ==========================================================
# 📊 ESTRUTURAS DE DADOS
# ==========================================================

@dataclass
class AlunoElegivel:
    """Dados de um aluno elegível para processamento"""
    id: str
    nome: str
    turma_id: str
    turma_nome: str
    valor_mensalidade: float
    dia_vencimento: int
    data_matricula: Optional[str] = None
    mensalidades_geradas: bool = False
    # Dados calculados
    mensalidades_a_gerar: List[Dict] = field(default_factory=list)
    pagamentos_correlacionados: List[Dict] = field(default_factory=list)
    observacoes: str = ""

@dataclass
class SessaoProcessamentoSimplificada:
    """Sessão de processamento simplificada"""
    id: str
    nome: str
    turmas_selecionadas: List[str]
    modo_teste: bool = True
    etapa_atual: int = 1
    alunos_elegiveis: List[AlunoElegivel] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: obter_timestamp())

# ==========================================================
# 🔍 IDENTIFICAÇÃO DE ALUNOS ELEGÍVEIS
# ==========================================================

def identificar_alunos_elegiveis(turmas_nomes: List[str]) -> List[AlunoElegivel]:
    """
    Identifica alunos elegíveis para processamento automático
    
    Args:
        turmas_nomes: Lista de nomes das turmas (ex: ["berçário", "infantil i"])
        
    Returns:
        List[AlunoElegivel]: Lista de alunos elegíveis
    """
    try:
        print(f"🔍 Identificando alunos elegíveis nas turmas: {', '.join(turmas_nomes)}")
        
        # Buscar turmas baseado nos nomes
        turmas_response = supabase.table("turmas").select("id, nome_turma").execute()
        
        if not turmas_response.data:
            print("❌ Nenhuma turma encontrada")
            return []
        
        # Filtrar turmas que correspondem aos nomes desejados
        turmas_ids = []
        turmas_encontradas = []
        
        for turma in turmas_response.data:
            nome_turma_lower = turma["nome_turma"].lower()
            
            for nome_desejado in turmas_nomes:
                if nome_desejado.lower().replace(" ", "") in nome_turma_lower.replace(" ", ""):
                    turmas_ids.append(turma["id"])
                    turmas_encontradas.append(turma)
                    print(f"  🎓 {turma['nome_turma']} (ID: {turma['id']})")
                    break
        
        if not turmas_ids:
            print("❌ Nenhuma turma correspondente encontrada")
            return []
        
        # Buscar alunos das turmas selecionadas
        alunos_response = supabase.table("alunos").select("""
            id, nome, id_turma, data_matricula, dia_vencimento, valor_mensalidade, 
            mensalidades_geradas, turmas(nome_turma)
        """).in_("id_turma", turmas_ids).execute()
        
        if not alunos_response.data:
            print("❌ Nenhum aluno encontrado nas turmas selecionadas")
            return []
        
        # Filtrar alunos elegíveis
        alunos_elegiveis = []
        
        for aluno in alunos_response.data:
            elegivel = True
            motivos = []
            
            # Critério 1: Não possui mensalidades geradas
            if aluno.get("mensalidades_geradas"):
                elegivel = False
                motivos.append("já tem mensalidades")
            
            # Critério 2: Possui dia_vencimento
            if not aluno.get("dia_vencimento"):
                elegivel = False
                motivos.append("sem dia vencimento")
            
            # Critério 3: Possui valor_mensalidade > 0
            if not aluno.get("valor_mensalidade") or float(aluno.get("valor_mensalidade", 0)) <= 0:
                elegivel = False
                motivos.append("sem valor mensalidade")
            
            # Critério 4: Possui data_matricula (para calcular início das mensalidades)
            if not aluno.get("data_matricula"):
                elegivel = False
                motivos.append("sem data matrícula")
            
            if elegivel:
                aluno_elegivel = AlunoElegivel(
                    id=aluno["id"],
                    nome=aluno["nome"],
                    turma_id=aluno["id_turma"],
                    turma_nome=aluno["turmas"]["nome_turma"],
                    valor_mensalidade=float(aluno["valor_mensalidade"]),
                    dia_vencimento=int(aluno["dia_vencimento"]),
                    data_matricula=aluno["data_matricula"],
                    mensalidades_geradas=aluno.get("mensalidades_geradas", False)
                )
                
                alunos_elegiveis.append(aluno_elegivel)
                print(f"  ✅ {aluno['nome']} - {aluno['turmas']['nome_turma']} (R$ {aluno['valor_mensalidade']:.2f})")
            else:
                print(f"  ❌ {aluno['nome']} - {aluno['turmas']['nome_turma']} ({', '.join(motivos)})")
        
        print(f"\n📊 Total de alunos elegíveis: {len(alunos_elegiveis)}")
        return alunos_elegiveis
        
    except Exception as e:
        print(f"❌ Erro ao identificar alunos elegíveis: {str(e)}")
        return []

# ==========================================================
# 📋 GERAÇÃO AUTOMÁTICA DE MENSALIDADES
# ==========================================================

def gerar_mensalidades_para_aluno(aluno: AlunoElegivel) -> List[Dict]:
    """
    Gera mensalidades automaticamente para um aluno usando a lógica existente
    
    Args:
        aluno: Dados do aluno elegível
        
    Returns:
        List[Dict]: Lista de mensalidades a serem criadas
    """
    try:
        # Usar a função existente de geração automática
        dados_aluno = {
            "data_matricula": aluno.data_matricula,
            "dia_vencimento": aluno.dia_vencimento,
            "valor_mensalidade": aluno.valor_mensalidade
        }
        
        mensalidades = _gerar_mensalidades_automatico(dados_aluno)
        
        # Adicionar dados específicos para o processamento de teste
        for mensalidade in mensalidades:
            mensalidade["id_aluno"] = aluno.id
            mensalidade["status"] = "A vencer"
            mensalidade["observacoes"] = f"GERADO AUTOMATICAMENTE - Processamento de teste"
        
        return mensalidades
        
    except Exception as e:
        print(f"❌ Erro ao gerar mensalidades para {aluno.nome}: {str(e)}")
        return []

def processar_etapa_1_geracao(alunos_elegiveis: List[AlunoElegivel]) -> Dict:
    """
    Etapa 1: Gera mensalidades automaticamente para todos os alunos elegíveis
    
    Args:
        alunos_elegiveis: Lista de alunos elegíveis
        
    Returns:
        Dict: Resultado do processamento
    """
    try:
        print("📋 ETAPA 1: Gerando mensalidades automaticamente...")
        
        total_mensalidades = 0
        alunos_processados = 0
        
        for aluno in alunos_elegiveis:
            print(f"  📝 Processando {aluno.nome}...")
            
            mensalidades = gerar_mensalidades_para_aluno(aluno)
            
            if mensalidades:
                aluno.mensalidades_a_gerar = mensalidades
                total_mensalidades += len(mensalidades)
                alunos_processados += 1
                print(f"    ✅ {len(mensalidades)} mensalidades geradas")
            else:
                aluno.observacoes = "Erro na geração automática"
                print(f"    ❌ Erro na geração")
        
        resultado = {
            "success": True,
            "alunos_processados": alunos_processados,
            "total_mensalidades": total_mensalidades,
            "alunos_com_erro": len(alunos_elegiveis) - alunos_processados
        }
        
        print(f"\n📊 Etapa 1 concluída:")
        print(f"  👥 Alunos processados: {alunos_processados}")
        print(f"  📋 Mensalidades geradas: {total_mensalidades}")
        
        return resultado
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🔗 CORRELAÇÃO COM PAGAMENTOS
# ==========================================================

def buscar_pagamentos_pix_disponiveis() -> List[Dict]:
    """Busca pagamentos PIX disponíveis no extrato"""
    try:
        response = supabase.table("extrato_pix").select("*").eq("status", "novo").order("data_pagamento").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Erro ao buscar pagamentos PIX: {str(e)}")
        return []

def correlacionar_pagamentos_com_mensalidades(alunos_elegiveis: List[AlunoElegivel]) -> Dict:
    """
    Etapa 2: Correlaciona pagamentos PIX com mensalidades geradas
    
    Args:
        alunos_elegiveis: Lista de alunos com mensalidades geradas
        
    Returns:
        Dict: Resultado da correlação
    """
    try:
        print("🔗 ETAPA 2: Correlacionando com pagamentos PIX...")
        
        # Buscar pagamentos disponíveis
        pagamentos_pix = buscar_pagamentos_pix_disponiveis()
        print(f"  💰 {len(pagamentos_pix)} pagamentos PIX disponíveis")
        
        if not pagamentos_pix:
            print("  ⚠️ Nenhum pagamento PIX disponível para correlação")
            return {"success": True, "correlacoes": 0}
        
        # Buscar responsáveis de cada aluno para correlacionar pagamentos
        total_correlacoes = 0
        
        for aluno in alunos_elegiveis:
            if not aluno.mensalidades_a_gerar:
                continue
            
            print(f"  🔍 Correlacionando pagamentos para {aluno.nome}...")
            
            # Buscar responsáveis do aluno
            resp_response = supabase.table("alunos_responsaveis").select("""
                responsaveis(id, nome)
            """).eq("id_aluno", aluno.id).execute()
            
            if not resp_response.data:
                continue
            
            responsaveis_ids = [r["responsaveis"]["id"] for r in resp_response.data]
            responsaveis_nomes = [r["responsaveis"]["nome"] for r in resp_response.data]
            
            # Buscar pagamentos que podem estar relacionados
            pagamentos_correlacionados = []
            
            for pagamento in pagamentos_pix:
                # Correlação por responsável conhecido
                if pagamento.get("id_responsavel") in responsaveis_ids:
                    pagamentos_correlacionados.append(pagamento)
                    continue
                
                # Correlação por similaridade de nome
                nome_remetente = pagamento.get("nome_remetente", "").lower()
                for resp_nome in responsaveis_nomes:
                    if len(resp_nome.split()) >= 2:  # Pelo menos nome e sobrenome
                        primeiro_nome = resp_nome.split()[0].lower()
                        ultimo_nome = resp_nome.split()[-1].lower()
                        
                        if primeiro_nome in nome_remetente and ultimo_nome in nome_remetente:
                            pagamentos_correlacionados.append(pagamento)
                            break
                
                # Correlação por valor próximo à mensalidade
                valor_pix = float(pagamento.get("valor", 0))
                valor_mensalidade = aluno.valor_mensalidade
                margem = 0.05  # 5% de margem
                
                if abs(valor_pix - valor_mensalidade) <= (valor_mensalidade * margem):
                    pagamentos_correlacionados.append(pagamento)
            
            if pagamentos_correlacionados:
                aluno.pagamentos_correlacionados = pagamentos_correlacionados
                total_correlacoes += len(pagamentos_correlacionados)
                print(f"    ✅ {len(pagamentos_correlacionados)} pagamentos correlacionados")
            else:
                print(f"    ⚠️ Nenhum pagamento correlacionado")
        
        print(f"\n📊 Etapa 2 concluída:")
        print(f"  🔗 Total de correlações: {total_correlacoes}")
        
        return {"success": True, "correlacoes": total_correlacoes}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 💾 EXECUÇÃO FINAL (MODO TESTE)
# ==========================================================

def executar_acoes_modo_teste(sessao: SessaoProcessamentoSimplificada) -> Dict:
    """
    Executa as ações finais em modo de teste (apenas adiciona identificação especial)
    
    Args:
        sessao: Sessão de processamento
        
    Returns:
        Dict: Resultado da execução
    """
    try:
        print("💾 EXECUTANDO AÇÕES EM MODO TESTE...")
        
        mensalidades_criadas = 0
        correlacoes_registradas = 0
        
        for aluno in sessao.alunos_elegiveis:
            if not aluno.mensalidades_a_gerar:
                continue
            
            print(f"  📝 Processando {aluno.nome}...")
            
            # Criar mensalidades com identificação de teste
            for mensalidade in aluno.mensalidades_a_gerar:
                id_mensalidade = gerar_id_mensalidade()
                
                dados_mensalidade = {
                    "id_mensalidade": id_mensalidade,
                    "id_aluno": aluno.id,
                    "mes_referencia": mensalidade["mes_referencia"],
                    "valor": float(mensalidade["valor"]),
                    "data_vencimento": mensalidade["data_vencimento"],
                    "status": "A vencer",
                    "observacoes": f"[TESTE] Gerado automaticamente - Sessão: {sessao.id}",
                    "inserted_at": obter_timestamp(),
                    "updated_at": obter_timestamp()
                }
                
                # Em modo teste, inserir nas tabelas originais com identificação especial
                response = supabase.table("mensalidades").insert(dados_mensalidade).execute()
                
                if response.data:
                    mensalidades_criadas += 1
                else:
                    print(f"    ❌ Erro ao criar mensalidade {mensalidade['mes_referencia']}")
            
            # Registrar correlações de pagamentos
            for pagamento in aluno.pagamentos_correlacionados:
                # Criar registro de correlação identificada
                dados_correlacao = {
                    "id_pagamento": gerar_id_pagamento(),
                    "id_responsavel": pagamento.get("id_responsavel", "IDENTIFICADO_AUTO"),
                    "id_aluno": aluno.id,
                    "data_pagamento": pagamento["data_pagamento"],
                    "valor": float(pagamento["valor"]),
                    "tipo_pagamento": "mensalidade",
                    "forma_pagamento": "PIX",
                    "descricao": f"[TESTE] Correlação automática - PIX: {pagamento['nome_remetente']}",
                    "origem_extrato": True,
                    "id_extrato": pagamento["id"],
                    "inserted_at": obter_timestamp(),
                    "updated_at": obter_timestamp()
                }
                
                response = supabase.table("pagamentos").insert(dados_correlacao).execute()
                
                if response.data:
                    correlacoes_registradas += 1
        
        print(f"\n✅ Execução concluída:")
        print(f"  📋 Mensalidades criadas: {mensalidades_criadas}")
        print(f"  🔗 Correlações registradas: {correlacoes_registradas}")
        
        return {
            "success": True,
            "mensalidades_criadas": mensalidades_criadas,
            "correlacoes_registradas": correlacoes_registradas
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==========================================================
# 🚀 FUNÇÃO PRINCIPAL DE PROCESSAMENTO
# ==========================================================

def iniciar_processamento_simplificado(
    turmas_nomes: List[str],
    nome_sessao: str,
    modo_teste: bool = True
) -> SessaoProcessamentoSimplificada:
    """
    Inicia uma nova sessão de processamento automatizado simplificado
    
    Args:
        turmas_nomes: Lista de nomes das turmas (ex: ["berçário", "infantil i"])
        nome_sessao: Nome para identificar a sessão
        modo_teste: Se True, adiciona identificação especial aos dados
        
    Returns:
        SessaoProcessamentoSimplificada: Sessão criada
    """
    try:
        print("🚀 INICIANDO PROCESSAMENTO AUTOMATIZADO SIMPLIFICADO")
        print("=" * 60)
        
        # Criar sessão
        sessao = SessaoProcessamentoSimplificada(
            id=str(uuid.uuid4()),
            nome=nome_sessao,
            turmas_selecionadas=turmas_nomes,
            modo_teste=modo_teste
        )
        
        print(f"📝 Sessão: {sessao.nome}")
        print(f"🧪 Modo teste: {'Ativo' if modo_teste else 'PRODUÇÃO'}")
        print(f"🎓 Turmas: {', '.join(turmas_nomes)}")
        print("")
        
        # Etapa 1: Identificar alunos elegíveis
        alunos_elegiveis = identificar_alunos_elegiveis(turmas_nomes)
        sessao.alunos_elegiveis = alunos_elegiveis
        
        if not alunos_elegiveis:
            print("❌ Nenhum aluno elegível encontrado")
            return sessao
        
        # Etapa 2: Gerar mensalidades automaticamente
        resultado_etapa1 = processar_etapa_1_geracao(alunos_elegiveis)
        
        if not resultado_etapa1.get("success"):
            print(f"❌ Erro na etapa 1: {resultado_etapa1.get('error')}")
            return sessao
        
        # Etapa 3: Correlacionar com pagamentos
        resultado_etapa2 = correlacionar_pagamentos_com_mensalidades(alunos_elegiveis)
        
        if not resultado_etapa2.get("success"):
            print(f"❌ Erro na etapa 2: {resultado_etapa2.get('error')}")
            return sessao
        
        sessao.etapa_atual = 2  # Pronto para execução
        
        print("\n" + "=" * 60)
        print("✅ PROCESSAMENTO PREPARADO COM SUCESSO!")
        print("")
        print("📊 Resumo:")
        print(f"  👥 Alunos processados: {resultado_etapa1['alunos_processados']}")
        print(f"  📋 Mensalidades a criar: {resultado_etapa1['total_mensalidades']}")
        print(f"  🔗 Correlações identificadas: {resultado_etapa2['correlacoes']}")
        print("")
        print("🎯 Próximo passo: Revisar dados e executar ações")
        
        return sessao
        
    except Exception as e:
        print(f"❌ Erro no processamento: {str(e)}")
        return SessaoProcessamentoSimplificada(
            id="ERRO",
            nome=nome_sessao,
            turmas_selecionadas=turmas_nomes,
            modo_teste=modo_teste
        )

# ==========================================================
# 🧪 FUNÇÃO DE TESTE
# ==========================================================

def testar_processamento():
    """Função para testar o processamento com dados reais"""
    print("🧪 TESTANDO PROCESSAMENTO AUTOMATIZADO SIMPLIFICADO")
    print("=" * 60)
    
    # Testar com turmas específicas
    turmas_teste = ["berçário", "infantil i", "infantil ii", "infantil iii"]
    
    sessao = iniciar_processamento_simplificado(
        turmas_nomes=turmas_teste,
        nome_sessao=f"Teste - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        modo_teste=True
    )
    
    if sessao.id != "ERRO" and sessao.alunos_elegiveis:
        print("\n🎯 EXECUTAR AÇÕES? (Digite 'sim' para confirmar)")
        resposta = input("Resposta: ").strip().lower()
        
        if resposta == "sim":
            resultado = executar_acoes_modo_teste(sessao)
            
            if resultado.get("success"):
                print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            else:
                print(f"\n❌ Erro na execução: {resultado.get('error')}")
        else:
            print("\n🔄 Execução cancelada pelo usuário")
    
    return sessao

if __name__ == "__main__":
    testar_processamento() 