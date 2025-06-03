import re

def input_nome(mensagem):
    while True:
        nome = input(mensagem).strip()

        if nome.replace(" ", "").isalpha():
            if 8 <= len(nome) <= 20:

                return nome
        print("Nome inválido. Use apenas letras e espaços.")


def input_texto(mensagem):
    while True:


        valor = str(input(mensagem).strip())

        if 8 <= len(valor) <= 20:

            return valor
        print("Entrada obrigatória. Tente novamente.")

def input_senha(mensagem):
    while True:

        valor = input(mensagem).strip()
        if 8 <= len(valor) <= 20:

            return valor
        print("Entrada obrigatória minimo 8 digitos. Tente novamente.")



def input_inteiro(mensagem):
    while True:
        try:
            valor = int(input(mensagem).strip())
            return valor
        except ValueError:
            print("Digite um número inteiro válido.")

def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)  # Remove caracteres não numéricos
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # Validação do primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if digito1 != int(cpf[9]):
        return False

    # Validação do segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    if digito2 != int(cpf[10]):
        return False

    return True

def input_cpf(mensagem):
    while True:
        cpf = input(mensagem).strip()
        if validar_cpf(cpf):
            return cpf
        print("CPF inválido. Tente novamente.")


def validar_email(email):
    padrao = r'^[\w\.-]+@[\w\.-]+\.\w{2,4}$'
    return re.match(padrao, email) is not None

def input_email(mensagem):
    while True:
        email = input(mensagem).strip()
        if validar_email(email):
            return email
        print("E-mail inválido. Tente novamente.")

def input_3dig(mensagem):
    while True:
        try:
            valor = int(input(mensagem).strip())
            if 1 <= valor <= 999:
                return valor
            else:
                print("O número deve ter exatamente 3 dígitos (entre 100 e 999).")
        except ValueError:
            print("Digite um número inteiro válido.")