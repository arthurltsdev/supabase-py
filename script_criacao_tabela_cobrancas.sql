-- ================================================
-- 🎯 CRIAÇÃO DA TABELA COBRANÇAS
-- ================================================
-- 
-- Tabela para gerenciar cobranças adicionais além das mensalidades:
-- - Formatura (parcelas)
-- - Eventos e taxas
-- - Dívidas anteriores
-- - Cobranças pontuais
--

CREATE TABLE cobrancas (
    -- Identificação
    id_cobranca TEXT PRIMARY KEY,
    id_aluno TEXT NOT NULL REFERENCES alunos(id),
    id_responsavel TEXT REFERENCES responsaveis(id),
    
    -- Informações da cobrança
    titulo TEXT NOT NULL, -- "Formatura 2025", "Taxa de Material", "Festa Junina"
    descricao TEXT, -- Detalhes adicionais
    valor NUMERIC NOT NULL CHECK (valor > 0),
    
    -- Datas
    data_vencimento DATE NOT NULL,
    data_pagamento DATE, -- NULL se não pago ainda
    
    -- Status e classificação
    status TEXT DEFAULT 'Pendente' CHECK (status IN ('Pendente', 'Pago', 'Vencido', 'Cancelado')),
    tipo_cobranca TEXT DEFAULT 'outros' CHECK (tipo_cobranca IN (
        'formatura', 'evento', 'taxa', 'material', 'uniforme', 
        'divida', 'renegociacao', 'outros'
    )),
    
    -- Agrupamento de parcelas
    grupo_cobranca TEXT, -- ID único para agrupar parcelas relacionadas (ex: "FORM_2025_ALU123")
    parcela_numero INTEGER DEFAULT 1 CHECK (parcela_numero > 0),
    parcela_total INTEGER DEFAULT 1 CHECK (parcela_total > 0),
    
    -- Integração com pagamentos
    id_pagamento TEXT REFERENCES pagamentos(id_pagamento), -- Quando a cobrança for paga
    
    -- Observações e metadados
    observacoes TEXT,
    prioridade INTEGER DEFAULT 1 CHECK (prioridade BETWEEN 1 AND 5), -- 1=baixa, 5=alta
    
    -- Timestamps
    inserted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ================================================
-- 📋 ÍNDICES PARA PERFORMANCE
-- ================================================

-- Índice para busca por aluno (mais comum)
CREATE INDEX idx_cobrancas_aluno ON cobrancas(id_aluno);

-- Índice para busca por responsável
CREATE INDEX idx_cobrancas_responsavel ON cobrancas(id_responsavel);

-- Índice para busca por status e data
CREATE INDEX idx_cobrancas_status_vencimento ON cobrancas(status, data_vencimento);

-- Índice para busca por grupo (parcelas relacionadas)
CREATE INDEX idx_cobrancas_grupo ON cobrancas(grupo_cobranca) WHERE grupo_cobranca IS NOT NULL;

-- Índice para busca por tipo
CREATE INDEX idx_cobrancas_tipo ON cobrancas(tipo_cobranca);

-- ================================================
-- 🔧 TRIGGERS PARA ATUALIZAÇÃO AUTOMÁTICA
-- ================================================

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_cobrancas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cobrancas_updated_at
    BEFORE UPDATE ON cobrancas
    FOR EACH ROW
    EXECUTE FUNCTION update_cobrancas_updated_at();

-- ================================================
-- ✅ COMENTÁRIOS PARA DOCUMENTAÇÃO
-- ================================================

COMMENT ON TABLE cobrancas IS 'Tabela para gerenciar cobranças adicionais além das mensalidades regulares';
COMMENT ON COLUMN cobrancas.id_cobranca IS 'ID único da cobrança (formato: COB_XXXXXX)';
COMMENT ON COLUMN cobrancas.titulo IS 'Título descritivo da cobrança (ex: Formatura 2025 - Parcela 1/6)';
COMMENT ON COLUMN cobrancas.grupo_cobranca IS 'ID para agrupar parcelas relacionadas (ex: FORM_2025_ALU123)';
COMMENT ON COLUMN cobrancas.parcela_numero IS 'Número da parcela atual (1, 2, 3...)';
COMMENT ON COLUMN cobrancas.parcela_total IS 'Total de parcelas no grupo';
COMMENT ON COLUMN cobrancas.prioridade IS 'Prioridade da cobrança: 1=baixa, 2=normal, 3=média, 4=alta, 5=urgente';

-- ================================================
-- 📊 EXEMPLOS DE USO
-- ================================================

/*
-- Exemplo 1: Cadastrar formatura com 6 parcelas
INSERT INTO cobrancas (id_cobranca, id_aluno, id_responsavel, titulo, valor, data_vencimento, tipo_cobranca, grupo_cobranca, parcela_numero, parcela_total) VALUES
('COB_001', 'ALU_123456', 'RES_789', 'Formatura 2025 - Parcela 1/6', 150.00, '2025-02-05', 'formatura', 'FORM_2025_ALU123456', 1, 6),
('COB_002', 'ALU_123456', 'RES_789', 'Formatura 2025 - Parcela 2/6', 150.00, '2025-03-05', 'formatura', 'FORM_2025_ALU123456', 2, 6),
('COB_003', 'ALU_123456', 'RES_789', 'Formatura 2025 - Parcela 3/6', 150.00, '2025-04-05', 'formatura', 'FORM_2025_ALU123456', 3, 6),
('COB_004', 'ALU_123456', 'RES_789', 'Formatura 2025 - Parcela 4/6', 150.00, '2025-05-05', 'formatura', 'FORM_2025_ALU123456', 4, 6),
('COB_005', 'ALU_123456', 'RES_789', 'Formatura 2025 - Parcela 5/6', 150.00, '2025-06-05', 'formatura', 'FORM_2025_ALU123456', 5, 6),
('COB_006', 'ALU_123456', 'RES_789', 'Formatura 2025 - Parcela 6/6', 150.00, '2025-07-05', 'formatura', 'FORM_2025_ALU123456', 6, 6);

-- Exemplo 2: Taxa pontual
INSERT INTO cobrancas (id_cobranca, id_aluno, id_responsavel, titulo, descricao, valor, data_vencimento, tipo_cobranca, prioridade) VALUES
('COB_007', 'ALU_123456', 'RES_789', 'Taxa de Material Escolar', 'Kit completo de material para o ano letivo 2025', 280.00, '2025-01-15', 'material', 3);

-- Exemplo 3: Dívida anterior
INSERT INTO cobrancas (id_cobranca, id_aluno, id_responsavel, titulo, descricao, valor, data_vencimento, tipo_cobranca, observacoes, prioridade) VALUES
('COB_008', 'ALU_123456', 'RES_789', 'Dívida - Dezembro 2024', 'Mensalidade em atraso de dezembro/2024', 300.00, '2025-01-10', 'divida', 'Renegociado para pagamento até 10/01/2025', 4);
*/ 