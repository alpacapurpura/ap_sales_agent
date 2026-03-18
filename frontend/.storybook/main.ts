import type { StorybookConfig } from '@storybook/nextjs-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-themes',
    '@storybook/addon-a11y',
  ],
  framework: '@storybook/nextjs-vite',
  staticDirs: ['../public'],
};

export default config;
