import type { Meta, StoryObj } from '@storybook/nextjs-vite';

const meta = {
  title: 'Tokens/Design Tokens',
  tags: ['autodocs'],
} satisfies Meta;

export default meta;
type Story = StoryObj;

const colorTokens = [
  'background', 'foreground',
  'card', 'card-foreground',
  'popover', 'popover-foreground',
  'primary', 'primary-foreground',
  'secondary', 'secondary-foreground',
  'muted', 'muted-foreground',
  'accent', 'accent-foreground',
  'destructive', 'destructive-foreground',
  'border', 'input', 'ring',
  'sidebar-background', 'sidebar-foreground',
  'sidebar-primary', 'sidebar-primary-foreground',
  'sidebar-accent', 'sidebar-accent-foreground',
  'sidebar-border', 'sidebar-ring',
];

const typographySizes = [
  { class: 'text-xs', label: 'text-xs (12px)' },
  { class: 'text-sm', label: 'text-sm (14px)' },
  { class: 'text-base', label: 'text-base (16px)' },
  { class: 'text-lg', label: 'text-lg (18px)' },
  { class: 'text-xl', label: 'text-xl (20px)' },
  { class: 'text-2xl', label: 'text-2xl (24px)' },
  { class: 'text-3xl', label: 'text-3xl (30px)' },
];

const spacingValues = [
  { rem: '1rem', px: '16px' },
  { rem: '2rem', px: '32px' },
  { rem: '4rem', px: '64px' },
  { rem: '8rem', px: '128px' },
];

const radiusValues = [
  { class: 'rounded-sm', label: 'rounded-sm' },
  { class: 'rounded-md', label: 'rounded-md' },
  { class: 'rounded-lg', label: 'rounded-lg' },
  { class: 'rounded-xl', label: 'rounded-xl' },
  { class: 'rounded-full', label: 'rounded-full' },
];

export const Default: Story = {
  render: () => (
    <div className="space-y-12 p-6">
      {/* Colors */}
      <section>
        <h2 className="text-2xl font-bold mb-6">Colors</h2>
        <div className="grid grid-cols-1 gap-3">
          {colorTokens.map((token) => (
            <div key={token} className="flex items-center gap-4">
              <div
                className="w-12 h-12 rounded-md border border-border shrink-0"
                style={{ backgroundColor: `hsl(var(--${token}))` }}
              />
              <div className="flex flex-col">
                <span className="text-sm font-medium">{token}</span>
                <span className="text-xs text-muted-foreground font-mono">--{token}</span>
                <span className="text-xs text-muted-foreground">
                  bg-{token} / text-{token}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Typography */}
      <section>
        <h2 className="text-2xl font-bold mb-6">Typography</h2>
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">font-sans (Geist)</h3>
          <div className="space-y-2">
            {typographySizes.map(({ class: cls, label }) => (
              <div key={cls} className="flex items-baseline gap-4">
                <span className="text-xs text-muted-foreground w-32 shrink-0 font-mono">{label}</span>
                <span className={`${cls} font-sans`}>The quick brown fox jumps over the lazy dog</span>
              </div>
            ))}
          </div>
          <h3 className="text-lg font-semibold mt-6">font-mono (Geist Mono)</h3>
          <div className="space-y-2">
            {typographySizes.map(({ class: cls, label }) => (
              <div key={`mono-${cls}`} className="flex items-baseline gap-4">
                <span className="text-xs text-muted-foreground w-32 shrink-0 font-mono">{label}</span>
                <span className={`${cls} font-mono`}>const x = 42;</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Spacing */}
      <section>
        <h2 className="text-2xl font-bold mb-6">Spacing</h2>
        <div className="space-y-3">
          {spacingValues.map(({ rem, px }) => (
            <div key={rem} className="flex items-center gap-4">
              <span className="text-xs text-muted-foreground w-24 shrink-0 font-mono">{rem} ({px})</span>
              <div
                className="h-8 bg-primary rounded"
                style={{ width: rem }}
              />
            </div>
          ))}
        </div>
      </section>

      {/* Border Radius */}
      <section>
        <h2 className="text-2xl font-bold mb-6">Border Radius</h2>
        <div className="flex gap-6 flex-wrap">
          {radiusValues.map(({ class: cls, label }) => (
            <div key={cls} className="flex flex-col items-center gap-2">
              <div className={`w-20 h-20 bg-primary/20 border-2 border-primary ${cls}`} />
              <span className="text-xs text-muted-foreground font-mono">{label}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  ),
};
