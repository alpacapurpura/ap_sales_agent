import { useState, useEffect } from 'react';

/**
 * A hook that persists state to localStorage with SSR support.
 *
 * @param key The key to store the value under in localStorage
 * @param initialValue The initial value to use if no value is stored
 * @returns A tuple containing the stored value and a function to set the value
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  // Initialize with initialValue to prevent hydration mismatch
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  // After mount, we can safely access localStorage
  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
    }
  }, [key]);

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      // Allow value to be a function so we have same API as useState
      const valueToStore =
        value instanceof Function ? value(storedValue) : value;
      
      // Save state
      setStoredValue(valueToStore);
      
      // Save to local storage
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue] as const;
}
