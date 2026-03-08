# Strategy Canvas Spec

## Why
The "Strategy Canvas" is a critical visual tool for the Marketing Studio. It allows users to visualize their marketing funnel as a horizontal Sankey diagram, tracking the flow of users from "Universe" to "Evangelization". It provides insights into volume, efficiency (health), and financial impact at each stage.

## What Changes
- Create a new component `StrategyCanvas` within `frontend/src/features/marketing-studio`.
- Implement a **fixed-node** Sankey diagram using `@visx/sankey`.
- Implement dynamic edges (links) representing marketing actions/campaigns.
- Implement a slide-out drawer for detailed action metadata.
- Use **mock data** to simulate the backend response.

## Impact
- **New Feature**: Adds a visualization tool to the Marketing Studio.
- **Dependencies**: Adds `@visx/sankey`, `@visx/group`, `@visx/shape`, `@visx/responsive`, `@visx/gradient`, `@visx/tooltip`.
- **Codebase**: Adds new components in `frontend/src/features/marketing-studio/components/strategy-canvas`.

## ADDED Requirements

### Requirement: Sankey Visualization
The system SHALL render a horizontal Sankey diagram with 8 fixed nodes:
0. Universe
1. Acquisition
2. Activation
3. Nutrition
4. Conversion
5. Adoption
6. Expansion
7. Evangelization

#### Scenario: Rendering
- **WHEN** the component loads
- **THEN** it renders the 8 nodes in order.
- **AND** it renders edges connecting the nodes based on the mock configuration.
- **AND** edges have varying thickness based on volume.
- **AND** edges have varying colors/styles based on status (Potential/Gray/Dotted, Healthy/Solid, Bottleneck/Red/Pulse) and Channel Type.

### Requirement: Node Metadata
Each node SHALL display:
- Title
- Volume Metric (# of people)
- Efficiency Metric ($ or %)

### Requirement: Edge Interaction
The system SHALL allow users to interact with the edges.
- **WHEN** a user clicks an edge
- **THEN** a slide-out drawer opens displaying detailed metadata for that action (Campaign Name, Cost, Status, etc.).

### Requirement: Architecture Patterns
The implementation SHALL follow these patterns:
- **Server-Driven UI**: Topology defined by JSON configuration (mocked).
- **Inversion of Control**: Visual components decoupled from business logic via render props.
- **Component Registry**: Factory pattern for rendering different metric types.
- **Adapter Pattern**: Transform raw data into the format required by the visualization component.

## MODIFIED Requirements
N/A

## REMOVED Requirements
N/A
