import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "./schema";

export interface SectionProps {
  form: UseFormReturn<OfferFormValues>;
  className?: string;
}
