"use client";

import { useState, useEffect } from 'react';
import { CustomerProfile } from '../types';
import { fetchClient } from '../../../lib/http-client';

interface RFMStats {
  averageLtv: number;
  totalCustomers: number;
  activePercentage: number;
  churnRate: number;
}

interface MarketingDataResponse {
  profiles: CustomerProfile[];
  rfmStats: RFMStats | null;
}

export const useMarketingData = () => {
  const [profiles, setProfiles] = useState<CustomerProfile[]>([]);
  const [rfmStats, setRfmStats] = useState<RFMStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch from API
        const response = await fetchClient('/api/v1/marketing/profiles');
        
        if (response.ok) {
          const data: MarketingDataResponse = await response.json();
          setProfiles(data.profiles || []);
          setRfmStats(data.rfmStats || null);
        } else {
          // If API is not ready or fails, return empty
          console.warn('[MarketingStudio] API not ready or returned error, using empty state.');
          setProfiles([]);
          setRfmStats(null);
        }
      } catch (error) {
        console.error('[MarketingStudio] Failed to fetch data:', error);
        setProfiles([]);
        setRfmStats(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return {
    profiles,
    rfm: rfmStats,
    loading,
  };
};
