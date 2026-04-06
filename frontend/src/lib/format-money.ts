/**
 * Centralized currency formatting utilities.
 * Uses Intl.NumberFormat for proper locale-aware symbol resolution.
 * Single source of truth -- replaces ~12 broken implementations across the codebase.
 */

export function formatMoney(
  amount: number,
  currency: string,
  options?: {
    compact?: boolean;
    fractionDigits?: number;
    locale?: string;
  },
): string {
  const locale = options?.locale ?? 'en-US';

  const formatOptions: Intl.NumberFormatOptions = {
    style: 'currency',
    currency,
  };

  if (options?.compact) {
    formatOptions.notation = 'compact';
    formatOptions.maximumFractionDigits = 1;
  } else if (options?.fractionDigits !== undefined) {
    formatOptions.minimumFractionDigits = options.fractionDigits;
    formatOptions.maximumFractionDigits = options.fractionDigits;
  }

  return new Intl.NumberFormat(locale, formatOptions).format(amount);
}

export function formatDualCurrency(
  amount: number,
  currency: string,
  usdAmount: number | null | undefined,
  options?: { compact?: boolean },
): string {
  const main = formatMoney(amount, currency, {
    fractionDigits: 0,
    ...options,
  });

  if (currency === 'USD') return main;

  if (usdAmount != null) {
    const usdFormatted = formatMoney(usdAmount, 'USD', {
      fractionDigits: 0,
      locale: 'en-US',
      ...options,
    });
    return `${main} (~${usdFormatted} USD)`;
  }

  return main;
}
