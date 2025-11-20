from .models import *


# Esse arquivo python nada masi é que definir contextos globais
def carrinho(request):
    quantidade_produtos_carrinho = 0

    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        id_sessao = request.COOKIES.get("id_sessao")
        if id_sessao:
            cliente = Cliente.objects.filter(id_sessao=id_sessao).first()
            if not cliente:
                return {"quantidade_produtos_carrinho": quantidade_produtos_carrinho}
        else:
            return {"quantidade_produtos_carrinho": quantidade_produtos_carrinho}

    # Apenas busca o pedido, sem criar
    pedido = Pedido.objects.filter(cliente=cliente, finalizado=False).first()
    if pedido:
        itens_pedido = ItensPedido.objects.filter(pedido=pedido)
        for item in itens_pedido:
            quantidade_produtos_carrinho += item.quantidade

    return {"quantidade_produtos_carrinho": quantidade_produtos_carrinho}


def categorias_tipos(request):
    categorias_nav = Categoria.objects.all()
    tipos_nav = Tipo.objects.all()
    return {"categorias_nav": categorias_nav, "tipos_nav": tipos_nav}

def faz_parte_equipe(request):
    equipe = False
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Equipe").exists():
            equipe = True

        return {"equipe": equipe}