#include <iostream>
#include <cstdlib>

using namespace std;
int main(){
    int escolha = 0;
    cout<<("Digite o numero da operacao que deseja fazer\n1 Cadastrar:\n2 Consultar\n3 Alterar\n4 Excluir\n0 Fechar Programa\n");
    cin>>(escolha);
    while (escolha != 0)
    {
        switch (escolha)
        {
            case 1:
                cout<<"Cadastrado";
                break;
            case 2:
                cout<<"Consultando";
                break;
            case 3:
                cout<<"Alterando";
                break;
            case 4:
                cout<<"Excluir";
            break;
        default:
            cout<<"Opcao invalida";
            break;
        };
        cout<<("\n1 Cadastrar:\n2 Consultar\n3 Alterar\n4 Excluir\n0 Fechar Programa\n");
        cin>>(escolha);
    };
    cout<<("Finalizado");
    return 0;
}