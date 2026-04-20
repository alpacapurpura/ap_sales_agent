/**
 *
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 *
 */
export function getLuminance(r: number, g: number, b: number): number {
  const a = [r, g, b].map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

/**
 *
 */
export function getContrastColor(hex: string): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return "#000000";
  const luminance = getLuminance(rgb.r, rgb.g, rgb.b);
  // Threshold can be adjusted. 0.5 is standard, 0.6 favors black text on mid-tones.
  return luminance > 0.5 ? "#000000" : "#ffffff";
}

/**
 *
 */
export function adjustBrightness(hex: string, percent: number): string {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;

  let { r, g, b } = rgb;

  r = Math.round(r * (1 + percent / 100));
  g = Math.round(g * (1 + percent / 100));
  b = Math.round(b * (1 + percent / 100));

  r = Math.min(255, Math.max(0, r));
  g = Math.min(255, Math.max(0, g));
  b = Math.min(255, Math.max(0, b));

  const toHex = (n: number) => {
    const h = n.toString(16);
    return h.length === 1 ? `0${h}` : h;
  };

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 *
 */
export function hexToHsl(hex: string): string {
  let r = 0,
    g = 0,
    b = 0;
  if (hex.length === 4) {
    r = parseInt(`0x${hex[1]}${hex[1]}`);
    g = parseInt(`0x${hex[2]}${hex[2]}`);
    b = parseInt(`0x${hex[3]}${hex[3]}`);
  } else if (hex.length === 7) {
    r = parseInt(`0x${hex[1]}${hex[2]}`);
    g = parseInt(`0x${hex[3]}${hex[4]}`);
    b = parseInt(`0x${hex[5]}${hex[6]}`);
  }
  r /= 255;
  g /= 255;
  b /= 255;
  const cmin = Math.min(r, g, b),
    cmax = Math.max(r, g, b),
    delta = cmax - cmin;
  let h = 0,
    s = 0,
    l = 0;

  if (delta === 0) h = 0;
  else if (cmax === r) h = ((g - b) / delta) % 6;
  else if (cmax === g) h = (b - r) / delta + 2;
  else h = (r - g) / delta + 4;

  h = Math.round(h * 60);
  if (h < 0) h += 360;

  l = (cmax + cmin) / 2;
  s = delta === 0 ? 0 : delta / (1 - Math.abs(2 * l - 1));
  s = +(s * 100).toFixed(1);
  l = +(l * 100).toFixed(1);

  return `${h} ${s}% ${l}%`;
}
