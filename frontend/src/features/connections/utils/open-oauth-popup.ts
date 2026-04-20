interface OpenOAuthPopupOptions {
  url: string;
  name?: string;
  width?: number;
  height?: number;
}

/**
 *
 */
export function openOAuthPopup({
  url,
  name = "oauth-popup",
  width = 520,
  height = 640,
}: OpenOAuthPopupOptions): Window | null {
  const left = window.screen.width / 2 - width / 2;
  const top = window.screen.height / 2 - height / 2;

  return window.open(
    url,
    name,
    `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`,
  );
}
