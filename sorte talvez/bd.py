import sqlite3
import os
from cadastro import Cadastro
from cadastro import Cadastro_adm
from datetime import datetime # Import datetime at the top

class BancoDeDados:
    def __init__(self, nome_banco="banco.sqlite"):
        self.nome_banco = os.path.join(os.path.dirname(__file__), nome_banco)
        self.conn = None

    def conectar(self):
        try:
            self.conn = sqlite3.connect(self.nome_banco, timeout=10, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            print("Conexão aberta e PRAGMA foreign_keys=ON executado.")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            self.conn = None
            return False

    def criar_tabelas(self):
        if not self.conn:
            if not self.conectar():
                print("Não foi possível conectar ao banco para criar tabelas.")
                return False
        try:
            self.cadastrar() # Creates Pessoa table
            self.cadastrar_adm() # Creates Adm table
            self.banco_log() # Creates/Updates Log table
            return True
        except Exception as e:
            print(f"Erro durante a criação de tabelas: {e}")
            return False

    # --- Pessoa Methods --- 
    def cadastrar(self):
        """Cria a tabela Pessoa se não existir."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Pessoa(
                    cpf INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    bloco INTEGER,
                    numero_ap INTEGER,
                    email TEXT NOT NULL UNIQUE,
                    data_cadastro TEXT
                    )"""
                )
                self.conn.commit()
                print("Tabela Pessoa verificada/criada.")
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela Pessoa: {e}")
                raise

    def inserir_pessoa(self, pessoa: Cadastro, cpf_adm=None):
        """Insere uma nova pessoa e registra o log. cpf_adm=None para auto-cadastro."""
        if not self.conn:
            print("Erro: Sem conexão com o banco para inserir pessoa.")
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Pessoa (cpf, nome, login, senha, bloco, numero_ap, email, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (pessoa.cpf, pessoa.nome, pessoa.login, pessoa.get_senha(), pessoa.bloco, pessoa.numero_ap,
                 pessoa.email, pessoa.data_cadastro)
            )
            acao_log = "Cadastro de novo usuário" if cpf_adm else "Auto-cadastro de usuário"
            log_id = self.inserir_log(cpf_adm, pessoa.cpf, acao_log)
            if log_id is None:
                print(f"Erro ao inserir log para {acao_log}. Revertendo inserção de pessoa.")
                self.conn.rollback()
                # Não retorna False aqui, deixa a exceção do inserir_log propagar se houver
                # return False 
                # A exceção será capturada na camada superior (adm.py ou interface.py)
                raise sqlite3.Error(f"Falha ao registrar log para {acao_log}.")
            self.conn.commit()
            print(f"Pessoa inserida com sucesso! Log ID: {log_id}")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao inserir pessoa: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: CPF ou Login ou Email já cadastrado ({e})")
            raise # Re-raise a exceção para ser tratada na interface

    def atualizar_pessoa(self, cpf, cpf_adm=None, novo_nome=None, novo_email=None, novo_login=None, novo_senha=None,
                         novo_bloco=None, novo_numero_ap=None):
        """Atualiza dados de uma pessoa e registra o log. cpf_adm=None para auto-atualização."""
        if not self.conn:
            print("Erro: Sem conexão com o banco para atualizar pessoa.")
            return False
        updates = []
        params = []
        if novo_nome is not None: updates.append("nome = ?"); params.append(novo_nome)
        if novo_email is not None: updates.append("email = ?"); params.append(novo_email)
        if novo_login is not None: updates.append("login = ?"); params.append(novo_login)
        if novo_senha is not None: updates.append("senha = ?"); params.append(novo_senha)
        if novo_bloco is not None: updates.append("bloco = ?"); params.append(novo_bloco)
        if novo_numero_ap is not None: updates.append("numero_ap = ?"); params.append(novo_numero_ap)
        
        if not updates:
            print("Nenhuma atualização solicitada para Pessoa.")
            return False # Ou True? Considerar se nenhuma mudança é sucesso ou não.
            
        params.append(cpf)
        sql = f"UPDATE Pessoa SET {", ".join(updates)} WHERE cpf = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(params))
            if cursor.rowcount > 0:
                acao_log = "Usuário atualizado por ADM" if cpf_adm else "Usuário atualizou próprios dados"
                log_id = self.inserir_log(cpf_adm, cpf, acao_log)
                if log_id is None:
                    print(f"Erro ao inserir log para {acao_log}. Revertendo atualização.")
                    self.conn.rollback()
                    raise sqlite3.Error(f"Falha ao registrar log para {acao_log}.")
                self.conn.commit()
                print(f"Pessoa atualizada com sucesso! Log ID: {log_id}")
                return True
            else:
                print(f"Nenhuma pessoa encontrada com o CPF {cpf} para atualizar.")
                return False
        except sqlite3.Error as e:
            print(f"Erro ao atualizar pessoa: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: Login ou Email já cadastrado por outro usuário ({e})")
            raise

    def deletar_pessoa(self, cpf, cpf_adm=None):
        """Deleta uma pessoa e registra o log. cpf_adm=None para auto-exclusão."""
        if not self.conn:
            raise ConnectionError("Sem conexão com o banco para deletar pessoa.")
        
        print(f"[BD DEBUG] deletar_pessoa - Tentando excluir CPF: {cpf} por ADM: {cpf_adm}")
        
        try:
            cursor = self.conn.cursor()
            # Verifica se a pessoa existe antes de tentar deletar
            cursor.execute("SELECT nome FROM Pessoa WHERE cpf = ?", (cpf,))
            pessoa = cursor.fetchone()
            
            if pessoa:
                # Tenta inserir o log ANTES de deletar
                acao_log = "Usuário excluído por ADM" if cpf_adm else "Usuário excluiu própria conta"
                print(f"[BD DEBUG] deletar_pessoa - Tentando inserir log ANTES da exclusão. ADM: {cpf_adm}, Alvo: {cpf}, Ação: {acao_log}")
                log_id = self.inserir_log(cpf_adm, cpf, acao_log)
                
                if log_id is None:
                    # Se o log falhar, não prossegue com a exclusão
                    print(f"[BD ERROR] Falha ao inserir log para {acao_log}. Exclusão cancelada.")
                    # Não precisa de rollback aqui pois nada foi alterado ainda
                    raise sqlite3.Error(f"Falha ao registrar log de {acao_log}. Exclusão cancelada.")
                
                # Se o log foi inserido com sucesso, deleta a pessoa
                print(f"[BD DEBUG] deletar_pessoa - Log ID {log_id} inserido. Prosseguindo com DELETE para CPF {cpf}.")
                cursor.execute("DELETE FROM Pessoa WHERE cpf = ?", (cpf,))
                
                if cursor.rowcount > 0:
                    self.conn.commit()
                    print(f"Pessoa (CPF: {cpf}) deletada com sucesso! Log ID: {log_id}")
                    return True
                else:
                    # Isso não deveria acontecer se o log foi inserido, mas por segurança:
                    print(f"[BD ERROR] Erro INESPERADO ao deletar: Usuário com CPF {cpf} não encontrado APÓS inserção do log (rowcount=0).")
                    self.conn.rollback() # Desfaz a inserção do log
                    return False
            else:
                print(f"Usuário com CPF {cpf} não encontrado para exclusão.")
                return False
        except sqlite3.Error as e:
            # Captura erros do log ou do delete
            print(f"[BD ERROR] Erro SQLite ao deletar pessoa (CPF: {cpf}): {e}")
            self.conn.rollback() # Garante rollback em caso de erro
            raise # Re-raise para a camada superior tratar

    def listar_pessoas(self):
        """Lista todas as pessoas."""
        if not self.conn:
            if not self.conectar(): return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Pessoa")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar pessoas: {e}")
            return []

    # --- Adm Methods --- 
    def cadastrar_adm(self):
        """Cria a tabela Adm se não existir."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS Adm(
                    cpf INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    login TEXT NOT NULL UNIQUE,
                    senha TEXT NOT NULL,
                    data_cadastro TEXT
                    )"""
                )
                self.conn.commit()
                print("Tabela Adm verificada/criada.")
            except sqlite3.Error as e:
                print(f"Erro ao criar tabela Adm: {e}")
                raise

    def inserir_adm(self, adm: Cadastro_adm):
        """Insere um novo administrador."""
        if not self.conn:
             print("Erro: Sem conexão com o banco para inserir ADM.")
             return False
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO Adm (cpf, nome, login, senha, data_cadastro) VALUES (?, ?, ?, ?, ?)",
                (adm.cpf, adm.nome, adm.login, adm.get_senha(), adm.data_cadastro)
            )
            # Log ADM creation (sem alvo específico, executor é o sistema/outro ADM?)
            # Por ora, não logando criação de ADM para simplificar.
            self.conn.commit()
            print("Adm inserido com sucesso!")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao inserir adm: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: CPF ou Login de ADM já cadastrado ({e})")
            raise

    def listar_adms(self):
        """Lista todos os administradores."""
        if not self.conn:
            if not self.conectar(): return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT cpf, nome, login, data_cadastro FROM Adm")
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar administradores: {e}")
            return []

    def atualizar_adm(self, cpf_adm_executor, cpf_adm_alvo, novo_nome=None, novo_login=None, nova_senha=None):
        """Atualiza dados de um administrador."""
        if not self.conn:
            print("Erro: Sem conexão com o banco para atualizar ADM.")
            return False
        updates = []
        params = []
        if novo_nome is not None: updates.append("nome = ?"); params.append(novo_nome)
        if novo_login is not None: updates.append("login = ?"); params.append(novo_login)
        if nova_senha is not None: updates.append("senha = ?"); params.append(nova_senha)
        
        if not updates:
            print("Nenhuma atualização solicitada para ADM.")
            return False
            
        params.append(cpf_adm_alvo)
        sql = f"UPDATE Adm SET {", ".join(updates)} WHERE cpf = ?"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(params))
            if cursor.rowcount > 0:
                # Log ADM update (Executor: cpf_adm_executor, Alvo: cpf_adm_alvo)
                # Ação pode ser "ADM atualizou dados de outro ADM"
                # A tabela Log atualmente só tem FK para Pessoa como alvo.
                # Para logar ações sobre ADMs, precisaríamos alterar a tabela Log ou criar outra.
                # Por ora, não logando.
                self.conn.commit()
                print(f"Administrador (CPF: {cpf_adm_alvo}) atualizado com sucesso!")
                return True
            else:
                print(f"Nenhum administrador encontrado com o CPF {cpf_adm_alvo} para atualizar.")
                return False
        except sqlite3.Error as e:
            print(f"Erro ao atualizar administrador: {e}")
            self.conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                 raise ValueError(f"Erro: Login de ADM já cadastrado por outro administrador ({e})")
            raise

    def deletar_adm(self, cpf_adm_executor, cpf_adm_alvo):
        """Deleta um administrador."""
        if not self.conn:
            raise ConnectionError("Sem conexão com o banco para deletar ADM.")
        if cpf_adm_executor == cpf_adm_alvo:
            raise ValueError("Administrador não pode excluir a própria conta.")
            
        print(f"[BD DEBUG] deletar_adm - Tentando excluir ADM CPF: {cpf_adm_alvo} por ADM: {cpf_adm_executor}")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT nome FROM Adm WHERE cpf = ?", (cpf_adm_alvo,))
            adm = cursor.fetchone()
            if adm:
                # Log ADM deletion (Executor: cpf_adm_executor, Alvo: cpf_adm_alvo)
                # Novamente, a tabela Log não suporta ADM como alvo.
                # Não logando por enquanto.
                
                # Deleta o ADM
                cursor.execute("DELETE FROM Adm WHERE cpf = ?", (cpf_adm_alvo,))
                if cursor.rowcount > 0:
                    self.conn.commit()
                    print(f"Administrador (CPF: {cpf_adm_alvo}) deletado com sucesso!")
                    # Precisamos também anular o cpf_adm nos logs onde este ADM era o executor?
                    # A FK na tabela Log já tem ON DELETE SET NULL para cpf_adm.
                    return True
                else:
                    print(f"[BD ERROR] Erro INESPERADO ao deletar ADM: ADM com CPF {cpf_adm_alvo} não encontrado APÓS verificação inicial (rowcount=0).")
                    self.conn.rollback()
                    return False
            else:
                print(f"Administrador com CPF {cpf_adm_alvo} não encontrado para exclusão.")
                return False
        except sqlite3.Error as e:
            print(f"[BD ERROR] Erro SQLite ao deletar administrador (CPF: {cpf_adm_alvo}): {e}")
            self.conn.rollback()
            # Se o erro for FOREIGN KEY, pode ser que este ADM ainda seja referenciado em Log
            # A cláusula ON DELETE SET NULL deveria cuidar disso. Investigar se a FK está correta.
            raise

    # --- Login and Log Methods --- 
    @staticmethod
    def validar_login(login, senha):
        # Esta função não precisa de self.conn, usa conexão própria e fecha
        conn = None
        try:
            db_path = os.path.join(os.path.dirname(__file__), "banco.sqlite")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Verifica ADM primeiro
            cursor.execute("SELECT cpf, nome FROM Adm WHERE login = ? AND senha = ?", (login, senha))
            adm = cursor.fetchone()
            if adm:
                print(f"Login ADM bem-sucedido para {login}")
                return ("adm", adm[0], adm[1]) # Retorna (tipo, cpf, nome)
            # Se não for ADM, verifica Pessoa
            cursor.execute("SELECT cpf, nome, bloco, numero_ap, email FROM Pessoa WHERE login = ? AND senha = ?", (login, senha))
            pessoa = cursor.fetchone()
            if pessoa:
                print(f"Login Pessoa bem-sucedido para {login}")
                return ("pessoa", pessoa[0], pessoa[1], pessoa[2], pessoa[3], pessoa[4]) # Retorna (tipo, cpf, nome, bloco, ap, email)
            # Se não encontrou nenhum
            print(f"Login ou senha inválidos para {login}.")
            return None
        except sqlite3.Error as e:
            print(f"Erro durante validação de login: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def banco_log(self):
        """Cria ou atualiza a tabela Log, garantindo FKs corretas."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                # Verifica se a tabela Log existe
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Log';")
                table_exists = cursor.fetchone()
                
                # Define a estrutura desejada
                create_table_sql = """
                    CREATE TABLE Log(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpf_adm INTEGER, 
                        cpf_alvo INTEGER, 
                        acao TEXT NOT NULL,
                        data_hora TEXT,
                        FOREIGN KEY (cpf_adm) REFERENCES Adm(cpf) ON DELETE SET NULL,
                        FOREIGN KEY (cpf_alvo) REFERENCES Pessoa(cpf) ON DELETE SET NULL
                    )
                """
                
                if not table_exists:
                    print("Tabela Log não existe. Criando...")
                    cursor.execute(create_table_sql)
                else:
                    # Se existe, verifica as FKs (SQLite não tem ALTER TABLE fácil para FKs)
                    # A maneira mais segura é recriar se a estrutura não for a ideal
                    # Mas isso pode ser complexo com dados existentes. 
                    # Por ora, vamos assumir que a criação inicial ou a migração anterior
                    # deixou a tabela correta com ON DELETE SET NULL.
                    print("Tabela Log já existe. Verificação de estrutura não implementada.")
                    # Poderíamos verificar PRAGMA foreign_key_list('Log') aqui se necessário.
                    
                self.conn.commit()
                print("Tabela Log verificada/criada.")
            except sqlite3.Error as e:
                print(f"Erro ao criar/verificar tabela Log: {e}")
                raise

    def inserir_log(self, cpf_adm, cpf_alvo, acao):
        """Insere um registro na tabela Log. Returns log ID on success, raises error on failure."""
        if not self.conn:
             print("Erro: Sem conexão com o banco para inserir log.")
             raise ConnectionError("Sem conexão com o banco para inserir log.")
             
        print(f"[BD DEBUG] inserir_log - Tentando inserir: ADM={cpf_adm}, Alvo={cpf_alvo}, Ação='{acao}'")
        
        try:
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.conn.cursor()
            
            # Verifica se cpf_adm existe SE ele for fornecido
            if cpf_adm is not None:
                cursor.execute("SELECT 1 FROM Adm WHERE cpf = ?", (cpf_adm,))
                if cursor.fetchone() is None:
                    print(f"[BD ERROR] Falha ao inserir log: CPF do ADM executor ({cpf_adm}) não encontrado na tabela Adm.")
                    # Não insere o log se o ADM não existe
                    raise sqlite3.IntegrityError(f"FOREIGN KEY constraint failed: ADM CPF {cpf_adm} não existe.")
            
            # Verifica se cpf_alvo existe SE ele for fornecido E a ação não for exclusão
            # (Na exclusão, o alvo está prestes a ser deletado, então não verificamos)
            # if cpf_alvo is not None and "excluído" not in acao and "excluiu" not in acao:
            #     cursor.execute("SELECT 1 FROM Pessoa WHERE cpf = ?", (cpf_alvo,))
            #     if cursor.fetchone() is None:
            #         print(f"[BD ERROR] Falha ao inserir log: CPF do usuário alvo ({cpf_alvo}) não encontrado na tabela Pessoa.")
            #         raise sqlite3.IntegrityError(f"FOREIGN KEY constraint failed: Pessoa CPF {cpf_alvo} não existe.")

            # Insere o log
            cursor.execute(
                "INSERT INTO Log (cpf_adm, cpf_alvo, acao, data_hora) VALUES (?, ?, ?, ?)",
                (cpf_adm, cpf_alvo, acao, data_hora)
            )
            log_id = cursor.lastrowid
            print(f"[BD DEBUG] inserir_log - Log ID {log_id} inserido com sucesso.")
            # Não faz commit aqui, o commit é feito pela função chamadora (deletar_pessoa, etc.)
            return log_id
            
        except sqlite3.Error as e:
            print(f"[BD ERROR] Erro SQLite ao inserir log (ADM:{cpf_adm}, Alvo:{cpf_alvo}, Ação:{acao}): {e}")
            # Não faz rollback aqui, a função chamadora fará
            raise # Re-raise a exceção

    def fechar_conexao(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Conexão com o banco de dados fechada.")

