from datetime import datetime
from typing import List
from django.db.models import Prefetch
from ninja import Router, Schema
from ninja.errors import HttpError
from core.models import RoomResource, Event
from .event import EventOut

router = Router()

class ResourceSchema(Schema):
    id: int
    name: str
    description: str
    email: str
    event_set: List[EventOut] = None


@router.get('/{resource_email}', response=ResourceSchema)
def get_resource_detauks(request, resource_email: str):
    room_resource = RoomResource.objects.filter(
        email=resource_email, 
        deleted_at__isnull=True
    ).prefetch_related(
        Prefetch(
            "event_set", 
            queryset=Event.objects.filter(deleted_at__isnull=True, start_time__date=datetime.today())
        )
    )

    if room_resource.count() == 0:
        raise HttpError(404, 'Resource not found')
    
    return room_resource.first()