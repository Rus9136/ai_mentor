import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { textbookConversionsApi } from '@/lib/api/textbook-conversions';
import { toast } from 'sonner';

export const conversionKeys = {
  all: ['textbook-conversions'] as const,
  status: (textbookId: number) => [...conversionKeys.all, 'status', textbookId] as const,
};

export function useConversionStatus(textbookId: number, enabled = true) {
  return useQuery({
    queryKey: conversionKeys.status(textbookId),
    queryFn: () => textbookConversionsApi.getStatus(textbookId),
    enabled: enabled && textbookId > 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'PENDING' || status === 'PROCESSING') {
        return 3000; // Poll every 3 seconds while in progress
      }
      return false;
    },
  });
}

export function useUploadPdf(textbookId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => textbookConversionsApi.uploadPdf(textbookId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversionKeys.status(textbookId) });
      toast.success('PDF загружен, конвертация запущена');
    },
    onError: (error: Error) => {
      toast.error(`Ошибка загрузки: ${error.message}`);
    },
  });
}
