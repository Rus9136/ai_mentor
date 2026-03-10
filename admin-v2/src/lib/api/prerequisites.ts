import { apiClient } from './client';

export interface PrerequisiteResponse {
  id: number;
  paragraph_id: number;
  prerequisite_paragraph_id: number;
  strength: string;
  created_at: string;
  prerequisite_title: string | null;
  prerequisite_number: number | null;
  prerequisite_chapter_title: string | null;
  prerequisite_textbook_title: string | null;
  prerequisite_grade_level: number | null;
}

export interface PrerequisiteCreate {
  prerequisite_paragraph_id: number;
  strength: string;
}

export interface PrerequisiteEdge {
  id: number;
  from_paragraph_id: number;
  to_paragraph_id: number;
  strength: string;
}

export interface TextbookGraphResponse {
  textbook_id: number;
  edges: PrerequisiteEdge[];
  total_edges: number;
}

export const prerequisitesApi = {
  getList: async (paragraphId: number): Promise<PrerequisiteResponse[]> => {
    const { data } = await apiClient.get<PrerequisiteResponse[]>(
      `/admin/global/paragraphs/${paragraphId}/prerequisites`
    );
    return data;
  },

  create: async (
    paragraphId: number,
    payload: PrerequisiteCreate
  ): Promise<PrerequisiteResponse> => {
    const { data } = await apiClient.post<PrerequisiteResponse>(
      `/admin/global/paragraphs/${paragraphId}/prerequisites`,
      payload
    );
    return data;
  },

  delete: async (prereqId: number): Promise<void> => {
    await apiClient.delete(`/admin/global/prerequisites/${prereqId}`);
  },

  getTextbookGraph: async (textbookId: number): Promise<TextbookGraphResponse> => {
    const { data } = await apiClient.get<TextbookGraphResponse>(
      `/admin/global/textbooks/${textbookId}/prerequisite-graph`
    );
    return data;
  },
};
