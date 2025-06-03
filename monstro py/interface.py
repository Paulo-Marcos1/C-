import tkinter as tk
from tkinter import messagebox
from bd import BancoDeDados
from cadastro import Cadastro
from datetime import datetime

# Iniciar banco de dados
bd = BancoDeDados()
bd.conectar()
bd.criar_tabelas()

# Janela principal
root = tk.Tk()
root.title("Sistema de Login")
root.configure(bg="gray")
root.geometry("300x300")


def mostrar_dados_usuario(dados):
    nome, cpf, bloco, numero_ap, email = dados

    # Limpa a tela
    for widget in root.winfo_children():
        widget.destroy()

    janela_dados = root  # Usando a janela principal como "página"
    janela_dados.title("Dados do Usuário")
    janela_dados.geometry("400x300")
    janela_dados.configure(bg="#f0f8ff")

    tk.Label(janela_dados, text="Informações do Usuário", font=("Helvetica", 14, "bold"), bg="#f0f8ff").pack(pady=10)

    for info in [
        f"Nome: {nome}",
        f"CPF: {cpf}",
        f"Bloco: {bloco}",
        f"Apartamento: {numero_ap}",
        f"Email: {email}"
    ]:
        tk.Label(janela_dados, text=info, anchor="w", justify="left", bg="#f0f8ff").pack(fill="x", padx=15, pady=4)

    # Botões para Editar ou Excluir
    tk.Button(janela_dados, text="Editar", command=lambda: editar_dados_usuario(cpf)).pack(pady=5)
    tk.Button(janela_dados, text="Excluir Conta", command=lambda: excluir_conta(cpf)).pack(pady=5)


def editar_dados_usuario(cpf):
    cursor = bd.conn.cursor()
    cursor.execute("SELECT * FROM Pessoa WHERE cpf = ?", (cpf,))
    dados = cursor.fetchone()

    if not dados:
        messagebox.showerror("Erro", "Usuário não encontrado.")
        return

    cpf, nome, login, senha, bloco, numero_ap, email, data_cadastro = dados

    # Criação de nova janela para editar os dados
    editar_window = tk.Toplevel(root)
    editar_window.title("Editar Dados")
    editar_window.geometry("350x400")

    tk.Label(editar_window, text="Nome").pack()
    entry_nome_edit = tk.Entry(editar_window)
    entry_nome_edit.insert(0, nome)
    entry_nome_edit.pack()

    tk.Label(editar_window, text="Email").pack()
    entry_email_edit = tk.Entry(editar_window)
    entry_email_edit.insert(0, email)
    entry_email_edit.pack()

    tk.Label(editar_window, text="Bloco").pack()
    entry_bloco_edit = tk.Entry(editar_window)
    entry_bloco_edit.insert(0, str(bloco))
    entry_bloco_edit.pack()

    tk.Label(editar_window, text="Número do AP").pack()
    entry_numero_ap_edit = tk.Entry(editar_window)
    entry_numero_ap_edit.insert(0, str(numero_ap))
    entry_numero_ap_edit.pack()

    # Campos de senha
    tk.Label(editar_window, text="Nova Senha (deixe em branco para não alterar)").pack()
    entry_senha_edit = tk.Entry(editar_window, show="*")
    entry_senha_edit.pack()

    tk.Label(editar_window, text="Confirmar Nova Senha").pack()
    entry_confirma_senha_edit = tk.Entry(editar_window, show="*")
    entry_confirma_senha_edit.pack()

    def salvar_edicao():
        novo_nome = entry_nome_edit.get()
        novo_email = entry_email_edit.get()
        novo_bloco = int(entry_bloco_edit.get())
        novo_numero_ap = int(entry_numero_ap_edit.get())
        nova_senha = entry_senha_edit.get()
        confirma_senha = entry_confirma_senha_edit.get()

        if nova_senha != "" and nova_senha != confirma_senha:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return

        # Atualiza no banco de dados
        if nova_senha != "":
            # Se a senha foi alterada, atualiza no banco
            cursor.execute("""
                UPDATE Pessoa SET nome = ?, email = ?, bloco = ?, numero_ap = ?, senha = ? WHERE cpf = ?
            """, (novo_nome, novo_email, novo_bloco, novo_numero_ap, nova_senha, cpf))
        else:
            # Caso a senha não tenha sido alterada, apenas atualiza os outros dados
            cursor.execute("""
                UPDATE Pessoa SET nome = ?, email = ?, bloco = ?, numero_ap = ? WHERE cpf = ?
            """, (novo_nome, novo_email, novo_bloco, novo_numero_ap, cpf))

        bd.conn.commit()

        messagebox.showinfo("Sucesso", "Dados atualizados com sucesso!")
        editar_window.destroy()
        mostrar_dados_usuario((novo_nome, cpf, novo_bloco, novo_numero_ap, novo_email))

    tk.Button(editar_window, text="Salvar", command=salvar_edicao).pack(pady=10)


def excluir_conta(cpf):
    resposta = messagebox.askyesno("Excluir Conta", "Você tem certeza que deseja excluir sua conta?")
    if resposta:
        cursor = bd.conn.cursor()
        cursor.execute("DELETE FROM Pessoa WHERE cpf = ?", (cpf,))
        bd.conn.commit()
        messagebox.showinfo("Sucesso", "Conta excluída com sucesso!")
        # Redireciona para a tela de login após exclusão
        root.quit()


def fazer_login():
    login = entry_login.get()
    senha = entry_senha.get()
    if bd.conn:
        cursor = bd.conn.cursor()

        # Verifica login como ADM
        cursor.execute("SELECT nome, cpf FROM Adm WHERE login = ? AND senha = ?", (login, senha))
        dados = cursor.fetchone()
        if dados:
            messagebox.showinfo("Sucesso", "Login de administrador bem-sucedido!")
            from adm import mostrar_usuarios
            mostrar_usuarios(root)
            return

        # Verifica login como usuário
        cursor.execute("SELECT nome, cpf, bloco, numero_ap, email FROM Pessoa WHERE login = ? AND senha = ?",
                       (login, senha))
        dados = cursor.fetchone()
        if dados:
            messagebox.showinfo("Sucesso", "Login de usuário bem-sucedido!")
            mostrar_dados_usuario(dados)

            return

        messagebox.showerror("Erro", "Login ou senha inválidos.")


def abrir_cadastro():
    cadastro_window = tk.Toplevel(root)
    cadastro_window.title("Cadastro")
    cadastro_window.geometry("350x400")

    def cadastrar_pessoa():
        try:
            pessoa = Cadastro(
                cpf=entry_cpf.get(),
                login=entry_login_cad.get(),
                nome=entry_nome.get(),
                senha=entry_senha_cad.get(),
                bloco=int(entry_bloco.get()),
                numero_ap=int(entry_numero_ap.get()),
                email=entry_email.get(),
                data_cadastro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            bd.inserir_pessoa(pessoa)
            messagebox.showinfo("Sucesso", "Cadastro realizado com sucesso!")
            cadastro_window.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar: {e}")

    # Campos de cadastro
    tk.Label(cadastro_window, text="CPF").pack()
    entry_cpf = tk.Entry(cadastro_window)
    entry_cpf.pack()

    tk.Label(cadastro_window, text="Login").pack()
    entry_login_cad = tk.Entry(cadastro_window)
    entry_login_cad.pack()

    tk.Label(cadastro_window, text="Nome").pack()
    entry_nome = tk.Entry(cadastro_window)
    entry_nome.pack()

    tk.Label(cadastro_window, text="Senha").pack()
    entry_senha_cad = tk.Entry(cadastro_window, show="*")
    entry_senha_cad.pack()

    tk.Label(cadastro_window, text="Bloco").pack()
    entry_bloco = tk.Entry(cadastro_window)
    entry_bloco.pack()

    tk.Label(cadastro_window, text="Número do AP").pack()
    entry_numero_ap = tk.Entry(cadastro_window)
    entry_numero_ap.pack()

    tk.Label(cadastro_window, text="Email").pack()
    entry_email = tk.Entry(cadastro_window)
    entry_email.pack()

    tk.Button(cadastro_window, text="Cadastrar", command=cadastrar_pessoa).pack(pady=10)


# Tela de login
tk.Label(root, text="Login", bg="gray").pack()
entry_login = tk.Entry(root)
entry_login.pack()

tk.Label(root, text="Senha", bg="gray").pack()
entry_senha = tk.Entry(root, show="*")
entry_senha.pack()

tk.Button(root, text="Entrar", command=fazer_login).pack(pady=10)
tk.Button(root, text="Cadastrar", command=abrir_cadastro).pack()

root.mainloop()