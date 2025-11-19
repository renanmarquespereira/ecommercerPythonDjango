from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #Home
    path('', views.homepage, name='homepage'),
    
    #Login
    path('login/', views.fazer_login, name='fazer_login'),
    path('logout/', views.fazer_logout, name='fazer_logout'),
    
    #Loja
    path('meuspedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('loja/', views.loja, name='loja'),
    path('loja/<str:filtro>/', views.loja, name='loja'),
    path('loja/produto/<int:id_produto>/', views.ver_produto, name='ver_produto'),
    path('loja/produto/<int:id_produto>/<int:id_cor>/', views.ver_produto, name='ver_produto'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('checkout/', views.checkout, name='checkout'),
    path('pedidoaprovado/<int:id_pedido>/', views.pedido_aprovado, name='pedido_aprovado'),
    path('adicionarcarrinho/<int:id_produto>/', views.adicionar_carrinho, name='adicionar_carrinho'),
    path('excluircarrinho/<int:id_produto>/', views.excluir_carrinho, name='excluir_carrinho'),
    path('adicionarendereco/', views.adicionar_endereco, name='adicionar_endereco'),
    path('finalizarpedido/<int:id_pedido>/', views.finalizar_pedido, name='finalizar_pedido'),
    path('finalizarpagamento/', views.finalizar_pagamento, name='finalizar_pagamento'),
    
    #Conta
    path('criarconta/', views.criar_conta, name='criar_conta'),
    path('minhaconta/', views.minha_conta, name='minha_conta'),
    path('recuperarsenha/', views.recuperar_senha, name='recuperar_senha'),
    path("password_change/", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]