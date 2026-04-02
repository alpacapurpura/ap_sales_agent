// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import nextConfig from "eslint-config-next";

/** @type {import("eslint").Linter.Config[]} */
export default [...nextConfig, {
  ignores: [".next/", "node_modules/", "storybook-static/"],
}, ...storybook.configs["flat/recommended"]];
