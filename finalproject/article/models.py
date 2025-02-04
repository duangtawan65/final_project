from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from healmind.models import DoctorProfile  # Import จาก healmind app

class Article(models.Model):
    title = models.CharField(max_length=200)
    cover_image = models.ImageField(upload_to='articles/covers/')
    description = models.TextField()
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_author_profile(self):
        return DoctorProfile.objects.get(user=self.author)

    def __str__(self):
        return self.title