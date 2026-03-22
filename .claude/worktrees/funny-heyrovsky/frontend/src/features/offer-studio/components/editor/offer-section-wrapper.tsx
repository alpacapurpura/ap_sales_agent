import React from "react";
import { OfferSection } from "./offer-section/offer-section";

interface OfferSectionWrapperProps {
  id: string;
  title: string;
  description?: string;
  quote?: string;
  actionLabel?: string;
  icon: any;
  isEmpty: boolean;
  onEdit: () => void;
  children: React.ReactNode;
}

export function OfferSectionWrapper({
  id,
  title,
  description,
  quote,
  actionLabel,
  icon,
  isEmpty,
  onEdit,
  children
}: OfferSectionWrapperProps) {
  return (
    <OfferSection id={id} onEdit={onEdit}>
      <OfferSection.Header title={title} icon={icon} description={description} />
      
      {isEmpty ? (
        <OfferSection.EmptyState quote={quote} actionLabel={actionLabel} />
      ) : (
        <OfferSection.Content>
          {children}
          <OfferSection.Controls />
        </OfferSection.Content>
      )}
    </OfferSection>
  );
}
