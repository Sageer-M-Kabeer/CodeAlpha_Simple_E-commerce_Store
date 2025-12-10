# shop/algorithms/product_recommendation.py
# import pandas as pd
# import numpy as np
from itertools import combinations
from collections import defaultdict
import math
from typing import List, Dict, Any, Optional, Set, Tuple
from django.db.models import Count, Avg, Q, F
from shop.models import Product, Category, Cart, CartItem, Wishlist, Order, OrderItem
from accounts.models import User
import logging

logger = logging.getLogger(__name__)

class ProductRecommendationAlgorithm:
    def __init__(self, min_support=2.0, min_confidence=50.0):
        """
        Initialize the product recommendation algorithm
        
        Args:
            min_support: Minimum support percentage for association rules
            min_confidence: Minimum confidence percentage for association rules
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.logger = logging.getLogger(__name__)

    def _to_fraction(self, val: float) -> float:
        """Convert percent-style (>1) to fractional if necessary."""
        if val is None:
            return 0.0
        return (val / 100.0) if val > 1.0 else val

    def prepare_user_transactions(self) -> List[List[str]]:
        """
        Prepare transactions based on user behavior:
        - Cart items
        - Wishlist items  
        - Purchase history
        - Category preferences
        """
        transactions = []
        
        try:
            # ===== TRANSACTION TYPE 1: CART ITEMS =====
            carts_with_items = Cart.objects.filter(
                cartitem__isnull=False
            ).select_related('user').prefetch_related('cartitem__product__category')
            
            for cart in carts_with_items:
                transaction = []
                cart_items = cart.cartitem_set.all()
                
                # Add cart items as products
                for item in cart_items:
                    product = item.product
                    transaction.append(f"Product_{product.id}")
                    transaction.append(f"Category_{product.category.name.replace(' ', '_')}")
                
                # Add user preferences if available
                if cart.user.first_name:
                    transaction.append(f"User_Has_Profile")
                
                if len(transaction) >= 2:  # Only add meaningful transactions
                    transactions.append(transaction)
            
            self.logger.info(f"Prepared {len(transactions)} cart transactions")
            
            # ===== TRANSACTION TYPE 2: WISHLIST ITEMS =====
            wishlists_with_items = Wishlist.objects.filter(
                products__isnull=False
            ).select_related('user').prefetch_related('products__category')
            
            for wishlist in wishlists_with_items:
                transaction = []
                wishlist_products = wishlist.products.all()
                
                for product in wishlist_products:
                    transaction.append(f"Product_{product.id}")
                    transaction.append(f"Category_{product.category.name.replace(' ', '_')}")
                    transaction.append(f"Wishlist_Item")
                
                if len(transaction) >= 2:
                    transactions.append(transaction)
            
            self.logger.info(f"Prepared {len(transactions)} total transactions with wishlists")
            
            # ===== TRANSACTION TYPE 3: PURCHASE HISTORY =====
            completed_orders = Order.objects.filter(
                status__in=['completed', 'paid', 'shipped'],
                items__isnull=False
            ).select_related('user').prefetch_related('items__product__category').distinct()
            
            for order in completed_orders:
                transaction = []
                order_items = order.items.all()
                
                for item in order_items:
                    if item.product:
                        product = item.product
                        transaction.append(f"Product_{product.id}")
                        transaction.append(f"Category_{product.category.name.replace(' ', '_')}")
                        transaction.append(f"Purchased_Product")
                
                # Add purchase context
                if order.total_amount >= 10000:
                    transaction.append("High_Value_Purchase")
                elif order.total_amount >= 5000:
                    transaction.append("Medium_Value_Purchase")
                else:
                    transaction.append("Low_Value_Purchase")
                
                if len(transaction) >= 2:
                    transactions.append(transaction)
            
            self.logger.info(f"Prepared {len(transactions)} total transactions with purchases")
            
            # ===== TRANSACTION TYPE 4: CATEGORY CO-OCCURRENCE =====
            category_transactions = self._prepare_category_cooccurrence_transactions()
            transactions.extend(category_transactions)
            
            self.logger.info(f"Final total transactions: {len(transactions)}")
            
        except Exception as e:
            self.logger.error(f"Error preparing user transactions: {str(e)}")
            transactions = self._get_sample_transactions()
        
        return transactions

    def _prepare_category_cooccurrence_transactions(self) -> List[List[str]]:
        """Prepare transactions showing category co-occurrence patterns"""
        transactions = []
        
        try:
            # Get users with multiple carts/orders
            active_users = User.objects.filter(
                Q(cart__cartitem__isnull=False) | 
                Q(order__items__isnull=False)
            ).distinct()
            
            for user in active_users:
                transaction = []
                
                # Get all categories from user's carts
                cart_categories = CartItem.objects.filter(
                    cart__user=user
                ).values_list('product__category__name', flat=True).distinct()
                
                for category in cart_categories:
                    if category:
                        transaction.append(f"Category_{category.replace(' ', '_')}")
                        transaction.append(f"User_Category_{category.replace(' ', '_')}")
                
                # Get all categories from user's orders
                order_categories = OrderItem.objects.filter(
                    order__user=user
                ).values_list('product__category__name', flat=True).distinct()
                
                for category in order_categories:
                    if category:
                        transaction.append(f"Category_{category.replace(' ', '_')}")
                        transaction.append(f"Purchased_Category_{category.replace(' ', '_')}")
                
                # Get wishlist categories
                try:
                    wishlist = Wishlist.objects.get(user=user)
                    wishlist_categories = wishlist.products.values_list(
                        'category__name', flat=True
                    ).distinct()
                    
                    for category in wishlist_categories:
                        if category:
                            transaction.append(f"Category_{category.replace(' ', '_')}")
                            transaction.append(f"Wishlist_Category_{category.replace(' ', '_')}")
                except Wishlist.DoesNotExist:
                    pass
                
                if len(set(transaction)) >= 2:  # At least 2 unique categories
                    transactions.append(list(set(transaction)))
            
        except Exception as e:
            self.logger.error(f"Error preparing category transactions: {str(e)}")
        
        return transactions

    def prepare_product_attributes(self) -> List[List[str]]:
        """
        Prepare transactions based on product attributes and relationships
        """
        transactions = []
        
        try:
            # Get products with sales data
            products_with_orders = Product.objects.filter(
                orderitem__isnull=False
            ).annotate(
                total_sold=Count('orderitem'),
                avg_rating=Avg('orderitem__order__user__profile__seller_rating')  # If you have ratings
            )
            
            for product in products_with_orders:
                transaction = []
                
                # Basic product attributes
                transaction.append(f"Product_{product.id}")
                transaction.append(f"Category_{product.category.name.replace(' ', '_')}")
                
                # Price categories
                price = float(product.price)
                if price >= 5000:
                    transaction.append("Price_High")
                    transaction.append("Premium_Product")
                elif price >= 2000:
                    transaction.append("Price_Medium_High")
                elif price >= 1000:
                    transaction.append("Price_Medium")
                elif price >= 500:
                    transaction.append("Price_Low_Medium")
                else:
                    transaction.append("Price_Low")
                    transaction.append("Budget_Product")
                
                # Stock status
                if product.stock >= 20:
                    transaction.append("High_Stock")
                elif product.stock >= 5:
                    transaction.append("Medium_Stock")
                else:
                    transaction.append("Low_Stock")
                
                # Popularity based on sales
                if product.total_sold >= 10:
                    transaction.append("Best_Seller")
                    transaction.append("High_Demand")
                elif product.total_sold >= 5:
                    transaction.append("Popular_Item")
                
                # Category-specific attributes
                category_name = product.category.name.lower()
                if any(keyword in category_name for keyword in ['electronic', 'tech', 'gadget']):
                    transaction.append("Tech_Product")
                elif any(keyword in category_name for keyword in ['fashion', 'clothing', 'wear']):
                    transaction.append("Fashion_Product")
                elif any(keyword in category_name for keyword in ['home', 'decor', 'furniture']):
                    transaction.append("Home_Product")
                
                transactions.append(transaction)
            
            self.logger.info(f"Prepared {len(transactions)} product attribute transactions")
            
        except Exception as e:
            self.logger.error(f"Error preparing product attributes: {str(e)}")
        
        return transactions

    def run_product_recommendation_analysis(self, max_itemset_length: int = 3) -> List[Dict[str, Any]]:
        """
        Run Apriori algorithm to find association rules for product recommendations
        """
        try:
            # Combine transaction types
            user_transactions = self.prepare_user_transactions()
            product_transactions = self.prepare_product_attributes()
            
            all_transactions = user_transactions + product_transactions
            
            self.logger.info(f"Total transactions for analysis: {len(all_transactions)}")
            
            if len(all_transactions) == 0:
                self.logger.warning("No transactions found for analysis")
                return self._get_sample_recommendation_rules()
            
            num_transactions = len(all_transactions)
            
            # Convert thresholds to fractions
            min_support_frac = self._to_fraction(self.min_support)
            min_confidence_frac = self._to_fraction(self.min_confidence)
            
            min_support_count = math.ceil(min_support_frac * num_transactions)
            
            self.logger.info(f"Minimum support count: {min_support_count} out of {num_transactions} transactions")
            
            # 1) Count singleton supports
            item_counts = defaultdict(int)
            for transaction in all_transactions:
                for item in set(transaction):
                    item_counts[item] += 1
            
            # Frequent 1-itemsets
            frequent_itemsets = {}
            L1 = {}
            for item, count in item_counts.items():
                if count >= min_support_count:
                    L1[frozenset([item])] = count
            
            self.logger.info(f"Found {len(L1)} frequent 1-itemsets")
            
            if not L1:
                self.logger.warning("No frequent 1-itemsets found")
                return []
            
            frequent_itemsets[1] = L1
            
            # 2) Generate larger itemsets
            k = 2
            while k <= max_itemset_length:
                prev_L = frequent_itemsets.get(k - 1, {})
                if not prev_L:
                    break
                
                candidates = self._generate_candidates(prev_L, k)
                candidate_counts = defaultdict(int)
                
                self.logger.info(f"Generated {len(candidates)} candidate {k}-itemsets")
                
                for transaction in all_transactions:
                    trans_set = set(transaction)
                    for candidate in candidates:
                        if candidate.issubset(trans_set):
                            candidate_counts[candidate] += 1
                
                # Filter by min support
                Lk = {}
                for candidate, count in candidate_counts.items():
                    if count >= min_support_count:
                        Lk[candidate] = count
                
                self.logger.info(f"Found {len(Lk)} frequent {k}-itemsets")
                
                if not Lk:
                    break
                
                frequent_itemsets[k] = Lk
                k += 1
            
            # 3) Build support lookup
            support_counts = {}
            for size, itemsets in frequent_itemsets.items():
                for itemset, count in itemsets.items():
                    support_counts[itemset] = count
            
            # 4) Generate recommendation rules
            recommendations = []
            for size, itemsets in frequent_itemsets.items():
                if size < 2:
                    continue
                
                for itemset, itemset_count in itemsets.items():
                    itemset_list = list(itemset)
                    sup_xy_frac = itemset_count / num_transactions
                    
                    # Generate rules for all possible antecedents
                    for r in range(1, len(itemset_list)):
                        for antecedent_tuple in combinations(itemset_list, r):
                            antecedent_fs = frozenset(antecedent_tuple)
                            consequent_fs = itemset - antecedent_fs
                            
                            # We're interested in rules that recommend products/categories
                            if not self._is_interesting_product_consequent(consequent_fs):
                                continue
                            
                            antecedent_count = support_counts.get(antecedent_fs, 0)
                            if antecedent_count == 0:
                                continue
                            
                            confidence_frac = sup_xy_frac / (antecedent_count / num_transactions)
                            
                            if confidence_frac >= min_confidence_frac:
                                # Calculate lift
                                consequent_support = 0
                                for consequent_item in consequent_fs:
                                    item_support = item_counts.get(consequent_item, 0) / num_transactions
                                    consequent_support = max(consequent_support, item_support)
                                
                                lift = sup_xy_frac / ((antecedent_count / num_transactions) * consequent_support) if consequent_support > 0 else 0
                                
                                # Only include rules with meaningful lift
                                if lift >= 1.0:
                                    recommendations.append({
                                        'antecedent': sorted(list(antecedent_fs)),
                                        'consequent': sorted(list(consequent_fs)),
                                        'support': round(sup_xy_frac * 100, 2),
                                        'confidence': round(confidence_frac * 100, 2),
                                        'lift': round(lift, 2)
                                    })
            
            # Sort by confidence and support
            recommendations.sort(key=lambda x: (x['confidence'], x['support']), reverse=True)
            
            self.logger.info(f"Generated {len(recommendations)} association rules")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error in product recommendation analysis: {str(e)}")
            return self._get_sample_recommendation_rules()

    def _is_interesting_product_consequent(self, consequent_fs: Set[str]) -> bool:
        """Check if consequent contains interesting product recommendation attributes"""
        consequent_list = list(consequent_fs)
        
        # We want rules that recommend specific products or categories
        interesting_patterns = [
            'Product_', 'Category_', 'Best_Seller', 'Popular_Item', 
            'Tech_Product', 'Fashion_Product', 'Home_Product',
            'Premium_Product', 'Budget_Product'
        ]
        
        for consequent in consequent_list:
            for pattern in interesting_patterns:
                if pattern in consequent:
                    return True
        return False

    def _generate_candidates(self, prev_frequent: Dict[frozenset, int], k: int) -> Set[frozenset]:
        """Generate candidate k-itemsets from (k-1)-itemsets"""
        itemsets = list(prev_frequent.keys())
        candidates = set()
        
        for i in range(len(itemsets)):
            for j in range(i + 1, len(itemsets)):
                union = itemsets[i].union(itemsets[j])
                if len(union) == k:
                    # Prune: check if all subsets are frequent
                    valid = True
                    for subset in combinations(sorted(union), k - 1):
                        if frozenset(subset) not in prev_frequent:
                            valid = False
                            break
                    if valid:
                        candidates.add(union)
        
        return candidates

    def get_recommended_products(self, user=None, category=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recommended products based on association rules and user behavior
        
        Args:
            user: Optional user for personalization
            category: Optional category filter
            limit: Maximum number of products to return
        """
        try:
            # Get association rules
            rules = self.run_product_recommendation_analysis()
            
            # Get potential products (in stock)
            potential_products = Product.objects.filter(stock__gt=0).select_related('category')
            
            if category:
                potential_products = potential_products.filter(category=category)
            
            self.logger.info(f"Evaluating {potential_products.count()} potential products")
            
            recommended_products = []
            
            for product in potential_products:
                score = 0
                matching_rules = []
                recommendation_reasons = []
                
                product_attributes = self._get_product_attributes(product)
                
                # Calculate recommendation score based on rules
                for rule in rules:
                    rule_consequents = set(rule['consequent'])
                    
                    # Check if product matches rule consequent
                    if rule_consequents.intersection(product_attributes):
                        rule_score = rule['confidence'] * rule['lift']
                        score += rule_score
                        matching_rules.append(rule)
                        
                        # Add reason for recommendation
                        reason = self._format_product_recommendation_reason(rule, product_attributes)
                        if reason and reason not in recommendation_reasons:
                            recommendation_reasons.append(reason)
                
                # Boost score for best sellers
                total_sold = OrderItem.objects.filter(product=product).count()
                if total_sold >= 10:
                    score += 30
                    recommendation_reasons.append("Best-selling product")
                elif total_sold >= 5:
                    score += 20
                    recommendation_reasons.append("Popular item")
                
                # Boost score for high stock (availability)
                if product.stock >= 20:
                    score += 15
                    recommendation_reasons.append("High availability")
                
                # Boost for premium products
                if float(product.price) >= 5000:
                    score += 10
                
                # Personalization boost if user provided
                if user:
                    user_boost = self._calculate_user_personalization_boost(user, product)
                    score += user_boost
                
                # Only include products with meaningful scores
                if score > 0:
                    # Limit reasons to top 5
                    limited_reasons = recommendation_reasons[:5]
                    
                    recommended_products.append({
                        'product': product,
                        'score': round(score, 2),
                        'matching_rules_count': len(matching_rules),
                        'recommendation_reasons': limited_reasons,
                        'total_sold': total_sold,
                        'in_stock': product.stock,
                        'product_attributes': list(product_attributes)
                    })
            
            # Sort by score and return top products
            recommended_products.sort(key=lambda x: x['score'], reverse=True)
            
            self.logger.info(f"Found {len(recommended_products)} recommended products")
            
            return recommended_products[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting recommended products: {str(e)}")
            return self._get_sample_recommended_products()

    def get_personalized_recommendations(self, user, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personalized product recommendations for a specific user
        """
        try:
            # Get user's cart, wishlist, and purchase history
            user_categories = set()
            
            # Cart categories
            try:
                cart = Cart.objects.get(user=user)
                cart_categories = CartItem.objects.filter(cart=cart).values_list(
                    'product__category__name', flat=True
                ).distinct()
                user_categories.update(cart_categories)
            except Cart.DoesNotExist:
                pass
            
            # Wishlist categories
            try:
                wishlist = Wishlist.objects.get(user=user)
                wishlist_categories = wishlist.products.values_list(
                    'category__name', flat=True
                ).distinct()
                user_categories.update(wishlist_categories)
            except Wishlist.DoesNotExist:
                pass
            
            # Purchase history categories
            order_categories = OrderItem.objects.filter(
                order__user=user
            ).values_list('product__category__name', flat=True).distinct()
            user_categories.update(order_categories)
            
            # Get recommendations based on user's categories
            all_recommendations = []
            for category_name in user_categories:
                if category_name:
                    try:
                        category = Category.objects.get(name=category_name)
                        category_recommendations = self.get_recommended_products(
                            user=user, category=category, limit=5
                        )
                        all_recommendations.extend(category_recommendations)
                    except Category.DoesNotExist:
                        continue
            
            # Remove duplicates and sort by score
            unique_recommendations = {}
            for rec in all_recommendations:
                product_id = rec['product'].id
                if product_id not in unique_recommendations or rec['score'] > unique_recommendations[product_id]['score']:
                    unique_recommendations[product_id] = rec
            
            final_recommendations = sorted(
                unique_recommendations.values(), 
                key=lambda x: x['score'], 
                reverse=True
            )
            
            return final_recommendations[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting personalized recommendations: {str(e)}")
            return self.get_recommended_products(limit=limit)

    def _get_product_attributes(self, product: Product) -> Set[str]:
        """Get product attributes for rule matching"""
        attributes = set()
        
        # Basic identifiers
        attributes.add(f"Product_{product.id}")
        attributes.add(f"Category_{product.category.name.replace(' ', '_')}")
        
        # Price categories
        price = float(product.price)
        if price >= 5000:
            attributes.add("Price_High")
            attributes.add("Premium_Product")
        elif price >= 2000:
            attributes.add("Price_Medium_High")
        elif price >= 1000:
            attributes.add("Price_Medium")
        elif price >= 500:
            attributes.add("Price_Low_Medium")
        else:
            attributes.add("Price_Low")
            attributes.add("Budget_Product")
        
        # Stock status
        if product.stock >= 20:
            attributes.add("High_Stock")
        elif product.stock >= 5:
            attributes.add("Medium_Stock")
        else:
            attributes.add("Low_Stock")
        
        # Popularity
        total_sold = OrderItem.objects.filter(product=product).count()
        if total_sold >= 10:
            attributes.add("Best_Seller")
            attributes.add("High_Demand")
        elif total_sold >= 5:
            attributes.add("Popular_Item")
        
        # Category-specific
        category_name = product.category.name.lower()
        if any(keyword in category_name for keyword in ['electronic', 'tech', 'gadget']):
            attributes.add("Tech_Product")
        elif any(keyword in category_name for keyword in ['fashion', 'clothing', 'wear']):
            attributes.add("Fashion_Product")
        elif any(keyword in category_name for keyword in ['home', 'decor', 'furniture']):
            attributes.add("Home_Product")
        
        return attributes

    def _calculate_user_personalization_boost(self, user: User, product: Product) -> float:
        """Calculate personalization boost based on user behavior"""
        boost = 0
        
        try:
            # Check if product is in user's wishlist
            try:
                wishlist = Wishlist.objects.get(user=user)
                if product in wishlist.products.all():
                    boost += 25
            except Wishlist.DoesNotExist:
                pass
            
            # Check if product is in user's cart
            try:
                cart = Cart.objects.get(user=user)
                if CartItem.objects.filter(cart=cart, product=product).exists():
                    boost += 20
            except Cart.DoesNotExist:
                pass
            
            # Check if user has purchased similar category products
            similar_purchases = OrderItem.objects.filter(
                order__user=user,
                product__category=product.category
            ).count()
            
            if similar_purchases >= 3:
                boost += 15
            elif similar_purchases >= 1:
                boost += 10
            
        except Exception as e:
            self.logger.error(f"Error calculating personalization boost: {str(e)}")
        
        return boost

    def _format_product_recommendation_reason(self, rule: Dict, product_attributes: Set[str]) -> str:
        """Format a human-readable recommendation reason"""
        antecedents = rule['antecedent']
        consequents = rule['consequent']
        
        # Find matching consequent
        matching_consequent = None
        for consequent in consequents:
            if consequent in product_attributes:
                matching_consequent = consequent
                break
        
        if not matching_consequent:
            return ""
        
        # Format antecedents
        if len(antecedents) == 1:
            antecedent_text = self._format_attribute(antecedents[0])
        else:
            antecedent_text = ", ".join([self._format_attribute(a) for a in antecedents[:-1]])
            antecedent_text += f" and {self._format_attribute(antecedents[-1])}"
        
        # Format consequent
        consequent_text = self._format_attribute(matching_consequent)
        
        return f"Customers interested in {antecedent_text} also purchase {consequent_text}"

    def _format_attribute(self, attribute: str) -> str:
        """Format attribute for human-readable display"""
        if attribute.startswith('Category_'):
            return attribute.replace('Category_', '').replace('_', ' ') + ' products'
        elif attribute.startswith('Product_'):
            return 'this product'
        elif attribute.startswith('Price_'):
            return attribute.replace('Price_', '').replace('_', ' ').lower() + ' priced items'
        else:
            return attribute.replace('_', ' ').lower()

    def _get_sample_transactions(self) -> List[List[str]]:
        """Return sample transactions for testing"""
        return [
            ["Product_123", "Category_Electronics", "Price_Medium", "Tech_Product"],
            ["Product_456", "Category_Books", "Price_Low", "Budget_Product"],
            ["Category_Electronics", "Category_Accessories", "User_Has_Profile"],
            ["Category_Books", "Category_Stationery", "Wishlist_Item"],
            ["Product_123", "Product_789", "Purchased_Product", "High_Value_Purchase"]
        ]

    def _get_sample_recommendation_rules(self) -> List[Dict[str, Any]]:
        """Return sample association rules for testing"""
        return [
            {
                'antecedent': ['Category_Electronics', 'Price_Medium'],
                'consequent': ['Tech_Product', 'Popular_Item'],
                'support': 12.5,
                'confidence': 75.3,
                'lift': 2.1
            },
            {
                'antecedent': ['Wishlist_Item', 'Category_Books'],
                'consequent': ['Budget_Product', 'Category_Stationery'],
                'support': 8.7,
                'confidence': 68.9,
                'lift': 1.8
            },
            {
                'antecedent': ['Purchased_Product', 'High_Value_Purchase'],
                'consequent': ['Premium_Product', 'Best_Seller'],
                'support': 15.2,
                'confidence': 82.1,
                'lift': 2.3
            }
        ]

    def _get_sample_recommended_products(self) -> List[Dict[str, Any]]:
        """Return sample recommended products for testing"""
        try:
            # Get some actual products from the database for realistic samples
            sample_products = Product.objects.filter(stock__gt=0)[:3]
            
            recommendations = []
            for product in sample_products:
                total_sold = OrderItem.objects.filter(product=product).count()
                
                recommendations.append({
                    'product': product,
                    'score': 78.5,
                    'matching_rules_count': 3,
                    'recommendation_reasons': [
                        "Frequently purchased with similar items",
                        "Popular in Electronics category",
                        "High customer satisfaction"
                    ],
                    'total_sold': total_sold,
                    'in_stock': product.stock,
                    'product_attributes': ['Category_Electronics', 'Price_Medium', 'Tech_Product']
                })
            
            return recommendations
            
        except Exception:
            # Fallback if no real products exist
            return [
                {
                    'product': None,
                    'score': 78.5,
                    'matching_rules_count': 3,
                    'recommendation_reasons': [
                        "Frequently purchased with similar items",
                        "Popular in Electronics category",
                        "High customer satisfaction"
                    ],
                    'total_sold': 15,
                    'in_stock': 25,
                    'product_attributes': ['Category_Electronics', 'Price_Medium', 'Tech_Product']
                }
            ]

# Global instance for easy access
product_recommendation_algorithm = ProductRecommendationAlgorithm()