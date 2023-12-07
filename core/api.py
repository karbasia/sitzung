from ninja import NinjaAPI
from .routes.subscription import router as subscription_router

api = NinjaAPI()

api.add_router('/subscriptions/', subscription_router)