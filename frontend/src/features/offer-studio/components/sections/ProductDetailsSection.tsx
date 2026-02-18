"use client";

import { SectionProps } from "../../types/section";
import { ProductDetailsForm } from "../forms/product-form";

export function ProductDetailsSection({ form }: SectionProps) {
  return <ProductDetailsForm form={form} />;
}
