import React from "react";

import { AgendaLane } from "./lanes/AgendaLane";
import { OpportunityLane } from "./lanes/OpportunityLane";
import { SalesLane } from "./lanes/SalesLane";

export const ConversionCommandCenter = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full min-h-[600px]">
      <OpportunityLane />
      <AgendaLane />
      <SalesLane />
    </div>
  );
};
