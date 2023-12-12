from ninja import NinjaAPI
from .routes.subscription import router as subscription_router
from .routes.event import router as event_router

api = NinjaAPI()

api.add_router('/subscriptions/', subscription_router)
api.add_router('/events/', event_router)