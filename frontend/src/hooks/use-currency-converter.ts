import { useState, useEffect, useCallback } from "react";

const API_URL = "https://open.er-api.com/v6/latest";

interface ExchangeRates {
  [key: string]: number;
}

export function useCurrencyConverter(baseCurrency: string = "USD") {
  const [rates, setRates] = useState<ExchangeRates>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRates = async () => {
      try {
        // Check cache
        const cached = localStorage.getItem(`rates_${baseCurrency}`);
        if (cached) {
            const { timestamp, data } = JSON.parse(cached);
            // Cache valid for 1 hour
            if (Date.now() - timestamp < 3600000) {
                setRates(data);
                setLoading(false);
                return;
            }
        }

        const res = await fetch(`${API_URL}/${baseCurrency}`);
        if (!res.ok) throw new Error("Failed to fetch rates");
        const data = await res.json();
        
        setRates(data.rates);
        localStorage.setItem(`rates_${baseCurrency}`, JSON.stringify({
            timestamp: Date.now(),
            data: data.rates
        }));
        setLoading(false);
      } catch (err) {
        console.error(err);
        setError("Could not load exchange rates");
        setLoading(false);
      }
    };

    fetchRates();
  }, [baseCurrency]);

  const convert = useCallback((amount: number, from: string, to: string) => {
    if (from === to) return amount;
    // If we don't have rates yet, return original amount
    if (Object.keys(rates).length === 0) return amount;

    const rateFrom = rates[from]; 
    const rateTo = rates[to];     
    
    // If currencies are not in the list (e.g. unknown code), return original
    if (!rateFrom || !rateTo) return amount;
    
    // Convert to base then to target
    const inBase = amount / rateFrom;
    return inBase * rateTo;
  }, [rates]);

  return { rates, loading, error, convert };
}
