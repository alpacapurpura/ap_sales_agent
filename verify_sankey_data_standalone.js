
console.log("--- Starting Self-Contained Verification ---");

// --- Mock Data ---
const STRATEGY_NODES = [
  { id: 'node-0', order: 0 },
  { id: 'node-1', order: 1 },
  { id: 'node-2', order: 2 },
  { id: 'node-3', order: 3 },
  { id: 'node-4', order: 4 },
  { id: 'node-5', order: 5 },
  { id: 'node-6', order: 6 },
  { id: 'node-7', order: 7 }
];

const STRATEGY_LINKS = [
  { source: 'node-0', target: 'node-1' },
  { source: 'node-0', target: 'node-1' },
  { source: 'node-0', target: 'node-1' },
  { source: 'node-1', target: 'node-2' },
  { source: 'node-1', target: 'node-2' },
  { source: 'node-2', target: 'node-3' },
  { source: 'node-3', target: 'node-4' },
  { source: 'node-1', target: 'node-4' },
  { source: 'node-4', target: 'node-5' },
  { source: 'node-5', target: 'node-6' },
  { source: 'node-6', target: 'node-7' }
];

const MOCK_CONFIG = {
  nodes: STRATEGY_NODES,
  links: STRATEGY_LINKS
};

// --- Adapter Function (Copied from source) ---
const adaptStrategyToVisx = (config) => {
  if (!config || !config.nodes) {
    return { nodes: [], links: [] };
  }

  // 1. Sort nodes by order (Deep copy)
  const sortedNodes = config.nodes.map(node => ({ ...node })).sort((a, b) => (a.order || 0) - (b.order || 0));

  // 2. Create a map of ID -> Index
  const nodeIndexMap = new Map();
  sortedNodes.forEach((node, index) => {
    nodeIndexMap.set(node.id, index);
  });

  // 3. Map links
  const mappedLinks = (config.links || [])
    .filter(link => nodeIndexMap.has(link.source) && nodeIndexMap.has(link.target))
    .map(link => ({
      ...link,
      source: nodeIndexMap.get(link.source),
      target: nodeIndexMap.get(link.target),
      originalSource: link.source,
      originalTarget: link.target,
    }));

  return {
    nodes: sortedNodes,
    links: mappedLinks,
  };
};

// --- Verification Logic ---

// 1. First Pass
console.log("Running Adapter (Pass 1)...");
const data1 = adaptStrategyToVisx(MOCK_CONFIG);
console.log("Pass 1 Result:", JSON.stringify(data1, null, 2));

// Check integrity
if (data1.nodes.length !== 8) console.error("FAIL: Expected 8 nodes");
if (data1.links.length !== 11) console.error("FAIL: Expected 11 links");

data1.links.forEach((link, i) => {
    if (typeof link.source !== 'number') console.error(`FAIL: Link ${i} source is not number:`, link.source);
    if (typeof link.target !== 'number') console.error(`FAIL: Link ${i} target is not number:`, link.target);
});

// 2. Simulate D3 Mutation (The destructive part)
console.log("Simulating D3 Mutation on Pass 1 data...");
// D3 replaces numeric indices with object references
data1.links.forEach(link => {
    link.source = data1.nodes[link.source];
    link.target = data1.nodes[link.target];
});
console.log("Data mutated. Source is now:", typeof data1.links[0].source); // Should be 'object'

// 3. Second Pass (Simulating Re-render)
console.log("Running Adapter (Pass 2) with SAME config...");
// Crucial: Does adaptStrategyToVisx return fresh numeric indices even if previous output was mutated?
// It should, because it reads from MOCK_CONFIG which we hope wasn't mutated.
const data2 = adaptStrategyToVisx(MOCK_CONFIG);

// Verify Pass 2
let pass2Safe = true;
data2.links.forEach((link, i) => {
    if (typeof link.source !== 'number') {
        console.error(`FAIL (Pass 2): Link ${i} source is NOT a number. It is:`, typeof link.source);
        pass2Safe = false;
    }
});

if (pass2Safe) {
    console.log("SUCCESS: Adapter returns fresh numeric indices on second pass.");
} else {
    console.error("FAILURE: Adapter output is contaminated.");
}

console.log("--- Verification End ---");
