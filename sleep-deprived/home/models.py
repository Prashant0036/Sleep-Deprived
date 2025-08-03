from django.db import models
class GeneratedVideo(models.Model):
    subject = models.CharField(max_length=200)
    topic = models.CharField(max_length=200, unique=True) # Added unique=True potentially
    description = models.TextField()
    thumbnail = models.CharField(max_length=300)
    videoPath = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.topic
