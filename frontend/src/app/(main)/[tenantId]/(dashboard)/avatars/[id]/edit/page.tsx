import { AvatarEditPage } from "@/features/brand-studio/pages/AvatarEditPage";

/**
 * Avatar edit route — kept live so external links (offer-studio's
 * OfferContextPanel) continue to resolve. Delegates to the brand-studio
 * stub until the real avatar edit UX lands (next persona iteration).
 */
export default function EditAvatarPage() {
  return <AvatarEditPage />;
}
