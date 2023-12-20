from datetime import datetime
from typing import List
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from core.models import RoomResource, Event
from core.lib.exchange import create_exchange_event
from ninja.errors import HttpError

router = Router()

class EventSchema(Schema):
    id: int
    event_id: str
    organizer_name: str
    organizer_email: str
    subject: str
    start_time: datetime
    end_time: datetime

class EventInSchema(Schema):
    subject: str
    start_time: datetime
    end_time: datetime


@router.get('/{resource_email}', response=List[EventSchema])
def get_events(request, resource_email: str):
    room_resource = get_object_or_404(RoomResource, deleted_at__isnull=True, email=resource_email)
    events = Event.objects.filter(room_resource=room_resource, start_time__date=datetime.today(), deleted_at__isnull=True).order_by('start_time')
    return events

@router.post('/{resource_email}', response=EventSchema)
def create_event(request, payload: EventInSchema, resource_email: str):
    room_resource = get_object_or_404(RoomResource, deleted_at__isnull=True, email=resource_email)

    if payload.start_time > payload.end_time:
        raise HttpError(400, 'Invalid parameters')

    # Verify that there isn't any overlap with existing events
    event_conflicts = Event.objects.filter(
                                    Q(start_time__range=[payload.start_time, payload.end_time])
                                    | Q(end_time__range=[payload.start_time, payload.end_time])
                                    | (Q(start_time__lte=payload.start_time) & Q(end_time__gte=payload.end_time)),
                                    room_resource=room_resource, deleted_at__isnull=True,
                                )
    
    if event_conflicts.count() > 0:
        raise HttpError(400, 'Could not book meeting for the selected time')
    
    # Create the event in Exchange
    payload_dict = payload.dict()
    response = create_exchange_event(payload_dict, room_resource)

    event = Event.objects.create(event_id=response['id'], 
                  room_resource=room_resource,
                  organizer_name='ad-hoc',
                  organizer_email='adhoc@karbasi.dev',
                  **payload_dict)
    
    return event

    