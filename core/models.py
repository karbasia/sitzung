from datetime import datetime
from django.db import models

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

class RoomResource(BaseModel):
    name = models.CharField(max_length=500, null=False)
    description = models.TextField(null=True, blank=True)
    email = models.CharField(max_length=500, null=False)
    

class Subscription(BaseModel):
    subscription_id = models.CharField(max_length=512)
    expiration_time = models.DateTimeField(null=False)
    room_resource = models.ForeignKey(RoomResource, 
                                        on_delete=models.CASCADE, 
                                        verbose_name="The associated resource",
                                        null=True,
                                        blank=True)
    
    def is_expired(self):
        return self.expiration_time <= datetime.now()

class Event(BaseModel):
    event_id = models.CharField(max_length=512, null=False)
    room_resource = models.ForeignKey(RoomResource, on_delete=models.CASCADE)
    organizer_name = models.CharField(max_length=1000, null=False)
    organizer_email = models.CharField(max_length=1000, null=False)
    subject = models.CharField(max_length=1000, null=False)
    start_time = models.DateTimeField(null=False)
    end_time = models.DateTimeField(null=False)
