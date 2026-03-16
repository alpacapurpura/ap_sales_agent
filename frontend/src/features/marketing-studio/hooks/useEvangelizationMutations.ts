import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import { toast } from 'sonner';

export function usePromoteEvangelist() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (customerId: string) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.promoteToEvangelist(token, customerId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evangelization-detail'] });
      toast.success('Cliente promovido a Evangelista');
    },
    onError: () => { toast.error('Error al promover cliente'); },
  });
}

export function useCreateNpsSurvey() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { customer_id?: string; offer_id?: string; delivery_channel?: string }) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.createNpsSurvey(token, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evangelization-detail'] });
      toast.success('Encuesta enviada correctamente');
    },
    onError: () => { toast.error('Error al enviar encuesta'); },
  });
}
