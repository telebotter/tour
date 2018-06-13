from django.db import models
from main.models import Tour

# Create your models here.
class User(models.Model):
    telegram_id = models.IntegerField(unique=True)
    name = models.CharField(null=True, blank=True, max_length=255)
    tour = models.ForeignKey(Tour, blank=True, null=True, on_delete=models.SET_NULL)
    tag = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_created=True, null=True)
    admin = models.BooleanField(default=False)

