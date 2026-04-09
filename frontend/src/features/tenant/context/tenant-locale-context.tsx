'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useAuth } from '@clerk/nextjs';
import { settingsApi } from '@/lib/api/settings';

export interface TenantLocale {
  currency: string;
  timezone: string;
}

const DEFAULT_LOCALE: TenantLocale = {
  currency: 'USD',
  timezone: 'UTC',
};

const TenantLocaleContext = createContext<TenantLocale>(DEFAULT_LOCALE);

interface TenantLocaleProviderProps {
  children: ReactNode;
  initialLocale?: TenantLocale;
}

export function TenantLocaleProvider({
  children,
  initialLocale,
}: TenantLocaleProviderProps) {
  const [locale, setLocale] = useState<TenantLocale>(
    initialLocale ?? DEFAULT_LOCALE,
  );
  const { getToken } = useAuth();

  useEffect(() => {
    if (initialLocale) return;

    let cancelled = false;

    async function load() {
      try {
        const token = await getToken();
        if (!token || cancelled) return;

        const settings = await settingsApi.getGeneralSettings(token);
        if (!cancelled) {
          setLocale({
            currency: settings.default_currency || 'USD',
            timezone: settings.timezone || 'UTC',
          });
        }
      } catch {
        // Keep defaults on error
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [getToken, initialLocale]);

  return (
    <TenantLocaleContext.Provider value={locale}>
      {children}
    </TenantLocaleContext.Provider>
  );
}

export function useTenantLocale(): TenantLocale {
  return useContext(TenantLocaleContext);
}
