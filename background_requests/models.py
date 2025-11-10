from django.db import models
from django.contrib.auth import get_user_model

class Request(models.Model):
    PENDING = 'Pending'
    IN_PROGRESS = 'In Progress'
    COMPLETED = 'Completed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    ]
    
    PAYMENT_PENDING = 'payment_pending'
    PAYMENT_COMPLETED = 'payment_completed'
    PAYMENT_FAILED = 'payment_failed'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Payment Pending'),
        (PAYMENT_COMPLETED, 'Payment Completed'),
        (PAYMENT_FAILED, 'Payment Failed'),
    ]
    
    BASIC_REPORT = 'basic'
    PREMIUM_REPORT = 'premium'
    REPORT_TYPE_CHOICES = [
        (BASIC_REPORT, 'Basic Report - $25'),
        (PREMIUM_REPORT, 'Premium Report - $50'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dob = models.DateField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='')
    email = models.EmailField(default='')
    phone_number = models.CharField(max_length=20, default='')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    
    # Payment fields
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_PENDING,
        help_text="Payment status for this report"
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="Type of report selected by user"
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount paid for this report"
    )
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe checkout session ID"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe payment intent ID"
    )
    payment_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was completed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.status} - Payment: {self.payment_status}"
    
    def get_report_price(self):
        """Get price based on report type"""
        if self.report_type == self.BASIC_REPORT:
            return 25.00
        elif self.report_type == self.PREMIUM_REPORT:
            return 50.00
        return None

class Report(models.Model):
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name='report')
    pdf = models.FileField(upload_to='reports/')
    generated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    # Identity Verification Section
    ssn_validation = models.CharField(max_length=100, default='Valid & Matches Records', blank=True)
    address_history = models.CharField(max_length=100, default='Confirmed & Verified', blank=True)
    identity_cross_reference = models.CharField(max_length=100, default='Nothing Found', blank=True)
    database_match = models.CharField(max_length=100, default='100% Match', blank=True)
    
    # Criminal History Check Section
    federal_criminal_records = models.TextField(default='No records found in federal databases', blank=True)
    state_criminal_records = models.TextField(default='No records found', blank=True)
    state_searched = models.CharField(max_length=100, blank=True)
    county_criminal_records = models.TextField(default='No records found', blank=True)
    county_searched = models.CharField(max_length=100, blank=True)
    adult_offender_registry = models.TextField(default='No matches found', blank=True)
    
    # Address History Check
    address_history_details = models.TextField(blank=True, help_text='Detailed address history information')
    
    # Education Verification Section
    education_verified = models.BooleanField(default=False)
    education_degree = models.CharField(max_length=200, blank=True)
    education_institution = models.CharField(max_length=200, blank=True)
    education_graduation_year = models.CharField(max_length=4, blank=True)
    education_status = models.CharField(max_length=100, default='Confirmed by Registrar', blank=True)
    
    # Employment Verification Section (optional for future)
    employment_verified = models.BooleanField(default=False)
    employment_details = models.TextField(blank=True)
    
    # Final Summary & Recommendation
    final_summary = models.TextField(default='Has successfully passed all required checks with no adverse findings.', blank=True)
    recommendation = models.TextField(blank=True, help_text='Additional recommendations or notes')
    
    # Overall Status
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('verified', 'Verified'),
            ('clear', 'Clear'),
            ('pending_review', 'Pending Review'),
            ('flagged', 'Flagged')
        ],
        default='clear'
    )

    def __str__(self):
        return f"Report for {self.request.name}"
