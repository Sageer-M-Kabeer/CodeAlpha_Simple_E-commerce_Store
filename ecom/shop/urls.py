from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.dashboard, name='products'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recommendations/', views.recommendations_page, name='recommendations'),
    path('product/<uuid:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<uuid:item_id>/', views.remove_from_cart, name='remove_from_cart'),  # Changed to uuid
    path('orders/', views.orders, name='orders'),
    path('orders/place/', views.place_order, name='place_order'),
    path('orders/success/', views.order_success, name='order_success'),
    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('wishlist/add/<uuid:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<uuid:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('profile/', views.user_profile, name='profile'),
    path('logout/', views.user_logout, name='logout'),
     path('category/<slug:category_slug>/', views.category_products, name='category_products'),
]