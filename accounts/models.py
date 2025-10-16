from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(default='defaul.png', upload_to='profile_pics')
    health_info = models.TextField(blank=True, null=True) 
    allergies = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f'{self.user.username} Profile'