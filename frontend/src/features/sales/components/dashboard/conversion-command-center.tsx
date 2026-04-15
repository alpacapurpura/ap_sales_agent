import React from "react";

import { AgendaLane } from "./lanes/agenda-lane";
import { OpportunityLane } from "./lanes/opportunity-lane";
import { SalesLane } from "./lanes/sales-lane";

export const ConversionCommandCenter = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full min-h-[600px]">
      <OpportunityLane />
      <AgendaLane />
      <SalesLane />
    </div>
  );
};
