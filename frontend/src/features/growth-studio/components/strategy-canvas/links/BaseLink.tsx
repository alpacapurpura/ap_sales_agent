import React from "react";

import type { ChannelType } from "../config/types";
import type { VisxLink, VisxNode } from "../utils/adapter";

const CHANNEL_COLORS: Record<ChannelType, string> = {
  PAID_MEDIA: "#3b82f6", // blue-500
  ORGANIC_SEARCH: "#10b981", // green-500
  ORGANIC_SOCIAL: "#f59e0b", // amber-500
  OWNED_MEDIA: "#8b5cf6", // violet-500
  SALES_TEAM: "#ef4444", // red-500
  PARTNERS: "#ec4899", // pink-500
};

export interface BaseLinkProps {
  link: VisxLink;
  source: VisxNode;
  target: VisxNode;
  width: number;
  pathData: string;
  onClick?: () => void;
}

export const BaseLink: React.FC<BaseLinkProps> = ({
  link,
  source,
  target,
  width,
  pathData,
  onClick,
}) => {
  const { channelType, status } = link;

  // Determine color
  let fill = CHANNEL_COLORS[channelType] || "#9ca3af";
  if (status === "BOTTLENECK") {
    fill = "#dc2626";
  }

  const opacity = status === "POTENTIAL" ? 0.3 : 0.6;
  const className = status === "BOTTLENECK" ? "animate-pulse" : "";

  return (
    <path
      d={pathData}
      fill={fill}
      fillOpacity={opacity}
      stroke="none"
      onClick={onClick}
      className={`transition-all duration-300 hover:fill-opacity-80 cursor-pointer ${className}`}
      style={{
        mixBlendMode: "multiply", // Helps when flows overlap visually
      }}
    >
      <title>{`${source.title} → ${target.title}: ${link.label} (${link.value})`}</title>
    </path>
  );
};
