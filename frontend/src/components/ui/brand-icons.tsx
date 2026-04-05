import {
  SiFacebook,
  SiMeta,
  SiInstagram,
  SiWhatsapp,
  SiYoutube,
  SiTiktok,
  SiGoogle,
  SiTelegram,
  SiShopify,
} from 'react-icons/si';

import { FaLinkedin } from 'react-icons/fa';

// For ManyChat, since there's no official SVG in simple-icons, we provide a clean, distinct chat-based SVG path
// that represents an automated agent/bot chat bubble.
const ManyChatIcon = ({ className }: { className?: string }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 24 24" 
    fill="currentColor" 
    className={className}
  >
    <path d="M12 2C6.477 2 2 6.03 2 11c0 2.84 1.484 5.372 3.79 7.025V22l3.65-2.05A10.873 10.873 0 0012 20c5.523 0 10-4.03 10-9s-4.477-9-10-9zm-2 10H8V9h2v3zm6 0h-2V9h2v3z" />
  </svg>
);

const MailerLiteIcon = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
  </svg>
);

export const BrandIcon = ({ name, className = "w-5 h-5" }: { name: string; className?: string }) => {
  const normalizedValue = name.toLowerCase();

  if (normalizedValue.includes('facebook') || normalizedValue === 'fb') return <SiFacebook className={className} />;
  if (normalizedValue.includes('meta')) return <SiMeta className={className} />;
  if (normalizedValue.includes('instagram') || normalizedValue === 'ig') return <SiInstagram className={className} />;
  if (normalizedValue.includes('whatsapp') || normalizedValue === 'wa') return <SiWhatsapp className={className} />;
  if (normalizedValue.includes('youtube') || normalizedValue === 'yt') return <SiYoutube className={className} />;
  if (normalizedValue.includes('tiktok')) return <SiTiktok className={className} />;
  if (normalizedValue.includes('linkedin')) return <FaLinkedin className={className} />;
  if (normalizedValue.includes('google') || normalizedValue === 'ga4') return <SiGoogle className={className} />;
  if (normalizedValue.includes('manychat')) return <ManyChatIcon className={className} />;
  if (normalizedValue.includes('telegram')) return <SiTelegram className={className} />;
  if (normalizedValue.includes('shopify')) return <SiShopify className={className} />;
  if (normalizedValue.includes('mailerlite')) return <MailerLiteIcon className={className} />;

  // Default fallback if a brand is requested but not found
  return null;
};
