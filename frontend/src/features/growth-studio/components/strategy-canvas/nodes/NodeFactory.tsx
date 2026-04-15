import { Group } from "@visx/group";
import React from "react";

import type { VisxNode } from "../utils/adapter";

// Props passed by Visx Sankey to the node component
export interface NodeFactoryProps {
  node: VisxNode;
  x: number;
  y: number;
  width: number;
  height: number;
}

const NodeFactory: React.FC<NodeFactoryProps> = ({ node, x, y, width, height }) => {
  const isPositiveTrend = node.efficiencyMetric.trend === "up";
  const isNegativeTrend = node.efficiencyMetric.trend === "down";

  const trendColor = isPositiveTrend
    ? "text-emerald-600"
    : isNegativeTrend
      ? "text-red-600"
      : "text-gray-500";

  return (
    <Group top={y} left={x}>
      {/* Node label rendered above the node */}
      <foreignObject x={0} y={-40} width={width} height={40}>
        <div className="flex flex-col items-center justify-end h-full text-center pb-1">
          <div className="font-bold text-xs truncate w-full text-gray-900" title={node.title}>
            {node.title}
          </div>
        </div>
      </foreignObject>

      {/* The node itself (just a colored bar now) */}
      <rect
        width={width}
        height={height}
        fill="#3b82f6" // Use a variable or theme color if needed
        fillOpacity={0.8}
        rx={4}
        className="cursor-pointer hover:fill-blue-600 transition-colors"
      />

      {/* Optional: Metrics tooltip or details on hover, but for now kept minimal */}
    </Group>
  );
};

export default NodeFactory;
