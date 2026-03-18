"use client";

import type { DesignToken } from "@/lib/design-system/types";

interface TokenShowcaseProps {
  tokens: DesignToken[];
}

function ColorSwatches({ tokens }: { tokens: DesignToken[] }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">Colors</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {tokens.map((token) => (
          <div key={token.name} className="border rounded-lg p-3 space-y-2">
            <div
              className="w-full h-12 rounded-md border"
              style={{ backgroundColor: token.value }}
            />
            <div>
              <p className="text-sm font-medium">{token.name}</p>
              {token.cssVar && (
                <p className="text-xs font-mono text-muted-foreground">{token.cssVar}</p>
              )}
              <p className="text-xs font-mono text-muted-foreground">{token.tailwindClass}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TypographyScale({ tokens }: { tokens: DesignToken[] }) {
  const sizes = tokens.filter((t) => t.name.startsWith("Text"));
  const weights = tokens.filter((t) => t.name.startsWith("Font"));

  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">Typography</h3>
      <div className="space-y-4">
        <div className="border rounded-lg p-4 space-y-3">
          <p className="text-sm font-medium text-muted-foreground mb-2">Size Scale</p>
          {sizes.map((token) => (
            <div key={token.name} className="flex items-baseline gap-4">
              <span className="w-20 text-xs font-mono text-muted-foreground shrink-0">
                {token.tailwindClass}
              </span>
              <span className={token.tailwindClass}>
                The quick brown fox jumps over the lazy dog
              </span>
              <span className="text-xs text-muted-foreground shrink-0">{token.value}</span>
            </div>
          ))}
        </div>
        <div className="border rounded-lg p-4 space-y-2">
          <p className="text-sm font-medium text-muted-foreground mb-2">Weight Scale</p>
          {weights.map((token) => (
            <div key={token.name} className="flex items-baseline gap-4">
              <span className="w-28 text-xs font-mono text-muted-foreground shrink-0">
                {token.tailwindClass}
              </span>
              <span className={token.tailwindClass}>
                {token.name} ({token.value})
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SpacingScale({ tokens }: { tokens: DesignToken[] }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">Spacing</h3>
      <div className="border rounded-lg p-4 space-y-3">
        {tokens.map((token) => (
          <div key={token.name} className="flex items-center gap-4">
            <span className="w-16 text-xs font-mono text-muted-foreground shrink-0">
              {token.tailwindClass}
            </span>
            <div
              className="h-4 bg-primary/60 rounded-sm"
              style={{ width: token.value.split("(")[0].trim() }}
            />
            <span className="text-xs text-muted-foreground">{token.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function RadiusShowcase({ tokens }: { tokens: DesignToken[] }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">Border Radius</h3>
      <div className="flex flex-wrap gap-4">
        {tokens.map((token) => (
          <div key={token.name} className="text-center space-y-2">
            <div
              className={`w-16 h-16 bg-primary/20 border-2 border-primary/40 ${token.tailwindClass}`}
            />
            <p className="text-xs font-mono text-muted-foreground">{token.tailwindClass}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ShadowShowcase({ tokens }: { tokens: DesignToken[] }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-3">Shadows</h3>
      <div className="flex flex-wrap gap-6">
        {tokens.map((token) => (
          <div key={token.name} className="text-center space-y-2">
            <div
              className={`w-24 h-24 bg-card rounded-lg border ${token.tailwindClass}`}
            />
            <p className="text-xs font-mono text-muted-foreground">{token.tailwindClass}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function TokenShowcase({ tokens }: TokenShowcaseProps) {
  const colors = tokens.filter((t) => t.category === "color");
  const typography = tokens.filter((t) => t.category === "typography");
  const spacing = tokens.filter((t) => t.category === "spacing");
  const radius = tokens.filter((t) => t.category === "radius");
  const shadows = tokens.filter((t) => t.category === "shadow");

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-1">Design Tokens</h2>
        <p className="text-muted-foreground text-sm mb-6">
          Foundation layer: colors, typography, spacing, radii, and shadows extracted from
          globals.css and Tailwind defaults.
        </p>
      </div>
      <ColorSwatches tokens={colors} />
      <TypographyScale tokens={typography} />
      <SpacingScale tokens={spacing} />
      <RadiusShowcase tokens={radius} />
      <ShadowShowcase tokens={shadows} />
    </div>
  );
}
