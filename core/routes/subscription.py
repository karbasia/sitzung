from datetime import datetime
from typing import List
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from core.lib.exchange import decrypt_message
from core.models import Subscription, Event

router = Router()

class SubSchema(Schema):
    value: List[dict]
    validationTokens: List[str]

@router.post('/')
def create_validate_subscription(request, body: SubSchema, validationToken: str = None):

    # Respond to validation queries on subscription creation
    if validationToken:
        return HttpResponse(validationToken, content_type='text/plain')
    
    # Handle the event
    event_dict = body.value[0]

    queryset = Subscription.objects.select_related('room_resource').filter(expiration_time__gt=datetime.now())
    subscription = get_object_or_404(queryset, subscription_id=event_dict['subscriptionId'])

    encrypted_content = event_dict['encryptedContent']
    data_obj = decrypt_message(encrypted_content['dataKey'], encrypted_content['dataSignature'], encrypted_content['data'])

    if event_dict['changeType'] == 'deleted':
        Event.objects.filter(event_id=event_dict['resourceData']['id']).update(deleted_at=datetime.now())
    elif 'subject' in data_obj:
        # After a meeting is cancelled, update events with blank payloads are sent to the endpoint
        event_obj = {
            'event_id': event_dict['resourceData']['id'],
            'organizer_name': data_obj['organizer']['emailAddress']['name'],
            'organizer_email': data_obj['organizer']['emailAddress']['address'],
            'subject': data_obj['subject'],
            'start_time': data_obj['start']['dateTime'],
            'end_time': data_obj['end']['dateTime'],
        }
        
        if event_dict['changeType'] == 'created':
            Event.objects.create(room_resource=subscription.room_resource, **event_obj)
        else:
            Event.objects.filter(event_id=event_obj['event_id']).update(**event_obj)

    return None