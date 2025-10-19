from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan, SubscriptionFeature, PlanFeature


class Command(BaseCommand):
    help = 'Create sample subscription plans for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating subscription plans...'))
        
        # Create subscription features
        features = [
            {'name': 'basic_checks', 'description': 'Basic background checks'},
            {'name': 'advanced_checks', 'description': 'Advanced background checks with detailed reports'},
            {'name': 'bulk_processing', 'description': 'Process multiple requests at once'},
            {'name': 'priority_support', 'description': 'Priority customer support'},
            {'name': 'api_access', 'description': 'Full API access'},
            {'name': 'custom_reports', 'description': 'Custom report templates'},
            {'name': 'real_time_notifications', 'description': 'Real-time status notifications'},
            {'name': 'data_export', 'description': 'Export data to various formats'},
        ]
        
        created_features = []
        for feature_data in features:
            feature, created = SubscriptionFeature.objects.get_or_create(
                name=feature_data['name'],
                defaults={
                    'description': feature_data['description'],
                    'feature_key': feature_data['name']
                }
            )
            created_features.append(feature)
            if created:
                self.stdout.write(f'Created feature: {feature.name}')
            else:
                self.stdout.write(f'Feature already exists: {feature.name}')
        
        # Create subscription plans
        plans_data = [
            {
                'name': 'Basic Plan',
                'description': 'Perfect for individuals and small businesses',
                'plan_type': 'basic',
                'price': 29.99,
                'billing_cycle': 'monthly',
                'max_requests_per_month': 50,
                'api_access': True,
                'features': ['basic_checks', 'api_access']
            },
            {
                'name': 'Premium Plan',
                'description': 'For growing businesses with advanced needs',
                'plan_type': 'premium',
                'price': 79.99,
                'billing_cycle': 'monthly',
                'max_requests_per_month': 200,
                'priority_support': True,
                'advanced_reports': True,
                'api_access': True,
                'bulk_requests': True,
                'features': ['basic_checks', 'advanced_checks', 'bulk_processing', 'api_access', 'custom_reports']
            },
            {
                'name': 'Enterprise Plan',
                'description': 'For large organizations with unlimited needs',
                'plan_type': 'enterprise',
                'price': 199.99,
                'billing_cycle': 'monthly',
                'max_requests_per_month': 1000,
                'priority_support': True,
                'advanced_reports': True,
                'api_access': True,
                'bulk_requests': True,
                'features': ['basic_checks', 'advanced_checks', 'bulk_processing', 'priority_support', 
                           'api_access', 'custom_reports', 'real_time_notifications', 'data_export']
            },
            {
                'name': 'Basic Annual',
                'description': 'Basic plan with annual billing (20% discount)',
                'plan_type': 'basic',
                'price': 287.90,  # 29.99 * 12 * 0.8
                'billing_cycle': 'yearly',
                'max_requests_per_month': 50,
                'api_access': True,
                'features': ['basic_checks', 'api_access']
            },
            {
                'name': 'Premium Annual',
                'description': 'Premium plan with annual billing (20% discount)',
                'plan_type': 'premium',
                'price': 767.90,  # 79.99 * 12 * 0.8
                'billing_cycle': 'yearly',
                'max_requests_per_month': 200,
                'priority_support': True,
                'advanced_reports': True,
                'api_access': True,
                'bulk_requests': True,
                'features': ['basic_checks', 'advanced_checks', 'bulk_processing', 'api_access', 'custom_reports']
            }
        ]
        
        for plan_data in plans_data:
            features_to_add = plan_data.pop('features')
            
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
                
                # Add features to the plan
                for feature_name in features_to_add:
                    feature = next((f for f in created_features if f.name == feature_name), None)
                    if feature:
                        PlanFeature.objects.get_or_create(
                            plan=plan,
                            feature=feature
                        )
                        self.stdout.write(f'  Added feature: {feature_name}')
            else:
                self.stdout.write(f'Plan already exists: {plan.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created subscription plans!'))
        
        # Display summary
        self.stdout.write('\n=== SUBSCRIPTION PLANS SUMMARY ===')
        for plan in SubscriptionPlan.objects.all().order_by('price'):
            features_list = [pf.feature.name for pf in PlanFeature.objects.filter(plan=plan)]
            self.stdout.write(f'\n{plan.name} - ${plan.price}/{plan.billing_cycle}')
            self.stdout.write(f'  Max requests: {plan.max_requests_per_month}/month')
            self.stdout.write(f'  Features: {", ".join(features_list)}')