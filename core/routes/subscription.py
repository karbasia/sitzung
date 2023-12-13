from datetime import datetime
from typing import List
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from core.lib.exchange import decrypt_message, renew_subscription, create_subscription
from core.models import Subscription, Event, RoomResource

router = Router()

class SubSchema(Schema):
    value: List[dict]
    validationTokens: List[str]

class SubscriptionOut(Schema):
    subscription_id: str
    expiration_time: datetime

@router.post('/')
def execute_webhook(request, payload: SubSchema = None, validationToken: str = None):
    # Respond to validation queries on subscription creation
    if validationToken:
        return HttpResponse(validationToken, content_type='text/plain')
    
    # Handle the event
    event_dict = payload.value[0]

    queryset = Subscription.objects.select_related('room_resource').filter(expiration_time__gt=datetime.now())
    subscription = get_object_or_404(queryset, subscription_id=event_dict['subscriptionId'])

    encrypted_content = event_dict['encryptedContent']
    data_obj = decrypt_message(encrypted_content['dataKey'], encrypted_content['dataSignature'], encrypted_content['data'])

    event = Event.objects.filter(event_id=event_dict['resourceData']['id'], deleted_at__isnull=True)

    if event_dict['changeType'] == 'deleted':
        event.update(deleted_at=datetime.now())
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
        
        # If we create an event from our app, then we shouldn't create it again from the subscription
        if event_dict['changeType'] == 'created' and event.count() == 0:
            Event.objects.create(room_resource=subscription.room_resource, **event_obj)
        else:
            event.update(**event_obj)

    return None

@router.post('/verify/{resource_email}', response=SubscriptionOut)
def verify_subscription(request, resource_email: str):
    room_resource = get_object_or_404(RoomResource, deleted_at__isnull=True, email=resource_email)

    subscription = Subscription.objects.filter(room_resource=room_resource, expiration_time__gt=datetime.now(), deleted_at__isnull=True).first()
    if subscription:
        # refresh subscription
        expiration_time = renew_subscription(subscription.subscription_id)
        if expiration_time:
            subscription.expiration_time = expiration_time
            subscription.save()
    else:
        # create subscription
        subscription_details = create_subscription(room_resource.email)
        subscription = Subscription(room_resource=room_resource, **subscription_details)
        subscription.save()

    return subscription
