from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan, SubscriptionFeature, PlanFeature
import stripe
from django.conf import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class Command(BaseCommand):
    help = 'Create subscription plans with Stripe integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-stripe-products',
            action='store_true',
            help='Create products and prices in Stripe',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating subscription plans...'))
        
        # Clear existing plans (optional - comment out if you want to keep old plans)
        if options.get('create_stripe_products'):
            response = input('This will create new products in Stripe. Continue? (yes/no): ')
            if response.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Create subscription plans with Stripe products
        plans_data = [
            {
                'name': 'Basic Plan',
                'description': '• Basic identity verification\n• County criminal records search\n• Up to 5 requests per month\n• Standard support',
                'plan_type': 'basic',
                'price': 25.00,
                'billing_cycle': 'monthly',
                'max_requests_per_month': 5,
                'priority_support': False,
                'advanced_reports': False,
                'api_access': True,
                'bulk_requests': False,
                'basic_identity_verification': True,
                'criminal_records_search': True,
                'employment_verification': False,
                'education_verification': False,
                'federal_records_search': False,
            },
            {
                'name': 'Premium Plan',
                'description': '• Complete identity verification\n• Federal, state & county criminal records\n• Employment history verification\n• Education verification\n• Unlimited requests\n• Priority Support\n• 30-day report access',
                'plan_type': 'premium',
                'price': 50.00,
                'billing_cycle': 'monthly',
                'max_requests_per_month': 999999,  # Unlimited
                'priority_support': True,
                'advanced_reports': True,
                'api_access': True,
                'bulk_requests': True,
                'basic_identity_verification': True,
                'criminal_records_search': True,
                'employment_verification': True,
                'education_verification': True,
                'federal_records_search': True,
            }
        ]
        
        for plan_data in plans_data:
            # Create Stripe product and price if requested
            stripe_price_id = None
            if options.get('create_stripe_products'):
                try:
                    self.stdout.write(f'Creating Stripe product for: {plan_data["name"]}')
                    
                    # Create product in Stripe
                    product = stripe.Product.create(
                        name=plan_data['name'],
                        description=plan_data['description'],
                    )
                    
                    # Create price in Stripe
                    price = stripe.Price.create(
                        product=product.id,
                        unit_amount=int(plan_data['price'] * 100),  # Convert to cents
                        currency='usd',
                        recurring={'interval': 'month'},
                    )
                    
                    stripe_price_id = price.id
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created Stripe Product: {product.id}'))
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created Stripe Price: {price.id}'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Error creating Stripe product: {str(e)}'))
            
            # Create or update the plan in database
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults={
                    **plan_data,
                    'stripe_price_id': stripe_price_id or plan_data.get('stripe_price_id', '')
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created plan: {plan.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Updated plan: {plan.name}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== SUBSCRIPTION PLANS CREATED ===\n'))
        
        # Display summary
        for plan in SubscriptionPlan.objects.all().order_by('price'):
            self.stdout.write(self.style.SUCCESS(f'\n{plan.name} - ${plan.price}/{plan.billing_cycle}'))
            self.stdout.write(f'  Plan Type: {plan.plan_type}')
            self.stdout.write(f'  Max Requests: {"Unlimited" if plan.max_requests_per_month > 900000 else f"{plan.max_requests_per_month}/month"}')
            self.stdout.write(f'  Stripe Price ID: {plan.stripe_price_id or "Not set"}')
            self.stdout.write('\n  Features:')
            if plan.basic_identity_verification:
                self.stdout.write('    ✓ Basic identity verification')
            if plan.criminal_records_search:
                self.stdout.write('    ✓ Criminal records search')
            if plan.employment_verification:
                self.stdout.write('    ✓ Employment verification')
            if plan.education_verification:
                self.stdout.write('    ✓ Education verification')
            if plan.federal_records_search:
                self.stdout.write('    ✓ Federal records search')
            if plan.priority_support:
                self.stdout.write('    ✓ Priority support')
            if plan.advanced_reports:
                self.stdout.write('    ✓ Advanced reports')
            if plan.api_access:
                self.stdout.write('    ✓ API access')
            if plan.bulk_requests:
                self.stdout.write('    ✓ Bulk requests')
        
        self.stdout.write(self.style.SUCCESS('\n\n✓ All plans created successfully!'))
        
        if not options.get('create_stripe_products'):
            self.stdout.write(self.style.WARNING('\nNote: Stripe products were not created.'))
            self.stdout.write(self.style.WARNING('Run with --create-stripe-products flag to create them in Stripe.'))