import { apiClient } from './client';
import type {
  PresentationGenerateRequest,
  PresentationGenerateResponse,
  PresentationSaveRequest,
  PresentationFullResponse,
  PresentationListItem,
  PresentationUpdateRequest,
} from '@/types/presentation';

export async function generatePresentation(
  data: PresentationGenerateRequest
): Promise<PresentationGenerateResponse> {
  const response = await apiClient.post(
    '/teachers/presentations/generate',
    data
  );
  return response.data;
}

export async function savePresentation(
  data: PresentationSaveRequest
): Promise<PresentationFullResponse> {
  const response = await apiClient.post('/teachers/presentations', data);
  return response.data;
}

export async function listPresentations(
  skip = 0,
  limit = 20
): Promise<PresentationListItem[]> {
  const response = await apiClient.get('/teachers/presentations', {
    params: { skip, limit },
  });
  return response.data;
}

export async function getPresentation(
  id: number
): Promise<PresentationFullResponse> {
  const response = await apiClient.get(`/teachers/presentations/${id}`);
  return response.data;
}

export async function updatePresentation(
  id: number,
  data: PresentationUpdateRequest
): Promise<PresentationFullResponse> {
  const response = await apiClient.put(
    `/teachers/presentations/${id}`,
    data
  );
  return response.data;
}

export async function deletePresentation(id: number): Promise<void> {
  await apiClient.delete(`/teachers/presentations/${id}`);
}

export interface PresentationTemplate {
  slug: string;
  label: string;
  file: string;
}

export async function getTemplates(): Promise<PresentationTemplate[]> {
  const response = await apiClient.get('/teachers/presentations/templates');
  return response.data;
}

export async function exportPresentationPptx(id: number, template = 'academic'): Promise<void> {
  const response = await apiClient.get(
    `/teachers/presentations/${id}/export/pptx`,
    { params: { template }, responseType: 'blob' }
  );
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `presentation_${id}.pptx`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
