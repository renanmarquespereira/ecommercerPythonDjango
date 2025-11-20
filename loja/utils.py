from django.db.models import Min, Max
from django.core.mail import send_mail
from django.http import HttpResponse
import csv

def filtar_produtos(produtos, filtro):
    # filtra a pagina por categorias
    if filtro:
        if "-" in filtro:
            categoria, tipo = filtro.split("-")
            produtos = produtos.filter(categoria__slug=categoria, tipo__slug=tipo)
        else:
            produtos = produtos.filter(categoria__slug=filtro)

    return produtos

def preco_min_max(produtos):
    minimo = 0
    maximo = 0
    if len(produtos) > 0:
        minimo = round(list(produtos.aggregate(Min('preco')).values())[0], 2)
        maximo = round(list(produtos.aggregate(Max('preco')).values())[0], 2)

    return minimo, maximo

def ordenar_produtos(produtos, ordem):
    if ordem == "menor_preco":
        return produtos.order_by("preco")
    elif ordem == "maior_preco":
        return produtos.order_by("-preco")
    elif ordem == "mais_vendidos":
        lista_produtos = []
        for produto in produtos:
            lista_produtos.append((produto.total_vendas_produtos(), produto))

        lista_produtos = sorted(lista_produtos, key=lambda x: x[0], reverse=True)
        produtos = [item[1] for item in lista_produtos]

        return produtos
    else:
        return produtos


def enviar_email(pedido):
    email = pedido.cliente.email
    assunto = f"Pedido aprovado: {pedido.id}"
    corpo = f"""Parabéns!!! Seu pedido foi aprovado.
    ID pedido: {pedido.id}
    Valor Total: {pedido.preco_total}
    """
    remetente = "renanmarques31@gmail.com"

    send_mail(assunto, corpo, remetente, [email])

def exportar_csv(dados):
    colunas = [campo.name for campo in dados.model._meta.fields]
    nome_tabela = dados.model._meta.db_table

    resposta = HttpResponse(content_type='text/csv')
    resposta["Content-Disposition"] = f"attachment; filename={nome_tabela}.csv"

    arquivo_csv = csv.writer(resposta, delimiter=';')
    arquivo_csv.writerow(colunas)

    for linha in dados.values_list():
        arquivo_csv.writerow(linha)

    return resposta