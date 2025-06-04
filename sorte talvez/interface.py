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

frame_principal = tk.Frame(root, bg="white")
frame_principal.pack(fill="both", expand=True)

def trocar_tela(conteudo_func):
    # Limpa tudo no frame_principal e chama a função desejada
    for widget in frame_principal.winfo_children():
        widget.destroy()
    conteudo_func(frame_principal)


# Variável global para armazenar o CPF do ADM logado (se houver)
# Usaremos isso para passar para as funções do adm.py
cpf_adm_logado_global = None

def mostrar_dados_usuario(dados):
    # A ordem vinda de fazer_login (após bd.validar_login) é: (cpf, nome, bloco, numero_ap, email)
    cpf, nome, bloco, numero_ap, email = dados

    # Limpa a tela
    for widget in root.winfo_children():
        widget.destroy()

    janela_dados = root
    janela_dados.title(f"Bem-vindo, {nome}")
    janela_dados.geometry("400x300")
    janela_dados.configure(bg="#f0f8ff")

    tk.Label(janela_dados, text="Informações do Usuário", font=("Helvetica", 14, "bold"), bg="#f0f8ff").pack(pady=10)

    info_frame = tk.Frame(janela_dados, bg="#f0f8ff")
    info_frame.pack(pady=10, padx=15, fill="x")

    for info_text in [
        f"Nome: {nome}",
        f"CPF: {cpf}",
        f"Bloco: {bloco if bloco is not None else 'N/A'}",
        f"Apartamento: {numero_ap if numero_ap is not None else 'N/A'}",
        f"Email: {email}"
    ]:
        tk.Label(info_frame, text=info_text, anchor="w", justify="left", bg="#f0f8ff").pack(fill="x", pady=2)

    # Botões para Editar ou Excluir
    action_frame = tk.Frame(janela_dados, bg="#f0f8ff")
    action_frame.pack(pady=15)
    tk.Button(action_frame, text="Editar Meus Dados", command=lambda u_cpf=cpf: editar_dados_usuario(u_cpf)).pack(side="left", padx=10)
    tk.Button(action_frame, text="Excluir Minha Conta", command=lambda u_cpf=cpf: excluir_conta(u_cpf), fg="red").pack(side="left", padx=10)
    
    # Botão de logout
    tk.Button(janela_dados, text="Logout", command=reiniciar_para_login).pack(pady=10)

def editar_dados_usuario(cpf):
    # Esta função é para o usuário editar seus próprios dados
    if not bd.conn:
        if not bd.conectar():
            messagebox.showerror("Erro", "Sem conexão com banco.")
            return
            
    cursor = bd.conn.cursor()
    try:
        cursor.execute("SELECT nome, email, bloco, numero_ap, login FROM Pessoa WHERE cpf = ?", (int(cpf),))
        dados = cursor.fetchone()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao buscar dados: {e}")
        return

    if not dados:
        messagebox.showerror("Erro", "Usuário não encontrado.")
        reiniciar_para_login()
        return

    nome_atual, email_atual, bloco_atual, numero_ap_atual, login_atual = dados

    editar_window = tk.Toplevel(root)
    editar_window.title("Editar Meus Dados")
    editar_window.geometry("350x450")
    editar_window.transient(root)
    editar_window.grab_set()

    tk.Label(editar_window, text="Nome*").pack()
    entry_nome_edit = tk.Entry(editar_window); entry_nome_edit.insert(0, nome_atual); entry_nome_edit.pack()
    tk.Label(editar_window, text="Email*").pack()
    entry_email_edit = tk.Entry(editar_window); entry_email_edit.insert(0, email_atual); entry_email_edit.pack()
    tk.Label(editar_window, text="Bloco").pack()
    entry_bloco_edit = tk.Entry(editar_window); entry_bloco_edit.insert(0, str(bloco_atual) if bloco_atual is not None else ""); entry_bloco_edit.pack()
    tk.Label(editar_window, text="Número do AP").pack()
    entry_numero_ap_edit = tk.Entry(editar_window); entry_numero_ap_edit.insert(0, str(numero_ap_atual) if numero_ap_atual is not None else ""); entry_numero_ap_edit.pack()
    tk.Label(editar_window, text="Nova Senha (deixe em branco para não alterar)").pack()
    entry_senha_edit = tk.Entry(editar_window, show="*"); entry_senha_edit.pack()
    tk.Label(editar_window, text="Confirmar Nova Senha").pack()
    entry_confirma_senha_edit = tk.Entry(editar_window, show="*"); entry_confirma_senha_edit.pack()
    tk.Label(editar_window, text="* Campos obrigatórios").pack(pady=5)

    def salvar_edicao():
        novo_nome = entry_nome_edit.get()
        novo_email = entry_email_edit.get()
        novo_bloco_str = entry_bloco_edit.get()
        novo_numero_ap_str = entry_numero_ap_edit.get()
        nova_senha = entry_senha_edit.get()
        confirma_senha = entry_confirma_senha_edit.get()

        if not novo_nome or not novo_email:
            messagebox.showwarning("Campos Obrigatórios", "Nome e Email são obrigatórios.", parent=editar_window)
            return
        if nova_senha != "" and nova_senha != confirma_senha:
            messagebox.showerror("Erro", "As novas senhas não coincidem.", parent=editar_window)
            return
        try:
            novo_bloco = int(novo_bloco_str) if novo_bloco_str else None
            novo_numero_ap = int(novo_numero_ap_str) if novo_numero_ap_str else None
        except ValueError:
            messagebox.showerror("Erro de Formato", "Bloco e AP devem ser números.", parent=editar_window)
            return
        try:
            # Chama bd.atualizar_pessoa com cpf_adm=None
            success = bd.atualizar_pessoa(cpf=int(cpf), cpf_adm=None, 
                                        novo_nome=novo_nome, novo_email=novo_email, 
                                        novo_bloco=novo_bloco, novo_numero_ap=novo_numero_ap, 
                                        novo_senha=nova_senha if nova_senha else None)
            if success:
                messagebox.showinfo("Sucesso", "Dados atualizados com sucesso!", parent=editar_window)
                editar_window.destroy()
                # Atualiza a tela principal
                mostrar_dados_usuario((int(cpf), novo_nome, novo_bloco, novo_numero_ap, novo_email))
            else:
                messagebox.showerror("Erro", "Falha ao atualizar dados.", parent=editar_window)
        except ValueError as ve:
             messagebox.showerror("Erro de Validação", str(ve), parent=editar_window)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao atualizar: {e}", parent=editar_window)

    tk.Button(editar_window, text="Salvar Alterações", command=salvar_edicao).pack(pady=10)

def excluir_conta(cpf):
    # Esta função é para o usuário excluir sua própria conta
    resposta = messagebox.askyesno("Excluir Conta", "ATENÇÃO!\nTem certeza que deseja excluir sua conta?\nEsta ação é irreversível.", icon='warning')
    if resposta:
        if not bd.conn:
            if not bd.conectar():
                messagebox.showerror("Erro", "Sem conexão com banco.")
                return
        try:
            # Chama bd.deletar_pessoa com cpf_adm=None
            success = bd.deletar_pessoa(cpf=int(cpf), cpf_adm=None)
            if success:
                messagebox.showinfo("Sucesso", "Conta excluída com sucesso!")
                reiniciar_para_login()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir a conta.")
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao excluir conta: {e}")

def fazer_login():
    global root,cpf_adm_logado_global # Referencia a variável global
    login = entry_login.get()
    senha = entry_senha.get()
    cpf_adm_logado_global = None # Reseta em cada tentativa de login

    if not bd.conn:
        if not bd.conectar():
             messagebox.showerror("Erro", "Falha ao conectar ao banco de dados.")
             return

    # Usar a função centralizada de validação do bd.py
    resultado_login = bd.validar_login(login, senha)

    if resultado_login:
        tipo_usuario = resultado_login[0]
        if tipo_usuario == "adm":


            # Ordem retornada: ("adm", cpf, nome)
            cpf_adm = resultado_login[1]
            nome_adm = resultado_login[2]
            cpf_adm_logado_global = cpf_adm # Armazena o CPF do ADM logado
            messagebox.showinfo("Sucesso", f"Login de administrador bem-sucedido! Bem-vindo, {nome_adm}")
            try:
                # Importa a função do módulo adm

                
                from adm import mostrar_usuarios
                # *** CORREÇÃO APLICADA AQUI: Passa o CPF do ADM logado ***

                mostrar_usuarios(root, cpf_adm_logado_global)


            except ImportError as imp_err:
                 messagebox.showerror("Erro", f"Não foi possível carregar o painel de administração: {imp_err}")
                 reiniciar_para_login()
            except Exception as adm_err:
                 messagebox.showerror("Erro", f"Erro ao iniciar painel ADM: {adm_err}")
                 reiniciar_para_login()

        elif tipo_usuario == "pessoa":
            # Ordem retornada: ("pessoa", cpf, nome, bloco, numero_ap, email)
            dados_pessoa_completo = resultado_login[1:]
            messagebox.showinfo("Sucesso", "Login de usuário bem-sucedido!")
            mostrar_dados_usuario(dados_pessoa_completo)
        else:
             messagebox.showerror("Erro", "Tipo de usuário desconhecido retornado pelo login.")
    else:
        messagebox.showerror("Erro", "Login ou senha inválidos.")

def abrir_cadastro():
    cadastro_window = tk.Toplevel(root)
    cadastro_window.title("Cadastro de Usuário")
    cadastro_window.geometry("350x450")
    cadastro_window.transient(root)
    cadastro_window.grab_set()

    def cadastrar_pessoa():
        try:
            cpf_str = entry_cpf.get()
            login = entry_login_cad.get()
            nome = entry_nome.get()
            senha = entry_senha_cad.get()
            bloco_str = entry_bloco.get()
            numero_ap_str = entry_numero_ap.get()
            email = entry_email.get()

            if not all([cpf_str, login, nome, senha, email]):
                messagebox.showwarning("Campos Obrigatórios", "CPF, Login, Nome, Senha e Email são obrigatórios.", parent=cadastro_window)
                return
            try:
                cpf = int(cpf_str)
                bloco = int(bloco_str) if bloco_str else None
                numero_ap = int(numero_ap_str) if numero_ap_str else None
            except ValueError:
                 messagebox.showerror("Erro de Formato", "CPF, Bloco e AP devem ser números.", parent=cadastro_window)
                 return

            pessoa = Cadastro(
                cpf=cpf, login=login, nome=nome, senha=senha, 
                bloco=bloco, numero_ap=numero_ap, email=email,
                data_cadastro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            # Chama inserir_pessoa com cpf_adm=None para auto-cadastro
            success = bd.inserir_pessoa(pessoa, cpf_adm=None)
            if success:
                messagebox.showinfo("Sucesso", "Cadastro realizado! Faça login.", parent=cadastro_window)
                cadastro_window.destroy()
            # else: Erro já tratado/lançado por inserir_pessoa
        except ValueError as ve:
             messagebox.showerror("Erro de Validação", str(ve), parent=cadastro_window)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Erro ao cadastrar: {e}", parent=cadastro_window)

    tk.Label(cadastro_window, text="CPF*").pack(); entry_cpf = tk.Entry(cadastro_window); entry_cpf.pack()
    tk.Label(cadastro_window, text="Login*").pack(); entry_login_cad = tk.Entry(cadastro_window); entry_login_cad.pack()
    tk.Label(cadastro_window, text="Nome*").pack(); entry_nome = tk.Entry(cadastro_window); entry_nome.pack()
    tk.Label(cadastro_window, text="Senha*").pack(); entry_senha_cad = tk.Entry(cadastro_window, show="*"); entry_senha_cad.pack()
    tk.Label(cadastro_window, text="Bloco").pack(); entry_bloco = tk.Entry(cadastro_window); entry_bloco.pack()
    tk.Label(cadastro_window, text="Número do AP").pack(); entry_numero_ap = tk.Entry(cadastro_window); entry_numero_ap.pack()
    tk.Label(cadastro_window, text="Email*").pack(); entry_email = tk.Entry(cadastro_window); entry_email.pack()
    tk.Label(cadastro_window, text="* Campos obrigatórios").pack(pady=5)
    tk.Button(cadastro_window, text="Cadastrar", command=cadastrar_pessoa).pack(pady=10)

def mostrar_tela_login():
    # Limpa a tela atual
    for widget in root.winfo_children():
        widget.destroy()

    root.title("Sistema de Login")
    root.configure(bg="gray")
    root.geometry("300x300")

    # Recria os widgets da tela de login
    global entry_login, entry_senha # Tornar acessível globalmente para a função fazer_login
    tk.Label(root, text="Login", bg="gray").pack()
    entry_login = tk.Entry(root)
    entry_login.pack()

    tk.Label(root, text="Senha", bg="gray").pack()
    entry_senha = tk.Entry(root, show="*")
    entry_senha.pack()

    tk.Button(root, text="Entrar", command=fazer_login).pack(pady=10)
    tk.Button(root, text="Cadastrar", command=abrir_cadastro).pack()

def reiniciar_para_login():
    global cpf_adm_logado_global
    cpf_adm_logado_global = None # Limpa o CPF do ADM ao fazer logout
    # Não precisamos limpar usuario_logado_dados aqui, pois a tela será reconstruída
    mostrar_tela_login()

# Inicia mostrando a tela de login
mostrar_tela_login()

root.mainloop()

# Fecha a conexão com o banco ao sair
if bd.conn:
    bd.fechar_conexao()

