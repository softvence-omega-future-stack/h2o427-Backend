from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan
import stripe
from django.conf import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class Command(BaseCommand):
    help = 'Create per-report subscription plans with Stripe integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-stripe-products',
            action='store_true',
            help='Create products and prices in Stripe',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating per-report subscription plans...'))
        
        # Clear existing plans (optional - comment out if you want to keep old plans)
        if options.get('create_stripe_products'):
            response = input('This will create new products in Stripe. Continue? (yes/no): ')
            if response.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Create subscription plans with new per-report structure
        plans_data = [
            {
                'name': 'Basic Plan',
                'description': 'Identity Verification\nSSN Trace\nNational Criminal Search\nSex Offender Registry',
                'plan_type': 'basic',
                'price_per_report': 25.00,
                
                # Basic features
                'identity_verification': True,
                'ssn_trace': True,
                'national_criminal_search': True,
                'sex_offender_registry': True,
                
                # Premium features (not included in basic)
                'employment_verification': False,
                'education_verification': False,
                'unlimited_county_search': False,
                
                # Support
                'priority_support': False,
                'api_access': True,
            },
            {
                'name': 'Premium Plan',
                'description': 'All Basic Plan features plus:\nEmployment History Verification\nEducation Verification\nUnlimited County Criminal Search\nPriority Support',
                'plan_type': 'premium',
                'price_per_report': 50.00,
                
                # All basic features included
                'identity_verification': True,
                'ssn_trace': True,
                'national_criminal_search': True,
                'sex_offender_registry': True,
                
                # Premium features
                'employment_verification': True,
                'education_verification': True,
                'unlimited_county_search': True,
                
                # Support
                'priority_support': True,
                'api_access': True,
            }
        ]
        
        for plan_data in plans_data:
            # Create Stripe product and price if requested
            stripe_price_id = None
            stripe_product_id = None
            
            if options.get('create_stripe_products'):
                try:
                    self.stdout.write(f'Creating Stripe product for: {plan_data["name"]}')
                    
                    # Create product in Stripe
                    product = stripe.Product.create(
                        name=plan_data['name'],
                        description=plan_data['description'],
                    )
                    stripe_product_id = product.id
                    
                    # Create one-time payment price in Stripe (not recurring)
                    price = stripe.Price.create(
                        product=product.id,
                        unit_amount=int(plan_data['price_per_report'] * 100),  # Convert to cents
                        currency='usd',
                        # No recurring parameter - this is a one-time payment per report
                    )
                    
                    stripe_price_id = price.id
                    self.stdout.write(self.style.SUCCESS(f'  Created Stripe Product: {product.id}'))
                    self.stdout.write(self.style.SUCCESS(f'  Created Stripe Price: {price.id}'))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error creating Stripe product: {str(e)}'))
            
            # Create or update the plan in database
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults={
                    **plan_data,
                    'stripe_price_id': stripe_price_id or plan_data.get('stripe_price_id', ''),
                    'stripe_product_id': stripe_product_id or plan_data.get('stripe_product_id', '')
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated plan: {plan.name}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== PER-REPORT SUBSCRIPTION PLANS CREATED ===\n'))
        
        # Display summary
        for plan in SubscriptionPlan.objects.all().order_by('price_per_report'):
            self.stdout.write(self.style.SUCCESS(f'\n{plan.name} - ${plan.price_per_report} per report'))
            self.stdout.write(f'  Plan Type: {plan.plan_type}')
            self.stdout.write(f'  Stripe Price ID: {plan.stripe_price_id or "Not set"}')
            self.stdout.write(f'  Stripe Product ID: {plan.stripe_product_id or "Not set"}')
            self.stdout.write('\n  Features:')
            
            if plan.identity_verification:
                self.stdout.write('    - Identity Verification')
            if plan.ssn_trace:
                self.stdout.write('    - SSN Trace')
            if plan.national_criminal_search:
                self.stdout.write('    - National Criminal Search')
            if plan.sex_offender_registry:
                self.stdout.write('    - Sex Offender Registry')
            if plan.employment_verification:
                self.stdout.write('    - Employment History Verification')
            if plan.education_verification:
                self.stdout.write('    - Education Verification')
            if plan.unlimited_county_search:
                self.stdout.write('    - Unlimited County Criminal Search')
            if plan.priority_support:
                self.stdout.write('    - Priority Support')
            else:
                self.stdout.write('    - Standard Support')
            if plan.api_access:
                self.stdout.write('    - API Access')
        
        self.stdout.write(self.style.SUCCESS('\n\nAll plans created successfully!'))
        self.stdout.write(self.style.WARNING('\nIMPORTANT: Per-report pricing model'))
        self.stdout.write(self.style.WARNING('- No monthly subscription or recurring billing'))
        self.stdout.write(self.style.WARNING('- Users pay per background check report'))
        self.stdout.write(self.style.WARNING('- Each new user gets 1 free search trial'))
        
        if not options.get('create-stripe-products'):
            self.stdout.write(self.style.WARNING('\nNote: Stripe products were not created.'))
            self.stdout.write(self.style.WARNING('Run with --create-stripe-products flag to create them in Stripe.'))