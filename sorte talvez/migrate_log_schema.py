import sqlite3
import os

def migrate_log_table(db_path):
    """Migrates the Log table to the new schema with ON DELETE SET NULL."""
    conn = None
    try:
        print(f"Conectando ao banco de dados: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Verificando a estrutura atual da tabela Log...")
        cursor.execute("PRAGMA table_info(Log)")
        columns = cursor.fetchall()
        # Check if migration is needed (e.g., if cpf_alvo is NOT NULL or foreign key is different)
        # For simplicity, we'll assume migration is needed if this script is run.
        # A more robust check would compare the exact PRAGMA foreign_key_list(Log) output.

        print("Iniciando migração da tabela Log...")

        # 1. Desabilitar chaves estrangeiras temporariamente
        cursor.execute("PRAGMA foreign_keys=OFF;")

        # Iniciar transação
        cursor.execute("BEGIN TRANSACTION;")

        # 2. Renomear a tabela Log antiga
        print("Renomeando tabela Log para Log_old...")
        cursor.execute("ALTER TABLE Log RENAME TO Log_old;")

        # 3. Criar a nova tabela Log com a estrutura correta
        print("Criando nova tabela Log com schema atualizado...")
        cursor.execute(
            """CREATE TABLE Log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf_adm INTEGER, -- Can be NULL for system actions/self-registration
                cpf_alvo INTEGER, -- Made nullable
                acao TEXT NOT NULL,
                data_hora TEXT,
                FOREIGN KEY (cpf_adm) REFERENCES Adm(cpf) ON DELETE SET NULL,
                FOREIGN KEY (cpf_alvo) REFERENCES Pessoa(cpf) ON DELETE SET NULL -- Key change
            )"""
        )

        # 4. Copiar os dados da tabela antiga para a nova
        print("Copiando dados de Log_old para Log...")
        cursor.execute("INSERT INTO Log (id, cpf_adm, cpf_alvo, acao, data_hora) SELECT id, cpf_adm, cpf_alvo, acao, data_hora FROM Log_old;")

        # 5. Remover a tabela antiga
        print("Removendo tabela Log_old...")
        cursor.execute("DROP TABLE Log_old;")

        # Finalizar transação
        conn.commit()
        print("Transação concluída.")

        # 6. Reabilitar chaves estrangeiras
        cursor.execute("PRAGMA foreign_keys=ON;")

        print("Migração da tabela Log concluída com sucesso!")

    except sqlite3.Error as e:
        print(f"Erro durante a migração: {e}")
        if conn:
            print("Revertendo alterações...")
            conn.rollback() # Rollback em caso de erro
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco fechada.")

if __name__ == "__main__":
    # Assume o banco está no mesmo diretório que os outros scripts
    db_file = os.path.join(os.path.dirname(__file__), "banco.sqlite")
    if os.path.exists(db_file):
        migrate_log_table(db_file)
    else:
        print(f"Erro: Arquivo do banco de dados não encontrado em {db_file}")

