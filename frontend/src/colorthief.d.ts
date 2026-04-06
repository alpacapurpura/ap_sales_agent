// Override colorthief types — v2.7.0 package.json "types" field incorrectly
// points to color-thief-node.d.ts (function exports) instead of
// color-thief.d.ts (class export used in browser environments).
declare module "colorthief" {
  type RGBColor = [number, number, number];

  class ColorThief {
    getColor(
      sourceImage: HTMLImageElement | HTMLCanvasElement,
      quality?: number,
    ): RGBColor | null;
    getPalette(
      sourceImage: HTMLImageElement | HTMLCanvasElement,
      colorCount?: number,
      quality?: number,
    ): RGBColor[] | null;
  }

  export default ColorThief;
}
