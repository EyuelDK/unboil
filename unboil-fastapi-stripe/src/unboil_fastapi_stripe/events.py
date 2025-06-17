import stripe
from unboil_utils_fastapi import RouteEvent

class Events:
    
    def __init__(self):
        self.on_event_received = RouteEvent[stripe.Event]()
        self.on_subscription_created = RouteEvent[stripe.Subscription]()
        self.on_subscription_updated = RouteEvent[stripe.Subscription]()
        self.on_subscription_deleted = RouteEvent[stripe.Subscription]()