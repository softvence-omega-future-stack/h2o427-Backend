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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.status}"

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
