import type { OfferFormValues } from "./schema";
import type { UseFormReturn } from "react-hook-form";

export interface SectionProps {
  form: UseFormReturn<OfferFormValues>;
  className?: string;
}
