from django.shortcuts import render, redirect
from .models import *
import uuid
from .utils import filtar_produtos, preco_min_max, ordenar_produtos
from django.contrib.auth import authenticate, login, logout
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .api_mercadopago import criar_pagamento
from django.urls import reverse

def homepage(request):
    banners = Banner.objects.filter(ativo=True)
    context = {"banners": banners}
    return render(request,'homepage.html', context)

def loja(request, filtro=None):
    produtos = Produto.objects.filter(ativo=True)

    produtos = filtar_produtos(produtos, filtro)

    if request.method == "POST":
        dados = request.POST.dict()
        produtos = produtos.filter(preco__gte=dados['precominimo'], preco__lte=dados['precomaximo'])
        if "tamanho" in dados:
            itens = ItemEstoque.objects.filter(produto__in=produtos, tamanho=dados["tamanho"])
            id_produtos = itens.values_list("produto", flat=True).distinct()
            produtos = produtos.filter(id__in=id_produtos)

        if "categoria" in dados:
            produtos = produtos.filter(categoria__slug=dados["categoria"])

        if "tipo" in dados:
            produtos = produtos.filter(tipo__slug=dados["tipo"])


    #esse in serve para passar lista como parametro
    itens_estoque = ItemEstoque.objects.filter(produto__in=produtos, quantidade__gt=0)
    tamanhos = itens_estoque.values_list("tamanho", flat=True).distinct()

    id_categoria = produtos.values_list("categoria", flat=True).distinct()
    categoria = Categoria.objects.filter(id__in=id_categoria)

    minimo, maximo = preco_min_max(produtos)

    ordem = request.GET.get("ordem", "menor-preco")
    produtos = ordenar_produtos(produtos, ordem)

    context = {"produtos": produtos, "minimo": minimo, "maximo": maximo, "tamanhos": tamanhos, "categorias": categoria}
    return render(request,'loja/loja.html', context)

def ver_produto(request, id_produto, id_cor=None):
    tem_estoque = False
    cores = {}
    tamanhos = {}
    cor = None

    produto = Produto.objects.get(id=id_produto)
    itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0)

    if len(itens_estoque) > 0:
        tem_estoque = True
        cores = {item.cor for item in itens_estoque}

        if id_cor:
            itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0, cor__id=id_cor)
            tamanhos = {item.tamanho for item in itens_estoque}
            cor = Cor.objects.get(id=id_cor)

    context = {"produto": produto, "itens_estoque": itens_estoque, "tem_estoque": tem_estoque, "cores": cores, "tamanhos":tamanhos, "cor": cor}
    return render(request,'loja/ver_produtos.html', context)

def carrinho(request):
    cliente = None

    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        id_sessao = request.COOKIES.get("id_sessao")
        if id_sessao:
            cliente = Cliente.objects.filter(id_sessao=id_sessao).first()
            if not cliente:
                context = {"cliente_existente": False, "itens_pedido": None, "pedido": None}
                return render(request, 'loja/carrinho.html', context)
        else:
            context = {"cliente_existente": False, "itens_pedido": None, "pedido": None}
            return render(request, 'loja/carrinho.html', context)

    # Apenas busca o pedido, sem criar
    pedido = Pedido.objects.filter(cliente=cliente, finalizado=False).first()
    if pedido:
        itens_pedido = ItensPedido.objects.filter(pedido=pedido)
        cliente_existente = True
    else:
        itens_pedido = None
        cliente_existente = False

    context = {
        "itens_pedido": itens_pedido,
        "pedido": pedido,
        "cliente_existente": cliente_existente
    }

    return render(request, 'loja/carrinho.html', context)



def adicionar_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:
        dados = request.POST.dict()
        tamanho = dados.get('tamanho')
        id_cor = dados.get('cor')

        if not tamanho:
            return redirect('loja')

        if request.user.is_authenticated:
            cliente = request.user.cliente
            resposta = redirect('carrinho')
        else:
            if request.COOKIES.get('id_sessao'):
                id_sessao = request.COOKIES.get('id_sessao')
            else:
                id_sessao = str(uuid.uuid4())

            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            resposta = redirect('carrinho')

            # Agora garantimos que o cookie será salvo na resposta final
            if not request.COOKIES.get('id_sessao'):
                resposta.set_cookie(key='id_sessao', value=id_sessao, max_age=60*60*24*30)

        pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)

        item_pedido, criar_item = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
        item_pedido.quantidade += 1
        item_pedido.save()

        return resposta
    else:
        return redirect('loja')


def excluir_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:
        dados = request.POST.dict()
        tamanho = dados.get('tamanho')
        id_cor = dados.get('cor')

        if not dados.get('tamanho'):
            return redirect('loja')

        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            else:
                return redirect('loja')

        pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
        item_estoque = ItemEstoque.objects.get(produto__id=id_produto, tamanho=tamanho, cor__id=id_cor)

        item_pedido, criar_item = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)

        item_pedido.quantidade -= 1
        item_pedido.save()

        if item_pedido.quantidade <= 0:
            item_pedido.delete()
            if not ItensPedido.objects.filter(pedido=pedido):
                pedido.delete()

        return redirect('carrinho')
    else:
        return redirect('loja')

def checkout(request):
    cliente = None

    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente = Cliente.objects.get(id_sessao=id_sessao)
        else:
            return redirect('loja')

    # Apenas busca o pedido, sem criar
    pedido = Pedido.objects.filter(cliente=cliente, finalizado=False).first()
    if pedido:
        enderecos = Endereco.objects.filter(cliente=cliente)
    else:
        pedido = None
        enderecos = None

    context = {
        "pedido": pedido,
        "enderecos": enderecos,
        "erro": None
    }

    return render(request, 'loja/checkout.html', context)

def finalizar_pedido(request, id_pedido):
    if request.method == "POST":
        dados = request.POST.dict()
        erro = None
        total_compra = dados.get('total')
        total_compra = float(total_compra.replace(',', '.'))
        pedido = Pedido.objects.get(id=id_pedido)

        if total_compra != float(pedido.preco_total):
            erro = "Valores não conferem"

        if not "endereco" in dados:
            erro = "Informe um endereço"
        else:
            id_endereco = dados.get("endereco")
            endereco = Endereco.objects.get(id=id_endereco)
            pedido.endereco = endereco

        if not request.user.is_authenticated:
            try:
                validate_email(dados.get("email"))
            except ValidationError:
                erro = "Informe um email"

            if not erro:
                clientes = Cliente.objects.filter(email=dados.get("email"))
                if clientes:
                    pedido.cliente = clientes[0]
                else:
                    pedido.cliente.email = dados.get("email")
                    pedido.cliente.save()

        codigo_transacao = f"{pedido.id}-{datetime.now().timestamp()}"
        pedido.codigo_transacao = codigo_transacao
        pedido.save()

        if erro:
            enderecos = Endereco.objects.filter(cliente=pedido.cliente)
            context = {"erro": erro, "pedido": pedido, "enderecos": enderecos}
            return render(request,'loja/checkout.html', context)
        else:
            itens_pedido = ItensPedido.objects.filter(pedido=pedido)

            #Aqui foi utilizado essa funcao para mandar para o mercado livre nossa view em formato de url
            link = request.build_absolute_uri(reverse("finalizar_pagamento"))
            link = link.replace("http://", "https://")
            link_pagamento, id_pagamento = criar_pagamento(itens_pedido, link)
            pagamento = Pagamento.objects.create(id_pagamento=id_pagamento, pedido=pedido)
            pagamento.save()
            return redirect(link_pagamento)

    else:
        return redirect('loja')

def finalizar_pagamento(request):
    dados = request.GET.dict()
    status = dados.get("collection_status")
    id_pagamento = dados.get("preference_id")

    if status == "approved":
        pagamento = Pagamento.objects.get(id_pagamento=id_pagamento)
        pagamento.status = True
        pedido = pagamento.pedido
        pedido.finalizado = True
        pedido.data_finalizacao = datetime.now()

        pedido.save()
        pagamento.save()

        if request.user.is_authenticated:
            return redirect('meus_pedidos')
        else:
            return redirect('pedido_aprovado', pedido.id)
    else:
        redirect("checkout")


def pedido_aprovado(request, id_pedido):
    pedido = Pedido.objects.get(id=id_pedido)
    context = {"pedido": pedido}
    return render(request, 'loja/pedido_aprovado.html', context)

# //// USUÁRIO
def adicionar_endereco(request):
    if request.method == "POST":
        cliente = None

        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                cliente = Cliente.objects.get(id_sessao=id_sessao)
            else:
                return redirect('loja')

        dados = request.POST.dict()
        endereco = Endereco.objects.create(
            cliente=cliente,
            rua=dados.get('rua'),
            numero=dados.get('numero'),
            complemento=dados.get('complemento'),
            cep=dados.get('cep'),
            bairro=dados.get('bairro'),
            cidade=dados.get('cidade'),
            estado=dados.get('estado'),
        )

        endereco.save()
        return redirect('checkout')

    else:
        context = {}
        return render(request, 'loja/adicionar_endereco.html', context)

@login_required
def minha_conta(request):
    cliente = request.user.cliente
    erro = None

    if request.method == "POST":
        dados = request.POST.dict()

        if "btnSalvarDados" in dados:
            email = dados.get('email')
            telefone = dados.get('telefone')
            nome = dados.get('nome')

            if email != request.user.email:
                usuarios = User.objects.filter(email=email)
                if len(usuarios) > 0:
                    erro = "Email já existe, tente outro..."

            if not erro:
                cliente = request.user.cliente
                cliente.email = email
                request.user.email = email
                request.user.username = email
                cliente.nome = nome
                cliente.telefone = telefone
                cliente.save()
                request.user.save()
                erro = "Dados alterados"

        elif "btnEditarSenha" in dados:
            senhaAtual = dados.get('senhaAtual')
            senhaNova = dados.get('senhaNova')
            senhaNovaRepitida = dados.get('senhaNovaRepitida')

            if senhaNovaRepitida == senhaNova:
                usuario = authenticate(request, username=request.user.email, password=senhaAtual)
                if usuario:
                    usuario.set_password(senhaNova)
                    usuario.save()
                    erro = "Senha Alterada"
                else:
                    erro = "Senha Atual Invalida"
            else:
                erro = "Senhas não conferem"

    context = {"erro": erro}
    return render(request,'usuario/minha_conta.html', context)

@login_required
def meus_pedidos(request):
    pedidos = Pedido.objects.filter(cliente=request.user.cliente, finalizado=True)
    context = {"pedidos": pedidos.order_by('-data_finalizacao')}
    return render(request,'usuario/meus_pedidos.html', context)

def fazer_login(request):
    erro = False
    if request.user.is_authenticated:
        return redirect('loja')
    else:
        if request.method == "POST":
            dados = request.POST.dict()
            if "email" in dados  and "senha" in dados:
                usuario = authenticate(request, username=dados.get('email'), password=dados.get('senha'))
                if usuario:
                    login(request, usuario)
                    return redirect('loja')
                else:
                    erro = True
            else:
                erro = True

        context = {'erro': erro}
        return render(request, 'usuario/login.html', context)




def criar_conta(request):
    erro = None
    if request.user.is_authenticated:
        return redirect('loja')
    else:
        if request.method == "POST":
            dados = request.POST.dict()
            if "email" in dados and "senha" in dados and "confirmarSenha" in dados:
                email = dados.get('email')
                senha = dados.get('senha')
                confirmacao_senha = dados.get('confirmarSenha')

                try:
                    validate_email(email)
                except ValidationError:
                    erro = "Email invalido"

                if senha == confirmacao_senha:
                    usuario, criado = User.objects.get_or_create(username=email, email=email)
                    if not criado:
                        erro = "Usuario ja existe"
                    else:
                        usuario.set_password(senha)
                        usuario.save()

                        usuario = authenticate(request, username=email, password=senha)
                        login(request, usuario)

                        if request.COOKIES.get("id_sessao"):
                            id_sessao = request.COOKIES.get("id_sessao")
                            cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
                        else:
                            cliente, criado = Cliente.objects.get_or_create(email=email)

                        cliente.usuario = usuario
                        cliente.email = email
                        cliente.save()
                        return redirect('loja')
                else:
                    erro = "Senhas não conferem"
            else:
                erro = "Preenchar todos os campos"

        context = {'erro': erro}
        return render(request, 'usuario/criarconta.html', context)

def recuperar_senha(request):
    return render(request, 'usuario/recuperar_senha.html')

@login_required
def fazer_logout(request):
    logout(request)
    return redirect('fazer_login')

