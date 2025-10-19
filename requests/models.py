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

    def __str__(self):
        return f"Report for {self.request.name}"
