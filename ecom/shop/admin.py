from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, Cart, CartItem, 
    Wishlist, Order, OrderItem
)


# -------------------------
# CATEGORY ADMIN
# -------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    list_filter = ('name',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Number of Products'


# -------------------------
# PRODUCT ADMIN
# -------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'display_image', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description', 'slug')
    list_editable = ('price', 'stock')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'display_image')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock')
        }),
        ('Media', {
            'fields': ('image', 'display_image')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Image Preview'


# -------------------------
# CART ITEM INLINE
# -------------------------
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('product', 'quantity', 'subtotal')
    
    def subtotal(self, obj):
        return f"${obj.subtotal():.2f}"
    subtotal.short_description = 'Subtotal'


# -------------------------
# CART ADMIN
# -------------------------
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'total_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'total_amount_display')
    inlines = [CartItemInline]
    
    def item_count(self, obj):
        return obj.cartitem_set.count()
    item_count.short_description = 'Items'
    
    def total_amount(self, obj):
        total = sum(item.subtotal() for item in obj.cartitem_set.all())
        return f"${total:.2f}"
    total_amount.short_description = 'Total Amount'
    
    def total_amount_display(self, obj):
        total = sum(item.subtotal() for item in obj.cartitem_set.all())
        return f"${total:.2f}"
    total_amount_display.short_description = 'Cart Total'


# -------------------------
# CART ITEM ADMIN
# -------------------------
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'subtotal_display')
    list_filter = ('cart__user',)
    search_fields = ('product__name', 'cart__user__email')
    
    def subtotal_display(self, obj):
        return f"${obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'


# -------------------------
# WISHLIST ADMIN
# -------------------------
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username')
    filter_horizontal = ('products',)
    readonly_fields = ('created_at',)
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Number of Products'


# -------------------------
# ORDER ITEM INLINE
# -------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal_display',)
    fields = ('product', 'quantity', 'price', 'subtotal_display')
    
    def subtotal_display(self, obj):
        return f"${obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'


# -------------------------
# ORDER ADMIN
# -------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'item_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username', 'id')
    readonly_fields = ('created_at', 'total_amount', 'order_summary')
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_completed', 'mark_as_cancelled']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total_amount')
        }),
        ('Order Summary', {
            'fields': ('order_summary',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'
    
    def order_summary(self, obj):
        items = obj.items.all()
        if not items:
            return "No items in this order"
        
        summary = []
        for item in items:
            summary.append(f"{item.quantity} × {item.product.name} - ${item.subtotal():.2f}")
        
        return format_html('<br>'.join(summary))
    order_summary.short_description = 'Order Items'
    
    # Custom actions
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} order(s) marked as paid.')
    mark_as_paid.short_description = "Mark selected orders as Paid"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} order(s) marked as shipped.')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} order(s) marked as completed.')
    mark_as_completed.short_description = "Mark selected orders as Completed"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} order(s) marked as cancelled.')
    mark_as_cancelled.short_description = "Mark selected orders as Cancelled"


# -------------------------
# ORDER ITEM ADMIN
# -------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'quantity', 'price', 'subtotal_display')
    list_filter = ('order__status',)
    search_fields = ('product__name', 'order__user__email')
    readonly_fields = ('subtotal_display',)
    
    def subtotal_display(self, obj):
        return f"${obj.subtotal():.2f}"
    subtotal_display.short_description = 'Subtotal'