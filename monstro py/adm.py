import tkinter as tk
from tkinter import messagebox
from bd import BancoDeDados
from cadastro import Cadastro_adm, Cadastro
from datetime import datetime
import os
import platform
import subprocess


# Iniciar banco de dados
bd = BancoDeDados()
bd.conectar()
bd.criar_tabelas()


# Janela principal
def mostrar_usuarios(root):
    if bd.conn:
        try:
            cursor = bd.conn.cursor()
            cursor.execute("SELECT nome, cpf, bloco, numero_ap, email, data_cadastro FROM Pessoa")
            usuarios = cursor.fetchall()

            for widget in root.winfo_children():
                widget.destroy()

            janela_usuarios = root
            janela_usuarios.title("Usuários Cadastrados")
            janela_usuarios.geometry("600x500")

            tk.Label(janela_usuarios, text="Lista de Usuários", font=("Helvetica", 14, "bold")).pack(pady=10)

            for usuario in usuarios:
                nome, cpf, bloco, numero_ap, email, data_cadastro = usuario
                frame = tk.Frame(janela_usuarios)
                frame.pack(fill="x", padx=10, pady=2)

                info = f"{nome} | CPF: {cpf} | Bloco: {bloco} | Ap: {numero_ap} | Email: {email}"
                tk.Label(frame, text=info, anchor="w").pack(side="left")

                tk.Button(frame, text="Editar", command=lambda c=cpf: editar_usuario(root, c)).pack(side="right")
                tk.Button(frame, text="Excluir", command=lambda c=cpf: excluir_usuario(root, c)).pack(side="right")

            tk.Button(janela_usuarios, text="Cadastrar novo ADM", command=lambda: abrir_cadastro_adm(root)).pack(
                pady=15)
            tk.Button(janela_usuarios, text="Cadastrar novo usuario", command=lambda: abrir_cadastro(root)).pack(
                pady=15)
            tk.Button(janela_usuarios, text="Mostrar Logs", command=exportar_logs_para_txt).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar usuários: {e}")

def exportar_logs_para_txt():
    try:
        cursor = bd.conn.cursor()
        cursor.execute("SELECT id, cpf_adm, cpf_alvo, acao, data_hora FROM Log ORDER BY data_hora DESC")
        logs = cursor.fetchall()

        if not logs:
            messagebox.showinfo("Logs", "Nenhum log encontrado.")
            return

        nome_arquivo = "log.txt"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("---- LOGS DE EVENTOS ----\n\n")
            for log in logs:
                id, cpf_adm, cpf_alvo, acao, data_hora = log
                f.write(f"[{data_hora}] (ID: {id}) - {acao}\nADM CPF: {cpf_adm} | Alvo CPF: {cpf_alvo}\n\n")

        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(nome_arquivo)
        elif sistema == "Darwin":
            subprocess.call(["open", nome_arquivo])
        else:
            subprocess.call(["xdg-open", nome_arquivo])

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exportar logs: {e}")





def editar_usuario(root, cpf):
    if bd.conn:
        cursor = bd.conn.cursor()
        cursor.execute("SELECT nome, email, bloco, senha, numero_ap, login FROM Pessoa WHERE cpf = ?", (cpf,))
        usuario = cursor.fetchone()

        if not usuario:
            messagebox.showerror("Erro", "Usuário não encontrado.")
            return

        nome_atual, email_atual, bloco_atual, senha_atual, numero_ap_atual, login_atual = usuario

        janela_editar = tk.Toplevel()
        janela_editar.title("Editar Usuário")
        janela_editar.geometry("400x600")

        tk.Label(janela_editar, text="Novo Nome").pack()
        entry_nome = tk.Entry(janela_editar)
        entry_nome.insert(0, nome_atual)
        entry_nome.pack()

        tk.Label(janela_editar, text="Novo Email").pack()
        entry_email = tk.Entry(janela_editar)
        entry_email.insert(0, email_atual)
        entry_email.pack()

        tk.Label(janela_editar, text="Novo bloco").pack()
        entry_bloco = tk.Entry(janela_editar)
        entry_bloco.insert(0, bloco_atual)
        entry_bloco.pack()

        tk.Label(janela_editar, text="Nova Senha").pack()
        entry_senha = tk.Entry(janela_editar)
        entry_senha.insert(0, senha_atual)
        entry_senha.pack()

        tk.Label(janela_editar, text="Novo apartamento").pack()
        entry_numero_ap = tk.Entry(janela_editar)
        entry_numero_ap.insert(0, numero_ap_atual)
        entry_numero_ap.pack()

        tk.Label(janela_editar, text="Novo Login").pack()
        entry_login = tk.Entry(janela_editar)
        entry_login.insert(0, login_atual)
        entry_login.pack()

        def salvar():
            resposta = messagebox.askyesno("Confirmar", "Tem certeza que deseja salvar as mudanças?")
            if resposta:
                novo_nome = entry_nome.get()
                novo_email = entry_email.get()
                novo_bloco = entry_bloco.get()
                novo_senha = entry_senha.get()
                novo_numero_ap = entry_numero_ap.get()
                novo_login = entry_login.get()

                bd.atualizar_pessoa(cpf, novo_nome=novo_nome, novo_email=novo_email, novo_bloco=novo_bloco,
                                    novo_senha=novo_senha, novo_numero_ap=novo_numero_ap, novo_login=novo_login,)
                messagebox.showinfo("Sucesso", "Dados atualizados com sucesso!")
                janela_editar.destroy()
                mostrar_usuarios(root)

        tk.Button(janela_editar, text="Salvar", command=salvar).pack(pady=10)


def excluir_usuario(root, cpf):
    resposta = messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este usuário?")
    if resposta:
        bd.deletar_pessoa(cpf)
        messagebox.showinfo("Removido", "Usuário excluído com sucesso!")
        mostrar_usuarios(root)


def abrir_cadastro(root):
    cadastro_window = tk.Toplevel()
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
            mostrar_usuarios(root)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar: {e}")

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


def abrir_cadastro_adm(root):
    cadastro_window = tk.Toplevel()
    cadastro_window.title("Cadastro de ADM")
    cadastro_window.geometry("350x400")

    def cadastrar():
        try:
            pessoa = Cadastro_adm(
                cpf=entry_cpf.get(),
                login=entry_login_cad.get(),
                nome=entry_nome.get(),
                senha=entry_senha_cad.get(),
                data_cadastro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            bd.inserir_adm(pessoa)
            messagebox.showinfo("Sucesso", "Administrador cadastrado com sucesso!")
            cadastro_window.destroy()
            mostrar_usuarios(root)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar: {e}")

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

    tk.Button(cadastro_window, text="Cadastrar", command=cadastrar).pack(pady=10)