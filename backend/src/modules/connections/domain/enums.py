from enum import Enum

class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp" # Evolution / QR
    WHATSAPP_CLOUD = "whatsapp_cloud" # Meta Cloud API
    MANYCHAT = "manychat"
    
    # Marketing & E-commerce
    SHOPIFY = "shopify"
    MAILERLITE = "mailerlite"
    GOOGLE_ANALYTICS = "google_analytics"
    META = "meta" # Meta Ads / Facebook
    YOUTUBE = "youtube"
    
    # Calendar & Email
    GOOGLE_CALENDAR = "google_calendar"
    GMAIL = "gmail"
