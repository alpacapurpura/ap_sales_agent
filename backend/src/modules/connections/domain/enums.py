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
    META = "meta" # Meta Ads / Facebook — master credential (user token)
    FACEBOOK_PAGE = "facebook_page"      # Per-page asset (has its own page_access_token)
    INSTAGRAM_ACCOUNT = "instagram_account"  # IG Business Account linked to a Page
    META_ADS_ACCOUNT = "meta_ads_account"    # Ad Account (uses user token for reads)
    META_PIXEL = "meta_pixel"              # Meta (Facebook) Pixel for conversion tracking
    WHATSAPP_BUSINESS_ACCOUNT = "whatsapp_business_account"  # WABA from Meta Business Manager
    YOUTUBE = "youtube"
    YOUTUBE_ANALYTICS = "youtube_analytics"

    # Calendar & Email
    GOOGLE_CALENDAR = "google_calendar"
    GMAIL = "gmail"
