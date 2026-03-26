import { SankeyLink, SankeyNode } from '@visx/sankey';
import { StrategyCanvasConfig, MarketingNode, MarketingActionLink } from '../config/types';

// Extended types for Visx compatibility
export interface VisxNode extends MarketingNode, SankeyNode<MarketingNode, MarketingActionLink> {
  index?: number;
}

// VisxLink represents links in their pre-d3 form (source/target as numeric indices)
// We omit conflicting fields from both base types and add them back explicitly
export interface VisxLink extends Omit<MarketingActionLink, 'source' | 'target'>, Omit<SankeyLink<MarketingNode, MarketingActionLink>, 'source' | 'target'> {
  source: number;
  target: number;
  originalSource: string;
  originalTarget: string;
}

export interface VisxGraphData {
  nodes: VisxNode[];
  links: VisxLink[];
}

/**
 * Transforms StrategyCanvasConfig into Visx Sankey Graph format.
 * - Sorts nodes by 'order'.
 * - Maps string IDs to array indices for links.
 */
export const adaptStrategyToVisx = (config: StrategyCanvasConfig): VisxGraphData => {
  if (!config || !config.nodes) {
    return { nodes: [], links: [] };
  }

  // 1. Sort nodes by order (Deep copy to avoid mutation by d3-sankey)
  const sortedNodes = config.nodes.map(node => ({ ...node })).sort((a, b) => (a.order || 0) - (b.order || 0));

  // 2. Create a map of ID -> Index
  const nodeIndexMap = new Map<string, number>();
  sortedNodes.forEach((node, index) => {
    nodeIndexMap.set(node.id, index);
  });

  // 3. Map links: replace string IDs with indices
  const mappedLinks: VisxLink[] = (config.links || [])
    .filter(link => nodeIndexMap.has(link.source) && nodeIndexMap.has(link.target))
    .map(link => ({
      ...link,
      // d3-sankey expects numbers initially, but will replace them with objects.
      // We must provide fresh objects to avoid mutation issues.
      source: nodeIndexMap.get(link.source)!,
      target: nodeIndexMap.get(link.target)!,
      originalSource: link.source,
      originalTarget: link.target,
    }));

  // IMPORTANT: d3-sankey requires specific sorting or graph structure.
  // If the graph is not a DAG (Directed Acyclic Graph), it might fail.
  // Visx Sankey documentation mentions: "The graph generator takes the same input sankey data as defined in d3-sankey."
  // D3 Sankey modifies nodes and links in place.
  // We need to ensure we return fresh objects.

  // NOTE: We cannot simply use [...nodes] because objects inside are references.
  // We must deep copy nodes and links.
  
  // Also, mappedLinks might have numeric indices for source/target, but after d3 runs, they become objects.
  // If we reuse the same array, subsequent runs will have objects in source/target,
  // but d3 expects numbers (or objects, but if objects, it expects them to be the NEW nodes).
  // Deep copy ensures we reset to the primitive state (numbers) if that's what we stored,
  // OR we are relying on d3 to handle objects if we pass them.
  // BUT: adaptStrategyToVisx creates the structure with numeric indices.
  // So a deep copy here returns an object where links have numeric indices.
  // This is what d3 wants for a fresh run.
  
  return {
    nodes: JSON.parse(JSON.stringify(sortedNodes)),
    links: JSON.parse(JSON.stringify(mappedLinks)),
  };
};
