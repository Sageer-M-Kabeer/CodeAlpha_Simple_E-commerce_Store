from django.core.management.base import BaseCommand
from shop.algorithms.product_recommendation import product_recommendation_algorithm
import json
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Generate and cache product recommendations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear recommendation cache before generating'
        )
    
    def handle(self, *args, **options):
        if options['clear_cache']:
            self.stdout.write('Clearing recommendation cache...')
            # Clear all recommendation-related cache keys
            for key in cache.keys('*recommendation*'):
                cache.delete(key)
        
        self.stdout.write('Generating product recommendations...')
        
        # Generate recommendations for different categories
        from shop.models import Category
        
        categories = Category.objects.all()[:5]  # Top 5 categories
        
        for category in categories:
            self.stdout.write(f'Generating recommendations for {category.name}...')
            recommendations = product_recommendation_algorithm.get_recommended_products(
                category=category, 
                limit=10
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Generated {len(recommendations)} recommendations for {category.name}'
                )
            )
        
        # Generate general recommendations
        general_recommendations = product_recommendation_algorithm.get_recommended_products(limit=20)
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Generated {len(general_recommendations)} general recommendations'
            )
        )
        
        # Generate association rules
        rules = product_recommendation_algorithm.run_product_recommendation_analysis()
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Generated {len(rules)} association rules'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('Product recommendation generation completed!'))