from venv import logger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q  

# -------------------------
# DASHBOARD
# -------------------------
@login_required
def dashboard(request):
    products = Product.objects.all()
    
    # Get personalized product recommendations
    try:
        from .algorithms.product_recommendation import product_recommendation_algorithm
        recommendations = product_recommendation_algorithm.get_personalized_recommendations(
            user=request.user, 
            limit=8
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        recommendations = []
    
    # Get user's cart and wishlist info
    try:
        cart = Cart.objects.get(user=request.user)
        cart_count = cart.cartitem_set.count()
        cart_items = cart.cartitem_set.select_related('product')[:3]  # Recent 3 items
    except Cart.DoesNotExist:
        cart_count = 0
        cart_items = []
    
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        wishlist_count = wishlist.products.count()
        wishlist_items = wishlist.products.all()[:3]  # Recent 3 items
    except Wishlist.DoesNotExist:
        wishlist_count = 0
        wishlist_items = []
    
    # Get popular categories
    popular_categories = Category.objects.annotate(
        product_count=Count('product')
    ).filter(product_count__gt=0).order_by('-product_count')[:6]
    
    context = {
        "products": products,
        "recommendations": recommendations,
        "recommendations_count": len(recommendations),
        "cart_count": cart_count,
        "cart_items": cart_items,
        "wishlist_count": wishlist_count,
        "wishlist_items": wishlist_items,
        "popular_categories": popular_categories,
    }
    
    return render(request, 'dashboard.html', context)

# -------------------------
# PRODUCT DETAIL
# -------------------------
@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, id=pk)
    return render(request, 'product_detail.html', {"product": product})


# -------------------------
# CART VIEWS
# -------------------------
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()

    messages.success(request, "Product added to cart!")
    return redirect('cart')


@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)
    total = sum(item.product.price * item.quantity for item in items)

    return render(request, "cart.html", {"cart_items": items, "cart_total": total})


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    messages.success(request, "Item removed from cart")
    return redirect('cart')


# -------------------------
# ORDER VIEWS
# -------------------------
@login_required
def place_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    items = CartItem.objects.filter(cart=cart)

    if not items:
        messages.error(request, "Your cart is empty")
        return redirect('cart')

    total = sum(item.product.price * item.quantity for item in items)

    order = Order.objects.create(user=request.user, total_amount=total)

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

    items.delete()
    messages.success(request, "Order placed successfully!")
    return redirect('order_success')


@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "orders.html", {"orders": user_orders})


@login_required
def order_success(request):
    return render(request, "order_success.html")


# -------------------------
# WISHLIST VIEWS
# -------------------------
@login_required
def view_wishlist(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, "wishlist.html", {"wishlist": wishlist})


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    messages.success(request, "Product added to wishlist!")
    return redirect('wishlist')


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    messages.success(request, "Product removed from wishlist")
    return redirect('wishlist')

@login_required
def user_logout(request):
    """Custom logout view for normal users"""
    logout(request)
    messages.success(request, "You have been successfully logged out!")
    return redirect('dashboard')

@login_required
def user_profile(request):
    """User profile page"""
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'profile.html', {
        'user_orders': user_orders
    })

@login_required
def user_logout(request):
    """Custom logout view for normal users"""
    logout(request)
    messages.success(request, "You have been successfully logged out!")
    return redirect('dashboard')

# shop/views.py - Add these wishlist views
@login_required
def view_wishlist(request):
    """View user's wishlist"""
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = wishlist.products.all()
    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})

@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product in wishlist.products.all():
        messages.info(request, "Product is already in your wishlist!")
    else:
        wishlist.products.add(product)
        messages.success(request, f"{product.name} added to your wishlist!")
    
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    messages.success(request, f"{product.name} removed from your wishlist")
    return redirect('wishlist')

# -------------------------
# RECOMMENDATIONS PAGE
# -------------------------
@login_required
def recommendations_page(request):
    """Dedicated recommendations page"""
    try:
        from .algorithms.product_recommendation import product_recommendation_algorithm
        
        # Get different types of recommendations
        personalized_recommendations = product_recommendation_algorithm.get_personalized_recommendations(
            user=request.user, limit=20
        )
        
        # Get user's favorite categories for section headers
        user_categories = set()
        try:
            cart = Cart.objects.get(user=request.user)
            cart_categories = CartItem.objects.filter(cart=cart).values_list(
                'product__category__name', flat=True
            ).distinct()
            user_categories.update(cart_categories)
        except Cart.DoesNotExist:
            pass
        
        try:
            wishlist = Wishlist.objects.get(user=request.user)
            wishlist_categories = wishlist.products.values_list('category__name', flat=True).distinct()
            user_categories.update(wishlist_categories)
        except Wishlist.DoesNotExist:
            pass
        
        context = {
            'personalized_recommendations': personalized_recommendations,
            'user_categories': list(user_categories)[:3],  # Top 3 categories
        }
        
        return render(request, 'recommendations.html', context)
        
    except Exception as e:
        logger.error(f"Error loading recommendations page: {str(e)}")
        messages.error(request, "Unable to load recommendations at this time.")
        return redirect('dashboard')
    
# shop/views.py - Add this function
@login_required
def category_products(request, category_slug):
    """View products by category"""
    try:
        category = Category.objects.get(slug=category_slug)
        products = Product.objects.filter(category=category, stock__gt=0)
        
        context = {
            'category': category,
            'products': products,
        }
        return render(request, 'category_products.html', context)
        
    except Category.DoesNotExist:
        messages.error(request, "Category not found.")
        return redirect('dashboard')