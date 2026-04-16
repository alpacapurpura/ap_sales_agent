"use client";

import { ParentSize } from "@visx/responsive";
import { Sankey } from "@visx/sankey";
import { sankeyJustify } from "d3-sankey";
import React, { useState } from "react";

import { ActionDetailsDrawer } from "./drawer/ActionDetailsDrawer";
import { BaseLink } from "./links/BaseLink";
import { NodeFactory } from "./nodes/NodeFactory";
import { adaptStrategyToVisx } from "./utils/adapter";

import type { StrategyCanvasConfig, MarketingNode, MarketingActionLink } from "./config/types";
import type { SankeyGraph } from "@visx/sankey";

interface StrategyCanvasProps {
  config: StrategyCanvasConfig;
}

export const StrategyCanvas: React.FC<StrategyCanvasProps> = ({ config }) => {
  const data = adaptStrategyToVisx(config);
  const [selectedLink, setSelectedLink] = useState<MarketingActionLink | null>(null);

  return (
    <div className="w-full h-full min-h-[600px] bg-slate-50 rounded-xl border border-slate-200 shadow-sm p-6 overflow-hidden relative flex flex-col">
      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        <div className="min-w-[1600px] h-full relative">
          <ParentSize>
            {({ width, height }) => {
              if (width < 100 || height < 100) {
                return (
                  <div className="p-4 text-xs text-gray-400">
                    Waiting for dimensions... ({width}x{height})
                  </div>
                );
              }

              if (!data?.nodes || data.nodes.length === 0) {
                return (
                  <div className="flex items-center justify-center h-full">No data available</div>
                );
              }

              return (
                <Sankey
                  root={data as unknown as SankeyGraph<MarketingNode, MarketingActionLink>}
                  nodeWidth={24}
                  nodePadding={20}
                  extent={[
                    [0, 0],
                    [width, height],
                  ]}
                  nodeAlign={sankeyJustify}
                >
                  {({ graph, createPath }) => {
                    const links = graph?.links ?? [];
                    const nodes = graph?.nodes ?? [];

                    if (!nodes.length) {
                      return (
                        <div className="absolute inset-0 flex items-center justify-center text-red-500">
                          Error: Sankey layout failed to generate nodes.
                        </div>
                      );
                    }

                    return (
                      <svg width={width} height={height} className="overflow-visible">
                        <g style={{ mixBlendMode: "multiply" }}>
                          {links.map((link, i) => (
                            <BaseLink
                              key={`link-${i}`}
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any -- ReactFlow internal link type
                              link={link as any}
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any -- ReactFlow node ref
                              source={link.source as any}
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any -- ReactFlow node ref
                              target={link.target as any}
                              width={link.width ?? 1}
                              pathData={createPath(link) ?? ""}
                              onClick={() => {
                                setSelectedLink({
                                  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- ReactFlow extended link
                                  ...(link as any),
                                  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- custom ReactFlow prop
                                  source: (link as any).originalSource,
                                  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- custom ReactFlow prop
                                  target: (link as any).originalTarget,
                                });
                              }}
                            />
                          ))}
                        </g>
                        <g>
                          {nodes.map((node, i) => (
                            <NodeFactory
                              key={`node-${i}`}
                              // eslint-disable-next-line @typescript-eslint/no-explicit-any -- ReactFlow internal node type
                              node={node as any}
                              x={node.x0 ?? 0}
                              y={node.y0 ?? 0}
                              width={(node.x1 ?? 0) - (node.x0 ?? 0)}
                              height={(node.y1 ?? 0) - (node.y0 ?? 0)}
                            />
                          ))}
                        </g>
                      </svg>
                    );
                  }}
                </Sankey>
              );
            }}
          </ParentSize>
        </div>
      </div>
      <ActionDetailsDrawer
        isOpen={!!selectedLink}
        onClose={() => setSelectedLink(null)}
        link={selectedLink}
      />
    </div>
  );
};

