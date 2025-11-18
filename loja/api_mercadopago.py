import mercadopago

# Essas são as credenciais de teste que fizemos no site do mercado pago como vendedorTeste
public_key = "APP_USR-78acb297-20af-4f81-adb9-2ddb3176784d"
token = "APP_USR-1699042290809085-111222-cb082c0a7045938b863658be81686021-2986635701"

def criar_pagamento(itens_pedido, link):
    # Configure as credenciais
    sdk = mercadopago.SDK(token)
    # Crie um item na preferência

    # itens que ele está comprando no formato de dicionário
    itens = []
    for item in itens_pedido:
        quantidade = int(item.quantidade)
        nome_produto = item.item_estoque.produto.nome
        preco_unitario = float(item.item_estoque.produto.preco)
        itens.append({
            "title": nome_produto,
            "quantity": quantidade,
            "unit_price": preco_unitario,
        })

    # valor total
    preference_data = {
        "items": itens,
        "back_urls": {
            "success": link,
            "pending": link,
            "failure": link,
        },
        "auto_return": "all",
    }
    resposta = sdk.preference().create(preference_data)
    link_pagamento = resposta["response"]["init_point"]
    id_pagamento = resposta["response"]["id"]

    return link_pagamento, id_pagamento
