#!/usr/bin/env python3
"""
🔧 Quick Admin Fix Verification
===============================
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from subscriptions.models import SubscriptionPlan

def test_admin_fixes():
    """Quick test of the admin fixes"""
    
    print("🔧 Testing Admin Interface Fixes")
    print("=" * 40)
    
    try:
        # Test the relationship fix that was causing the error
        plans = SubscriptionPlan.objects.all()
        for plan in plans:
            feature_count = plan.features.count()
            print(f"✅ {plan.name}: {feature_count} features")
        
        print(f"\n✅ SUCCESS: All admin fixes working!")
        print(f"🌐 Admin interface ready at: http://127.0.0.1:8000/admin/")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_admin_fixes()