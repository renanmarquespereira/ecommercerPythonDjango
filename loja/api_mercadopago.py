import mercadopago

# Essas são as credenciais de teste que fizemos no site do mercado pago como vendedorTeste
public_key = "APP_USR-78acb297-20af-4f81-adb9-2ddb3176784d"
token = "APP_USR-1699042290809085-111222-cb082c0a7045938b863658be81686021-2986635701"

def criar_pagamento(itens_pedido, link):
    sdk = mercadopago.SDK(token)

    itens = []
    for item in itens_pedido:
        itens.append({
            "title": item.item_estoque.produto.nome,
            "quantity": int(item.quantidade),
            "unit_price": float(item.item_estoque.produto.preco)
        })

    preference_data = {
        "items": itens,
        "back_urls": {
            "success": link,
            "pending": link,
            "failure": link
        }
    }

    resposta = sdk.preference().create(preference_data)

    link_pagamento = resposta["response"]["init_point"]
    id_pagamento = resposta["response"]["id"]

    return link_pagamento, id_pagamento



