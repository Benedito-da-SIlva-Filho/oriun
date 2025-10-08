-- ============================================================
-- 📜 Script: sentinela_global.sql
-- 🛡️ Propósito: Aplicar triggers de log em todas as tabelas de todos os schemas do sistema
-- 🧠 Contexto: Projeto Oriun — onde cada dado é memória, cada operação é testemunho
-- ============================================================

-- ✍️ Autor: Benedito & Pílades
-- 📅 Data de criação: 12/09/2025
-- 🔄 Última revisão: [preencher conforme evolução]
-- 🧭 Missão: Garantir que toda movimentação (INSERT, UPDATE, DELETE)
--           seja registrada com clareza, fidelidade e rastreabilidade
--           em "01-Cadastros".a016_log_movimentacoes, respeitando o schema de origem

-- ============================================================
-- 🧩 Componentes:
-- 1. Criação da tabela de log
-- 2. Função genérica de log: fn_log_movimentacao()
-- 3. Loop dinâmico para aplicar triggers em todas as tabelas de todos os schemas
-- 4. Registro de auditoria da aplicação das triggers
-- 5. Emissão do relatório via view: log_auditoria
-- ============================================================

-- 🌾 Porque no Oriun, até o log tem alma.
-- ============================================================

-- 1️⃣ Criação da tabela de log
CREATE SCHEMA IF NOT EXISTS "01-Cadastros";

CREATE TABLE IF NOT EXISTS "01-Cadastros".a016_log_movimentacoes (
    id_log SERIAL PRIMARY KEY,
    schema_origem TEXT NOT NULL,
    tabela_origem TEXT NOT NULL,
    operacao TEXT NOT NULL,
    data_movimentacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_postgresql TEXT NOT NULL,
    valores_anteriores JSONB,
    valores_novos JSONB
);

-- 2️⃣ Função de log
CREATE OR REPLACE FUNCTION fn_log_movimentacao()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO "01-Cadastros".a016_log_movimentacoes (
    schema_origem,
    tabela_origem,
    operacao,
    data_movimentacao,
    usuario_postgresql,
    valores_anteriores,
    valores_novos
  )
  VALUES (
    TG_TABLE_SCHEMA,
    TG_TABLE_NAME,
    TG_OP,
    CURRENT_TIMESTAMP,
    SESSION_USER,
    row_to_json(OLD),
    row_to_json(NEW)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3️⃣ Tabela de auditoria da aplicação das triggers
CREATE TABLE IF NOT EXISTS "01-Cadastros".a017_relatorio_sentinela (
    id_relatorio SERIAL PRIMARY KEY,
    data_execucao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    schema_alvo TEXT NOT NULL,
    tabela_alvo TEXT NOT NULL,
    trigger_aplicada TEXT NOT NULL,
    status TEXT NOT NULL
);

-- 4️⃣ Aplicação global das triggers + registro de auditoria
DO $$
DECLARE
  r RECORD;
BEGIN
  FOR r IN
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE'
      AND table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
  LOOP
    BEGIN
      EXECUTE format('
        DROP TRIGGER IF EXISTS trg_log_%I ON %I.%I;
        CREATE TRIGGER trg_log_%I
        AFTER INSERT OR UPDATE OR DELETE ON %I.%I
        FOR EACH ROW EXECUTE FUNCTION fn_log_movimentacao();',
        r.table_name, r.table_schema, r.table_name,
        r.table_name, r.table_schema, r.table_name
      );

      INSERT INTO "01-Cadastros".a017_relatorio_sentinela (
        schema_alvo, tabela_alvo, trigger_aplicada, status
      ) VALUES (
        r.table_schema, r.table_name, 'trg_log_' || r.table_name, 'SUCESSO'
      );

    EXCEPTION WHEN OTHERS THEN
      INSERT INTO "01-Cadastros".a017_relatorio_sentinela (
        schema_alvo, tabela_alvo, trigger_aplicada, status
      ) VALUES (
        r.table_schema, r.table_name, 'trg_log_' || r.table_name, 'ERRO: ' || SQLERRM
      );
    END;
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 5️⃣ Emissão do relatório via view
CREATE OR REPLACE VIEW "01-Cadastros".log_auditoria AS
SELECT
  id_relatorio,
  data_execucao,
  schema_alvo,
  tabela_alvo,
  trigger_aplicada,
  status
FROM "01-Cadastros".a017_relatorio_sentinela
ORDER BY data_execucao DESC;
