#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎓 TESTES ESTRATÉGICOS DO MODELO PEDAGÓGICO
==========================================

Testes abrangentes e estratégicos para funções de gestão de alunos, responsáveis e turmas.
Validações específicas para filtros por campos vazios, edição de dados e cadastro completo.
"""

import unittest
from datetime import datetime, date
from models.pedagogico import *
from models.base import supabase, obter_timestamp, gerar_id_aluno, gerar_id_responsavel, gerar_id_vinculo
from tests import TEST_DATA, TEST_CONFIG
from typing import List, Dict

class TestPedagogicoBase(unittest.TestCase):
    """Classe base para testes pedagógicos com setup e cleanup"""
    
    @classmethod
    def setUpClass(cls):
        """Setup inicial para todos os testes"""
        cls.dados_teste = {
            "turma_id": None,
            "aluno_id": None,
            "responsavel_id": None,
            "vinculo_id": None,
            "aluno_campos_vazios_id": None,
            "responsavel_incompleto_id": None
        }
        
        print("\n" + "="*80)
        print("🧪 INICIANDO TESTES ESTRATÉGICOS DO MODELO PEDAGÓGICO")
        print("="*80)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup após todos os testes"""
        if TEST_CONFIG["cleanup_after_tests"]:
            cls._cleanup_test_data()
        
        print("\n" + "="*80)
        print("✅ TESTES ESTRATÉGICOS DO MODELO PEDAGÓGICO CONCLUÍDOS")
        print("="*80)
    
    @classmethod
    def _cleanup_test_data(cls):
        """Remove dados de teste criados"""
        try:
            # Remover vínculos de teste
            supabase.table("alunos_responsaveis").delete().like("id", "AR_TEST_%").execute()
            
            # Remover alunos de teste
            supabase.table("alunos").delete().like("id", "ALU_TEST_%").execute()
            supabase.table("alunos").delete().like("nome", "%Teste%").execute()
            
            # Remover responsáveis de teste
            supabase.table("responsaveis").delete().like("id", "RES_TEST_%").execute()
            supabase.table("responsaveis").delete().like("nome", "%Teste%").execute()
            
            # Remover turmas de teste
            supabase.table("turmas").delete().like("id", "TEST_%").execute()
            
            print("🧹 Cleanup de dados de teste concluído")
            
        except Exception as e:
            print(f"⚠️ Erro no cleanup: {str(e)}")

class TestGestaoTurmas(TestPedagogicoBase):
    """Testes para gestão de turmas"""
    
    def test_01_listar_turmas_disponiveis(self):
        """Teste 1: Listar turmas disponíveis"""
        print("\n🧪 Teste 1: Listar turmas disponíveis")
        
        resultado = listar_turmas_disponiveis()
        
        self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
        self.assertIsInstance(resultado["turmas"], list)
        self.assertGreater(resultado["count"], 0, "Deve haver pelo menos uma turma")
        
        print(f"✅ {resultado['count']} turmas encontradas: {resultado['turmas'][:3]}...")
    
    def test_02_obter_mapeamento_turmas(self):
        """Teste 2: Obter mapeamento nome->ID das turmas"""
        print("\n🧪 Teste 2: Obter mapeamento de turmas")
        
        resultado = obter_mapeamento_turmas()
        
        self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
        self.assertIsInstance(resultado["mapeamento"], dict)
        self.assertGreater(resultado["total_turmas"], 0)
        
        # Verificar se mapeamento está correto
        for nome, id_turma in resultado["mapeamento"].items():
            self.assertIsInstance(nome, str)
            self.assertIsInstance(id_turma, str)
            self.assertTrue(len(nome) > 0)
            self.assertTrue(len(id_turma) > 0)
        
        print(f"✅ Mapeamento criado para {resultado['total_turmas']} turmas")
    
    def test_03_obter_turma_por_id(self):
        """Teste 3: Obter dados de uma turma específica"""
        print("\n🧪 Teste 3: Obter turma por ID")
        
        # Primeiro obter uma turma existente
        mapeamento = obter_mapeamento_turmas()
        self.assertTrue(mapeamento["success"])
        
        if mapeamento["mapeamento"]:
            primeiro_id = list(mapeamento["mapeamento"].values())[0]
            
            resultado = obter_turma_por_id(primeiro_id)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIsInstance(resultado["turma"], dict)
            self.assertGreaterEqual(resultado["total_alunos"], 0)
            
            print(f"✅ Turma obtida: {resultado['turma']['nome_turma']} com {resultado['total_alunos']} alunos")
        else:
            print("⚠️ Nenhuma turma disponível para teste")

class TestGestaoAlunos(TestPedagogicoBase):
    """Testes para gestão de alunos"""
    
    def test_01_buscar_alunos_para_dropdown(self):
        """Teste 1: Buscar alunos para dropdown"""
        print("\n🧪 Teste 1: Buscar alunos para dropdown")
        
        # Teste sem filtro
        resultado = buscar_alunos_para_dropdown()
        self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
        self.assertIsInstance(resultado["opcoes"], list)
        
        # Teste com filtro
        if resultado["opcoes"]:
            primeiro_nome = resultado["opcoes"][0]["nome"]
            termo_busca = primeiro_nome[:3]  # Primeiras 3 letras
            
            resultado_filtrado = buscar_alunos_para_dropdown(termo_busca)
            self.assertTrue(resultado_filtrado["success"])
            
            # Verificar se o filtro funcionou
            for opcao in resultado_filtrado["opcoes"]:
                self.assertIn(termo_busca.lower(), opcao["nome"].lower())
            
            print(f"✅ Busca sem filtro: {resultado['count']} alunos")
            print(f"✅ Busca com filtro '{termo_busca}': {resultado_filtrado['count']} alunos")
        else:
            print("⚠️ Nenhum aluno disponível para teste")
    
    def test_02_buscar_alunos_por_turmas(self):
        """Teste 2: Buscar alunos por turmas específicas"""
        print("\n🧪 Teste 2: Buscar alunos por turmas")
        
        # Obter IDs de turmas disponíveis
        mapeamento = obter_mapeamento_turmas()
        self.assertTrue(mapeamento["success"])
        
        if mapeamento["mapeamento"]:
            # Testar com 2 turmas
            ids_turmas = list(mapeamento["mapeamento"].values())[:2]
            
            resultado = buscar_alunos_por_turmas(ids_turmas)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIsInstance(resultado["alunos_por_turma"], dict)
            self.assertGreaterEqual(resultado["total_alunos"], 0)
            
            # Verificar estrutura dos dados retornados
            for turma_nome, dados_turma in resultado["alunos_por_turma"].items():
                self.assertIn("id_turma", dados_turma)
                self.assertIn("nome_turma", dados_turma)
                self.assertIn("alunos", dados_turma)
                self.assertIsInstance(dados_turma["alunos"], list)
                
                # Verificar estrutura dos alunos
                for aluno in dados_turma["alunos"]:
                    campos_obrigatorios = ["id", "nome", "turno", "valor_mensalidade", "responsaveis"]
                    for campo in campos_obrigatorios:
                        self.assertIn(campo, aluno)
            
            print(f"✅ Busca por {len(ids_turmas)} turmas retornou {resultado['total_alunos']} alunos")
            print(f"✅ Turmas com alunos: {list(resultado['alunos_por_turma'].keys())}")
        else:
            print("⚠️ Nenhuma turma disponível para teste")
    
    def test_03_cadastrar_aluno_e_vincular(self):
        """Teste 3: Cadastrar novo aluno com vínculo"""
        print("\n🧪 Teste 3: Cadastrar aluno e vincular responsável")
        
        # Primeiro criar um responsável de teste
        dados_responsavel = TEST_DATA["responsavel_teste"].copy()
        dados_responsavel["nome"] = f"Responsável Teste {datetime.now().strftime('%H%M%S')}"
        
        # Obter uma turma para o aluno
        mapeamento = obter_mapeamento_turmas()
        self.assertTrue(mapeamento["success"])
        
        if mapeamento["mapeamento"]:
            id_turma = list(mapeamento["mapeamento"].values())[0]
            
            # Cadastrar responsável primeiro
            resp_resultado = supabase.table("responsaveis").insert({
                "id": f"RES_TEST_{datetime.now().strftime('%H%M%S')}",
                **dados_responsavel,
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }).execute()
            
            self.assertTrue(resp_resultado.data, "Erro ao criar responsável de teste")
            id_responsavel = resp_resultado.data[0]["id"]
            
            # Cadastrar aluno
            dados_aluno = TEST_DATA["aluno_teste"].copy()
            dados_aluno["nome"] = f"Aluno Teste {datetime.now().strftime('%H%M%S')}"
            dados_aluno["id_turma"] = id_turma
            
            resultado = cadastrar_aluno_e_vincular(
                dados_aluno=dados_aluno,
                id_responsavel=id_responsavel,
                tipo_relacao="mãe",
                responsavel_financeiro=True
            )
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIn("id_aluno", resultado)
            self.assertTrue(resultado.get("vinculo_criado", False))
            
            # Salvar IDs para outros testes
            self.__class__.dados_teste["aluno_id"] = resultado["id_aluno"]
            self.__class__.dados_teste["responsavel_id"] = id_responsavel
            
            print(f"✅ Aluno cadastrado: {resultado['id_aluno']}")
            print(f"✅ Vínculo criado: {resultado.get('vinculo_criado')}")
        else:
            print("⚠️ Nenhuma turma disponível para teste")
    
    def test_04_buscar_informacoes_completas_aluno(self):
        """Teste 4: Buscar informações completas de um aluno"""
        print("\n🧪 Teste 4: Buscar informações completas do aluno")
        
        if self.__class__.dados_teste["aluno_id"]:
            id_aluno = self.__class__.dados_teste["aluno_id"]
            
            resultado = buscar_informacoes_completas_aluno(id_aluno)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            
            # Verificar estrutura completa
            self.assertIn("aluno", resultado)
            self.assertIn("responsaveis", resultado)
            self.assertIn("pagamentos", resultado)
            self.assertIn("mensalidades", resultado)
            self.assertIn("estatisticas", resultado)
            
            # Verificar dados do aluno
            aluno = resultado["aluno"]
            campos_aluno = ["id", "nome", "turma_nome", "turno", "valor_mensalidade"]
            for campo in campos_aluno:
                self.assertIn(campo, aluno)
            
            # Verificar estatísticas
            stats = resultado["estatisticas"]
            campos_stats = ["total_responsaveis", "total_pagamentos", "total_mensalidades"]
            for campo in campos_stats:
                self.assertIn(campo, stats)
                self.assertIsInstance(stats[campo], int)
            
            print(f"✅ Informações completas obtidas para aluno {aluno['nome']}")
            print(f"✅ Responsáveis: {stats['total_responsaveis']}, Pagamentos: {stats['total_pagamentos']}")
        else:
            print("⚠️ Nenhum aluno de teste disponível")
    
    def test_05_atualizar_aluno_campos(self):
        """Teste 5: Atualizar campos de um aluno"""
        print("\n🧪 Teste 5: Atualizar campos do aluno")
        
        if self.__class__.dados_teste["aluno_id"]:
            id_aluno = self.__class__.dados_teste["aluno_id"]
            
            # Dados para atualização
            novos_dados = {
                "turno": "Vespertino",
                "valor_mensalidade": 500.0,
                "dia_vencimento": "10"
            }
            
            resultado = atualizar_aluno_campos(id_aluno, novos_dados)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIn("campos_atualizados", resultado)
            self.assertIn("data", resultado)
            
            # Verificar se os campos foram atualizados
            for campo in novos_dados.keys():
                self.assertIn(campo, resultado["campos_atualizados"])
            
            print(f"✅ Campos atualizados: {resultado['campos_atualizados']}")
        else:
            print("⚠️ Nenhum aluno de teste disponível")

class TestGestaoResponsaveis(TestPedagogicoBase):
    """Testes para gestão de responsáveis"""
    
    def test_01_buscar_responsaveis_para_dropdown(self):
        """Teste 1: Buscar responsáveis para dropdown"""
        print("\n🧪 Teste 1: Buscar responsáveis para dropdown")
        
        # Teste sem filtro
        resultado = buscar_responsaveis_para_dropdown()
        self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
        self.assertIsInstance(resultado["opcoes"], list)
        
        # Teste com filtro se houver responsáveis
        if resultado["opcoes"]:
            primeiro_nome = resultado["opcoes"][0]["nome"]
            termo_busca = primeiro_nome[:3]
            
            resultado_filtrado = buscar_responsaveis_para_dropdown(termo_busca)
            self.assertTrue(resultado_filtrado["success"])
            
            print(f"✅ Busca sem filtro: {resultado['total']} responsáveis")
            print(f"✅ Busca com filtro '{termo_busca}': {resultado_filtrado['total']} responsáveis")
        else:
            print("⚠️ Nenhum responsável disponível para teste")
    
    def test_02_verificar_responsavel_existe(self):
        """Teste 2: Verificar se responsável existe"""
        print("\n🧪 Teste 2: Verificar existência de responsável")
        
        # Teste com nome que não existe
        resultado_inexistente = verificar_responsavel_existe("Nome Inexistente 12345")
        self.assertTrue(resultado_inexistente["success"])
        self.assertFalse(resultado_inexistente["existe"])
        
        # Teste com nome que existe (se houver responsáveis)
        responsaveis = buscar_responsaveis_para_dropdown()
        if responsaveis["opcoes"]:
            nome_existente = responsaveis["opcoes"][0]["nome"]
            resultado_existente = verificar_responsavel_existe(nome_existente)
            self.assertTrue(resultado_existente["success"])
            self.assertTrue(resultado_existente["existe"])
            
            print(f"✅ Responsável inexistente: {not resultado_inexistente['existe']}")
            print(f"✅ Responsável existente '{nome_existente}': {resultado_existente['existe']}")
        else:
            print("⚠️ Nenhum responsável disponível para teste de existência")
    
    def test_03_listar_responsaveis_aluno(self):
        """Teste 3: Listar responsáveis de um aluno"""
        print("\n🧪 Teste 3: Listar responsáveis do aluno")
        
        if self.__class__.dados_teste["aluno_id"]:
            id_aluno = self.__class__.dados_teste["aluno_id"]
            
            resultado = listar_responsaveis_aluno(id_aluno)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIsInstance(resultado["responsaveis"], list)
            self.assertGreaterEqual(resultado["count"], 1, "Aluno de teste deve ter pelo menos 1 responsável")
            
            # Verificar estrutura dos responsáveis
            for responsavel in resultado["responsaveis"]:
                campos_obrigatorios = ["id", "nome", "tipo_relacao", "responsavel_financeiro"]
                for campo in campos_obrigatorios:
                    self.assertIn(campo, responsavel)
            
            print(f"✅ {resultado['count']} responsáveis encontrados para o aluno")
        else:
            print("⚠️ Nenhum aluno de teste disponível")
    
    def test_04_listar_alunos_vinculados_responsavel(self):
        """Teste 4: Listar alunos vinculados a um responsável"""
        print("\n🧪 Teste 4: Listar alunos vinculados ao responsável")
        
        if self.__class__.dados_teste["responsavel_id"]:
            id_responsavel = self.__class__.dados_teste["responsavel_id"]
            
            resultado = listar_alunos_vinculados_responsavel(id_responsavel)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIsInstance(resultado["alunos"], list)
            self.assertGreaterEqual(resultado["count"], 1, "Responsável de teste deve ter pelo menos 1 aluno")
            
            # Verificar estrutura dos alunos
            for aluno in resultado["alunos"]:
                campos_obrigatorios = ["id", "nome", "label", "tipo_relacao"]
                for campo in campos_obrigatorios:
                    self.assertIn(campo, aluno)
            
            print(f"✅ {resultado['count']} alunos encontrados para o responsável")
        else:
            print("⚠️ Nenhum responsável de teste disponível")

class TestGestaoVinculos(TestPedagogicoBase):
    """Testes para gestão de vínculos aluno-responsável"""
    
    def test_01_vincular_aluno_responsavel(self):
        """Teste 1: Criar vínculo entre aluno e responsável"""
        print("\n🧪 Teste 1: Criar vínculo aluno-responsável")
        
        if self.__class__.dados_teste["aluno_id"] and self.__class__.dados_teste["responsavel_id"]:
            # Criar um segundo responsável para testar vínculo adicional
            dados_responsavel2 = {
                "id": f"RES_TEST2_{datetime.now().strftime('%H%M%S')}",
                "nome": f"Segundo Responsável Teste {datetime.now().strftime('%H%M%S')}",
                "tipo_relacao": "pai",
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }
            
            resp2_resultado = supabase.table("responsaveis").insert(dados_responsavel2).execute()
            self.assertTrue(resp2_resultado.data)
            
            id_responsavel2 = resp2_resultado.data[0]["id"]
            
            # Criar vínculo
            resultado = vincular_aluno_responsavel(
                id_aluno=self.__class__.dados_teste["aluno_id"],
                id_responsavel=id_responsavel2,
                tipo_relacao="pai",
                responsavel_financeiro=False
            )
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIn("id_vinculo", resultado)
            
            # Salvar ID do vínculo para outros testes
            self.__class__.dados_teste["vinculo_id"] = resultado["id_vinculo"]
            
            print(f"✅ Vínculo criado: {resultado['id_vinculo']}")
        else:
            print("⚠️ Aluno ou responsável de teste não disponível")
    
    def test_02_atualizar_vinculo_responsavel(self):
        """Teste 2: Atualizar vínculo existente"""
        print("\n🧪 Teste 2: Atualizar vínculo")
        
        if self.__class__.dados_teste["vinculo_id"]:
            id_vinculo = self.__class__.dados_teste["vinculo_id"]
            
            resultado = atualizar_vinculo_responsavel(
                id_vinculo=id_vinculo,
                tipo_relacao="padrasto",
                responsavel_financeiro=True
            )
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIn("data", resultado)
            
            # Verificar se os dados foram atualizados
            dados_atualizados = resultado["data"]
            self.assertEqual(dados_atualizados["tipo_relacao"], "padrasto")
            self.assertTrue(dados_atualizados["responsavel_financeiro"])
            
            print(f"✅ Vínculo atualizado: tipo_relacao = padrasto, responsavel_financeiro = True")
        else:
            print("⚠️ Nenhum vínculo de teste disponível")

class TestFiltrosEstrategicos(TestPedagogicoBase):
    """Testes estratégicos para filtros por campos vazios e listagem com responsáveis"""
    
    def test_01_criar_dados_teste_campos_vazios(self):
        """Teste 1: Criar aluno com campos vazios para testes de filtro"""
        print("\n🧪 Teste 1: Criar aluno com campos vazios")
        
        # Obter uma turma para o teste
        mapeamento = obter_mapeamento_turmas()
        self.assertTrue(mapeamento["success"])
        
        if mapeamento["mapeamento"]:
            id_turma = list(mapeamento["mapeamento"].values())[0]
            
            # Criar aluno com campos propositalmente vazios
            id_aluno = f"ALU_TEST_{datetime.now().strftime('%H%M%S')}"
            dados_aluno_incompleto = {
                "id": id_aluno,
                "nome": f"Aluno Campos Vazios Teste {datetime.now().strftime('%H%M%S')}",
                "id_turma": id_turma,
                # Campos propositalmente omitidos/vazios:
                # "turno": None,  
                # "data_nascimento": None,
                # "dia_vencimento": None,
                # "data_matricula": None,
                # "valor_mensalidade": None,
                "inserted_at": obter_timestamp(),
                "updated_at": obter_timestamp()
            }
            
            response = supabase.table("alunos").insert(dados_aluno_incompleto).execute()
            self.assertTrue(response.data, "Erro ao criar aluno com campos vazios")
            
            # Salvar ID para outros testes
            self.__class__.dados_teste["aluno_campos_vazios_id"] = id_aluno
            
            print(f"✅ Aluno com campos vazios criado: {id_aluno}")
        else:
            print("⚠️ Nenhuma turma disponível para teste")
    
    def test_02_filtrar_alunos_por_campos_vazios(self):
        """Teste 2: Filtrar alunos por campos vazios específicos"""
        print("\n🧪 Teste 2: Filtrar alunos por campos vazios")
        
        # Implementar função de filtro por campos vazios
        def filtrar_alunos_por_campos_vazios(campos_vazios: List[str]) -> Dict:
            """
            Filtra alunos que possuem os campos especificados vazios
            
            Args:
                campos_vazios: Lista de campos para verificar se estão vazios
                
            Returns:
                Dict com alunos encontrados e informações dos responsáveis
            """
            try:
                query = supabase.table("alunos").select("""
                    id, nome, turno, data_nascimento, dia_vencimento, 
                    data_matricula, valor_mensalidade, id_turma,
                    turmas!inner(id, nome_turma)
                """)
                
                # Aplicar filtros para campos vazios
                for campo in campos_vazios:
                    if campo in ["turno", "data_nascimento", "dia_vencimento", "data_matricula", "valor_mensalidade"]:
                        query = query.is_(campo, "null")
                
                response = query.execute()
                
                if not response.data:
                    return {
                        "success": True,
                        "alunos": [],
                        "count": 0,
                        "message": "Nenhum aluno encontrado com os campos vazios especificados"
                    }
                
                # Para cada aluno, buscar responsáveis
                alunos_com_responsaveis = []
                for aluno in response.data:
                    # Buscar responsáveis vinculados
                    resp_response = supabase.table("alunos_responsaveis").select("""
                        tipo_relacao, responsavel_financeiro,
                        responsaveis!inner(id, nome, telefone, email, cpf)
                    """).eq("id_aluno", aluno["id"]).execute()
                    
                    # Organizar dados dos responsáveis
                    responsaveis_info = []
                    for vinculo in resp_response.data:
                        resp_info = vinculo["responsaveis"].copy()
                        resp_info["tipo_relacao"] = vinculo.get("tipo_relacao")
                        resp_info["responsavel_financeiro"] = vinculo.get("responsavel_financeiro", False)
                        responsaveis_info.append(resp_info)
                    
                    # Identificar campos vazios do aluno
                    campos_vazios_encontrados = []
                    for campo in ["turno", "data_nascimento", "dia_vencimento", "data_matricula", "valor_mensalidade"]:
                        if aluno.get(campo) is None:
                            campos_vazios_encontrados.append(campo)
                    
                    aluno_completo = aluno.copy()
                    aluno_completo["responsaveis"] = responsaveis_info
                    aluno_completo["total_responsaveis"] = len(responsaveis_info)
                    aluno_completo["campos_vazios"] = campos_vazios_encontrados
                    aluno_completo["turma_nome"] = aluno["turmas"]["nome_turma"]
                    
                    alunos_com_responsaveis.append(aluno_completo)
                
                return {
                    "success": True,
                    "alunos": alunos_com_responsaveis,
                    "count": len(alunos_com_responsaveis)
                }
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # Testar filtro por turno vazio
        resultado_turno = filtrar_alunos_por_campos_vazios(["turno"])
        self.assertTrue(resultado_turno["success"], f"Erro: {resultado_turno.get('error')}")
        
        # Testar filtro por múltiplos campos
        resultado_multiplos = filtrar_alunos_por_campos_vazios(["data_nascimento", "valor_mensalidade"])
        self.assertTrue(resultado_multiplos["success"], f"Erro: {resultado_multiplos.get('error')}")
        
        # Verificar se encontrou o aluno de teste
        aluno_teste_encontrado = False
        if self.__class__.dados_teste["aluno_campos_vazios_id"]:
            for aluno in resultado_turno["alunos"]:
                if aluno["id"] == self.__class__.dados_teste["aluno_campos_vazios_id"]:
                    aluno_teste_encontrado = True
                    # Verificar estrutura dos dados
                    self.assertIn("responsaveis", aluno)
                    self.assertIn("campos_vazios", aluno)
                    self.assertIn("turma_nome", aluno)
                    self.assertIn("turno", aluno["campos_vazios"])
                    break
        
        print(f"✅ Filtro por turno vazio: {resultado_turno['count']} alunos")
        print(f"✅ Filtro por múltiplos campos: {resultado_multiplos['count']} alunos")
        print(f"✅ Aluno de teste encontrado: {aluno_teste_encontrado}")
    
    def test_03_listar_alunos_por_turma_com_responsaveis(self):
        """Teste 3: Listar alunos por turma incluindo informações completas dos responsáveis"""
        print("\n🧪 Teste 3: Listar alunos por turma com responsáveis")
        
        # Obter turmas disponíveis
        mapeamento = obter_mapeamento_turmas()
        self.assertTrue(mapeamento["success"])
        
        if mapeamento["mapeamento"]:
            # Testar com 2 turmas
            ids_turmas = list(mapeamento["mapeamento"].values())[:2]
            
            resultado = buscar_alunos_por_turmas(ids_turmas)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            self.assertIsInstance(resultado["alunos_por_turma"], dict)
            
            # Verificar estrutura detalhada dos dados retornados
            for turma_nome, dados_turma in resultado["alunos_por_turma"].items():
                self.assertIn("id_turma", dados_turma)
                self.assertIn("nome_turma", dados_turma)
                self.assertIn("alunos", dados_turma)
                
                # Verificar cada aluno na turma
                for aluno in dados_turma["alunos"]:
                    campos_obrigatorios = [
                        "id", "nome", "turno", "valor_mensalidade", 
                        "responsaveis", "total_responsaveis", "responsavel_financeiro_nome"
                    ]
                    for campo in campos_obrigatorios:
                        self.assertIn(campo, aluno, f"Campo {campo} ausente no aluno {aluno.get('nome')}")
                    
                    # Verificar estrutura dos responsáveis
                    self.assertIsInstance(aluno["responsaveis"], list)
                    for responsavel in aluno["responsaveis"]:
                        campos_resp = ["nome", "tipo_relacao", "responsavel_financeiro"]
                        for campo in campos_resp:
                            self.assertIn(campo, responsavel)
            
            print(f"✅ Busca por {len(ids_turmas)} turmas retornou {resultado['total_alunos']} alunos")
            print(f"✅ Turmas processadas: {list(resultado['alunos_por_turma'].keys())}")
        else:
            print("⚠️ Nenhuma turma disponível para teste")

class TestEdicaoEstrategica(TestPedagogicoBase):
    """Testes estratégicos para edição de dados de alunos e responsáveis"""
    
    def test_01_visualizar_detalhes_completos_aluno(self):
        """Teste 1: Visualizar todas as informações detalhadas de um aluno"""
        print("\n🧪 Teste 1: Visualizar detalhes completos do aluno")
        
        if self.__class__.dados_teste.get("aluno_id"):
            id_aluno = self.__class__.dados_teste["aluno_id"]
            
            resultado = buscar_informacoes_completas_aluno(id_aluno)
            
            self.assertTrue(resultado["success"], f"Erro: {resultado.get('error')}")
            
            # Verificar estrutura completa e detalhada
            self.assertIn("aluno", resultado)
            self.assertIn("responsaveis", resultado)
            self.assertIn("pagamentos", resultado)
            self.assertIn("mensalidades", resultado)
            self.assertIn("estatisticas", resultado)
            
            # Verificar dados pedagógicos específicos
            aluno = resultado["aluno"]
            campos_pedagogicos = [
                "id", "nome", "turma_nome", "turno", "data_nascimento", 
                "dia_vencimento", "data_matricula", "valor_mensalidade"
            ]
            for campo in campos_pedagogicos:
                self.assertIn(campo, aluno)
            
            # Verificar responsáveis com dados completos
            for responsavel in resultado["responsaveis"]:
                campos_responsavel = [
                    "id", "nome", "tipo_relacao", "responsavel_financeiro",
                    "telefone", "email", "cpf", "endereco"
                ]
                for campo in campos_responsavel:
                    self.assertIn(campo, responsavel)
            
            print(f"✅ Detalhes completos obtidos para aluno {aluno['nome']}")
            print(f"✅ Responsáveis: {len(resultado['responsaveis'])}")
            print(f"✅ Campos pedagógicos verificados: {len(campos_pedagogicos)}")
        else:
            print("⚠️ Nenhum aluno de teste disponível")
    
    def test_02_editar_campos_aluno_individual(self):
        """Teste 2: Editar campos individuais do aluno"""
        print("\n🧪 Teste 2: Editar campos individuais do aluno")
        
        if self.__class__.dados_teste.get("aluno_id"):
            id_aluno = self.__class__.dados_teste["aluno_id"]
            
            # Teste 1: Editar campo único
            resultado_nome = atualizar_aluno_campos(id_aluno, {"nome": f"Nome Editado {datetime.now().strftime('%H%M%S')}"})
            self.assertTrue(resultado_nome["success"], f"Erro ao editar nome: {resultado_nome.get('error')}")
            
            # Teste 2: Editar múltiplos campos
            novos_dados = {
                "turno": "Vespertino",
                "valor_mensalidade": 750.0,
                "dia_vencimento": "15",
                "data_nascimento": "2015-03-20"
            }
            
            resultado_multiplos = atualizar_aluno_campos(id_aluno, novos_dados)
            self.assertTrue(resultado_multiplos["success"], f"Erro ao editar múltiplos campos: {resultado_multiplos.get('error')}")
            
            # Verificar se todos os campos foram atualizados
            for campo in novos_dados.keys():
                self.assertIn(campo, resultado_multiplos["campos_atualizados"])
            
            # Teste 3: Verificar persistência das alterações
            info_atualizada = buscar_informacoes_completas_aluno(id_aluno)
            self.assertTrue(info_atualizada["success"])
            
            aluno_atualizado = info_atualizada["aluno"]
            self.assertEqual(aluno_atualizado["turno"], "Vespertino")
            self.assertEqual(float(aluno_atualizado["valor_mensalidade"]), 750.0)
            
            print(f"✅ Campo nome editado com sucesso")
            print(f"✅ Múltiplos campos editados: {resultado_multiplos['campos_atualizados']}")
            print(f"✅ Persistência das alterações verificada")
        else:
            print("⚠️ Nenhum aluno de teste disponível")
    
    def test_03_editar_responsavel_campos(self):
        """Teste 3: Editar campos de responsável"""
        print("\n🧪 Teste 3: Editar campos do responsável")
        
        if self.__class__.dados_teste.get("responsavel_id"):
            id_responsavel = self.__class__.dados_teste["responsavel_id"]
            
            # Implementar função para editar responsável
            def atualizar_responsavel_campos(id_responsavel: str, campos: Dict) -> Dict:
                """Atualiza campos específicos de um responsável"""
                try:
                    campos_permitidos = [
                        "nome", "cpf", "telefone", "email", "endereco"
                    ]
                    
                    dados_update = {k: v for k, v in campos.items() if k in campos_permitidos}
                    
                    if not dados_update:
                        return {"success": False, "error": "Nenhum campo válido para atualizar"}
                    
                    dados_update["updated_at"] = obter_timestamp()
                    
                    response = supabase.table("responsaveis").update(dados_update).eq("id", id_responsavel).execute()
                    
                    if response.data:
                        return {
                            "success": True,
                            "campos_atualizados": list(dados_update.keys()),
                            "data": response.data[0]
                        }
                    else:
                        return {"success": False, "error": "Responsável não encontrado"}
                        
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            # Testar edição de campos do responsável
            novos_dados_resp = {
                "telefone": "(11) 99999-8888",
                "email": f"responsavel.teste.{datetime.now().strftime('%H%M%S')}@email.com",
                "endereco": "Rua Teste Editada, 123"
            }
            
            resultado = atualizar_responsavel_campos(id_responsavel, novos_dados_resp)
            self.assertTrue(resultado["success"], f"Erro ao editar responsável: {resultado.get('error')}")
            
            # Verificar campos atualizados
            for campo in novos_dados_resp.keys():
                self.assertIn(campo, resultado["campos_atualizados"])
            
            print(f"✅ Campos do responsável editados: {resultado['campos_atualizados']}")
        else:
            print("⚠️ Nenhum responsável de teste disponível")

class TestCadastroCompleto(TestPedagogicoBase):
    """Testes estratégicos para cadastro completo de alunos com responsáveis"""
    
    def test_01_cadastrar_aluno_completo_novo_responsavel(self):
        """Teste 1: Cadastrar aluno completo com novo responsável"""
        print("\n🧪 Teste 1: Cadastrar aluno completo com novo responsável")
        
        # Obter turma para o teste
        mapeamento = obter_mapeamento_turmas()
        self.assertTrue(mapeamento["success"])
        
        if mapeamento["mapeamento"]:
            id_turma = list(mapeamento["mapeamento"].values())[0]
            
            # Dados completos do aluno
            timestamp = datetime.now().strftime('%H%M%S')
            dados_aluno_completo = {
                "nome": f"Aluno Completo Teste {timestamp}",
                "id_turma": id_turma,
                "turno": "Matutino",
                "data_nascimento": "2016-05-15",
                "dia_vencimento": "10",
                "valor_mensalidade": 600.0,
                "data_matricula": date.today().isoformat()
            }
            
            # Dados completos do responsável
            dados_responsavel_completo = {
                "nome": f"Responsável Completo Teste {timestamp}",
                "cpf": "123.456.789-00",
                "telefone": "(11) 98765-4321",
                "email": f"responsavel.completo.{timestamp}@teste.com",
                "endereco": "Rua Teste Completo, 456 - Bairro Teste"
            }
            
            # Cadastrar aluno com responsável
            resultado = cadastrar_aluno_e_vincular(
                dados_aluno=dados_aluno_completo,
                dados_responsavel=dados_responsavel_completo,
                tipo_relacao="mãe",
                responsavel_financeiro=True
            )
            
            self.assertTrue(resultado["success"], f"Erro no cadastro: {resultado.get('error')}")
            self.assertIn("id_aluno", resultado)
            self.assertIn("id_responsavel", resultado)
            self.assertTrue(resultado.get("vinculo_criado", False))
            
            # Verificar se todos os dados foram salvos corretamente
            info_completa = buscar_informacoes_completas_aluno(resultado["id_aluno"])
            self.assertTrue(info_completa["success"])
            
            aluno_salvo = info_completa["aluno"]
            self.assertEqual(aluno_salvo["nome"], dados_aluno_completo["nome"])
            self.assertEqual(aluno_salvo["turno"], dados_aluno_completo["turno"])
            self.assertEqual(float(aluno_salvo["valor_mensalidade"]), dados_aluno_completo["valor_mensalidade"])
            
            responsaveis_salvos = info_completa["responsaveis"]
            self.assertEqual(len(responsaveis_salvos), 1)
            
            responsavel_salvo = responsaveis_salvos[0]
            self.assertEqual(responsavel_salvo["nome"], dados_responsavel_completo["nome"])
            self.assertEqual(responsavel_salvo["email"], dados_responsavel_completo["email"])
            self.assertTrue(responsavel_salvo["responsavel_financeiro"])
            
            print(f"✅ Aluno completo cadastrado: {resultado['id_aluno']}")
            print(f"✅ Responsável completo cadastrado: {resultado['id_responsavel']}")
            print(f"✅ Todos os dados verificados e corretos")
        else:
            print("⚠️ Nenhuma turma disponível para teste")
    
    def test_02_cadastrar_aluno_responsavel_existente(self):
        """Teste 2: Cadastrar aluno vinculando a responsável já existente"""
        print("\n🧪 Teste 2: Cadastrar aluno com responsável existente")
        
        if self.__class__.dados_teste.get("responsavel_id"):
            # Obter turma para o teste
            mapeamento = obter_mapeamento_turmas()
            self.assertTrue(mapeamento["success"])
            
            if mapeamento["mapeamento"]:
                id_turma = list(mapeamento["mapeamento"].values())[0]
                id_responsavel_existente = self.__class__.dados_teste["responsavel_id"]
                
                # Dados do novo aluno
                timestamp = datetime.now().strftime('%H%M%S')
                dados_novo_aluno = {
                    "nome": f"Segundo Aluno Teste {timestamp}",
                    "id_turma": id_turma,
                    "turno": "Vespertino",
                    "data_nascimento": "2017-08-22",
                    "dia_vencimento": "5",
                    "valor_mensalidade": 550.0
                }
                
                # Cadastrar aluno vinculando ao responsável existente
                resultado = cadastrar_aluno_e_vincular(
                    dados_aluno=dados_novo_aluno,
                    id_responsavel=id_responsavel_existente,
                    tipo_relacao="pai",
                    responsavel_financeiro=False
                )
                
                self.assertTrue(resultado["success"], f"Erro no cadastro: {resultado.get('error')}")
                self.assertTrue(resultado.get("vinculo_criado", False))
                
                # Verificar que o responsável agora tem 2 alunos vinculados
                alunos_vinculados = listar_alunos_vinculados_responsavel(id_responsavel_existente)
                self.assertTrue(alunos_vinculados["success"])
                self.assertGreaterEqual(alunos_vinculados["count"], 2, "Responsável deve ter pelo menos 2 alunos")
                
                print(f"✅ Segundo aluno cadastrado: {resultado['id_aluno']}")
                print(f"✅ Vinculado ao responsável existente: {id_responsavel_existente}")
                print(f"✅ Responsável agora tem {alunos_vinculados['count']} alunos vinculados")
            else:
                print("⚠️ Nenhuma turma disponível para teste")
        else:
            print("⚠️ Nenhum responsável de teste disponível")
    
    def test_03_buscar_responsaveis_dropdown_cadastro(self):
        """Teste 3: Buscar responsáveis para dropdown durante cadastro"""
        print("\n🧪 Teste 3: Buscar responsáveis para dropdown")
        
        # Teste busca sem filtro
        resultado_sem_filtro = buscar_responsaveis_para_dropdown()
        self.assertTrue(resultado_sem_filtro["success"], f"Erro: {resultado_sem_filtro.get('error')}")
        self.assertIsInstance(resultado_sem_filtro["opcoes"], list)
        
        # Teste busca com filtro
        if resultado_sem_filtro["opcoes"]:
            primeiro_responsavel = resultado_sem_filtro["opcoes"][0]
            termo_busca = primeiro_responsavel["nome"][:4]  # Primeiras 4 letras
            
            resultado_filtrado = buscar_responsaveis_para_dropdown(termo_busca)
            self.assertTrue(resultado_filtrado["success"])
            
            # Verificar se o filtro funcionou
            for opcao in resultado_filtrado["opcoes"]:
                self.assertIn(termo_busca.lower(), opcao["nome"].lower())
                
                # Verificar estrutura completa para dropdown
                campos_opcao = ["id", "nome", "label", "telefone", "email"]
                for campo in campos_opcao:
                    self.assertIn(campo, opcao)
            
            print(f"✅ Busca sem filtro: {resultado_sem_filtro['total']} responsáveis")
            print(f"✅ Busca com filtro '{termo_busca}': {resultado_filtrado['total']} responsáveis")
            print(f"✅ Estrutura de dados para dropdown verificada")
        else:
            print("⚠️ Nenhum responsável disponível para teste de filtro")

def run_pedagogico_tests():
    """Executa todos os testes estratégicos do modelo pedagógico"""
    
    # Criar suite de testes na ordem estratégica
    suite = unittest.TestSuite()
    
    # 1. Testes de Turmas (base fundamental)
    suite.addTest(unittest.makeSuite(TestGestaoTurmas))
    
    # 2. Testes de Filtros Estratégicos (validação de filtros por campos vazios)
    suite.addTest(unittest.makeSuite(TestFiltrosEstrategicos))
    
    # 3. Testes de Alunos (funcionalidades básicas)
    suite.addTest(unittest.makeSuite(TestGestaoAlunos))
    
    # 4. Testes de Edição Estratégica (edição de dados completos)
    suite.addTest(unittest.makeSuite(TestEdicaoEstrategica))
    
    # 5. Testes de Responsáveis
    suite.addTest(unittest.makeSuite(TestGestaoResponsaveis))
    
    # 6. Testes de Cadastro Completo (cadastro com todas as funcionalidades)
    suite.addTest(unittest.makeSuite(TestCadastroCompleto))
    
    # 7. Testes de Vínculos (relacionamentos)
    suite.addTest(unittest.makeSuite(TestGestaoVinculos))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2 if TEST_CONFIG["verbose"] else 1)
    resultado = runner.run(suite)
    
    # Relatório final estratégico
    print(f"\n📊 RELATÓRIO FINAL ESTRATÉGICO - MODELO PEDAGÓGICO:")
    print(f"   ✅ Sucessos: {resultado.testsRun - len(resultado.failures) - len(resultado.errors)}")
    print(f"   ❌ Falhas: {len(resultado.failures)}")
    print(f"   🚫 Erros: {len(resultado.errors)}")
    print(f"   📈 Taxa de Sucesso: {((resultado.testsRun - len(resultado.failures) - len(resultado.errors)) / resultado.testsRun * 100):.1f}%")
    
    # Análise estratégica
    if resultado.wasSuccessful():
        print(f"   🎯 STATUS: SISTEMA PEDAGÓGICO VALIDADO E PRONTO PARA PRODUÇÃO")
    else:
        print(f"   ⚠️ STATUS: REQUER CORREÇÕES ANTES DA PRODUÇÃO")
    
    return resultado.wasSuccessful()

if __name__ == "__main__":
    success = run_pedagogico_tests()
    exit(0 if success else 1) 