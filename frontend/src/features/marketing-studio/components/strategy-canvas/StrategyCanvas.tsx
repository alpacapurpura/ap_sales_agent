"use client";

import React, { useEffect, useState } from 'react';
import { Sankey } from '@visx/sankey';
import { ParentSize } from '@visx/responsive';
import { sankeyJustify } from 'd3-sankey';
import { StrategyCanvasConfig, MarketingActionLink } from './config/types';
import { adaptStrategyToVisx } from './utils/adapter';
import NodeFactory from './nodes/NodeFactory';
import BaseLink from './links/BaseLink';
import ActionDetailsDrawer from './drawer/ActionDetailsDrawer';

interface StrategyCanvasProps {
  config: StrategyCanvasConfig;
}

const StrategyCanvas: React.FC<StrategyCanvasProps> = ({ config }) => {
  const data = adaptStrategyToVisx(config);
  const [selectedLink, setSelectedLink] = useState<MarketingActionLink | null>(null);

  useEffect(() => {
    console.log('[StrategyCanvas] input', {
      nodes: data.nodes.length,
      links: data.links.length,
      firstNode: data.nodes[0]?.id,
      firstLink: data.links[0] ? { source: data.links[0].source, target: data.links[0].target, value: data.links[0].value } : null,
    });
  }, [data]);

  return (
    <div className="w-full h-full min-h-[600px] bg-slate-50 rounded-xl border border-slate-200 shadow-sm p-6 overflow-hidden relative flex flex-col">
      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        <div className="min-w-[1600px] h-full relative">
          <ParentSize>
            {({ width, height }) => {
              if (width < 100 || height < 100) {
                return <div className="p-4 text-xs text-gray-400">Waiting for dimensions... ({width}x{height})</div>;
              }

              if (!data || !data.nodes || data.nodes.length === 0) {
                return <div className="flex items-center justify-center h-full">No data available</div>;
              }

              return (
                <Sankey
                  root={data}
                  nodeWidth={24}
                  nodePadding={20}
                  extent={[[0, 0], [width, height]]}
                  nodeAlign={sankeyJustify}
                >
                  {({ graph, createPath }) => {
                    const links = graph?.links ?? [];
                    const nodes = graph?.nodes ?? [];

                    console.log('[StrategyCanvas] layout', {
                      width,
                      height,
                      nodes: nodes.length,
                      links: links.length,
                    });

                    if (!nodes.length) {
                      return (
                        <div className="absolute inset-0 flex items-center justify-center text-red-500">
                          Error: Sankey layout failed to generate nodes.
                        </div>
                      );
                    }

                    return (
                      <svg width={width} height={height} className="overflow-visible">
                        <g style={{ mixBlendMode: 'multiply' }}>
                          {links.map((link, i) => (
                            <BaseLink
                              key={`link-${i}`}
                              link={link as any}
                              source={link.source as any}
                              target={link.target as any}
                              width={link.width ?? 1}
                              pathData={createPath(link) ?? ''}
                              onClick={() => {
                                setSelectedLink({
                                  ...(link as any),
                                  source: (link as any).originalSource,
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

export default StrategyCanvas;
