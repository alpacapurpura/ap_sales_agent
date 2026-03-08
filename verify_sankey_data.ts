
import { MOCK_CONFIG } from './frontend/src/features/marketing-studio/components/strategy-canvas/config/mock-data';
import { adaptStrategyToVisx } from './frontend/src/features/marketing-studio/components/strategy-canvas/utils/adapter';

console.log("--- Starting Verification ---");

// 1. Generate Data
const data = adaptStrategyToVisx(MOCK_CONFIG);

console.log(`Nodes count: ${data.nodes.length}`);
console.log(`Links count: ${data.links.length}`);

// 2. Check Nodes
data.nodes.forEach((node, i) => {
    if (typeof node !== 'object') console.error(`Node ${i} is not an object`);
    // D3 Sankey requires nodes to be objects.
});

// 3. Check Links
data.links.forEach((link, i) => {
    if (typeof link.source !== 'number') {
        console.error(`Link ${i} source is not a number:`, link.source);
    }
    if (typeof link.target !== 'number') {
        console.error(`Link ${i} target is not a number:`, link.target);
    }
    
    // Check bounds
    if (link.source < 0 || link.source >= data.nodes.length) {
        console.error(`Link ${i} source index ${link.source} out of bounds (0-${data.nodes.length-1})`);
    }
    if (link.target < 0 || link.target >= data.nodes.length) {
        console.error(`Link ${i} target index ${link.target} out of bounds (0-${data.nodes.length-1})`);
    }
});

console.log("--- Verification Complete ---");
