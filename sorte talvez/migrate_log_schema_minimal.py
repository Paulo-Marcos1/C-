#!/usr/bin/env python3.11
import sqlite3
import os

# Script para adicionar colunas faltantes na tabela Log (versão mínima)

def adicionar_coluna_se_nao_existir(cursor, nome_tabela, nome_coluna, tipo_coluna):
    """Adiciona uma coluna a uma tabela se ela não existir."""
    cursor.execute(f"PRAGMA table_info({nome_tabela})")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    if nome_coluna not in colunas_existentes:
        try:
            cursor.execute(f"ALTER TABLE {nome_tabela} ADD COLUMN {nome_coluna} {tipo_coluna}")
            print(f"Coluna '{nome_coluna}' adicionada à tabela '{nome_tabela}'.")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar coluna '{nome_coluna}' à tabela '{nome_tabela}': {e}")
            return False
    else:
        print(f"Coluna '{nome_coluna}' já existe na tabela '{nome_tabela}'.")
        return True

def main():
    nome_banco = os.path.join(os.path.dirname(__file__), "banco.sqlite")
    conn = None
    try:
        conn = sqlite3.connect(nome_banco)
        cursor = conn.cursor()
        print("Conectado ao banco para migração da tabela Log...")

        # Adiciona as colunas necessárias
        sucesso1 = adicionar_coluna_se_nao_existir(cursor, "Log", "cpf_modificador", "TEXT")
        sucesso2 = adicionar_coluna_se_nao_existir(cursor, "Log", "nome_modificador", "TEXT")
        sucesso3 = adicionar_coluna_se_nao_existir(cursor, "Log", "cpf_modificado", "TEXT")

        if sucesso1 and sucesso2 and sucesso3:
            conn.commit()
            print("Migração do schema da tabela Log concluída com sucesso.")
        else:
            print("Migração do schema da tabela Log falhou ou não foi necessária.")

    except sqlite3.Error as e:
        print(f"Erro durante a migração do schema da tabela Log: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco fechada.")

if __name__ == "__main__":
    main()

