from django.db import models
from django.contrib.auth.models import User


class register(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=50)
    confirm_password = models.CharField(max_length=50)
    role = models.CharField(max_length=20, default='distributor')  # 'distributor' or 'retailer'

    def __str__(self):
        return f"{self.username} ({self.role})"
        

class adregister(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=50)
    confirm_password = models.CharField(max_length=50)
    role = models.CharField(max_length=20, default='admin')

    def __str__(self):
        return f"{self.username} (admin)"
    

class OTP(models.Model):
    user = models.ForeignKey(register, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.code}"
    

class AdminOTP(models.Model):
    user = models.ForeignKey(adregister, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.code}"


class SCNProduct(models.Model):
    distributor = models.ForeignKey(register, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, default='Industrial Components')
    sku = models.CharField(max_length=30, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=100)
    lead_time_hours = models.DecimalField(max_digits=5, decimal_places=1, default=4.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class SCNOrder(models.Model):
    STATUS_CHOICES = (
        ('Processing', 'Processing'),
        ('Dispatched', 'Dispatched'),
        ('In-Transit', 'In-Transit'),
        ('Delivered', 'Delivered'),
    )
    order_id = models.CharField(max_length=30, unique=True)
    retailer_name = models.CharField(max_length=100)
    retailer_email = models.EmailField()
    distributor = models.ForeignKey(register, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(SCNProduct, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Processing')
    ordered_at = models.DateTimeField(auto_now_add=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    latency_recorded_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.order_id} - {self.status}"


class SCNLatencyLog(models.Model):
    order = models.ForeignKey(SCNOrder, on_delete=models.CASCADE, related_name='logs')
    event = models.CharField(max_length=100)
    recorded_by = models.CharField(max_length=100)
    role = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)
    latency_benchmark = models.CharField(max_length=100, default='Node Latency < 0.1s')

    def __str__(self):
        return f"{self.order.order_id} - {self.event}"
