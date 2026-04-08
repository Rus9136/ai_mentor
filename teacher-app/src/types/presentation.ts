export type SlideThemeName = 'warm' | 'green';

export interface PresentationGenerateRequest {
  paragraph_id: number;
  class_id?: number;
  language: string;
  slide_count: number;
}

export interface SlideData {
  type: 'title' | 'objectives' | 'content' | 'key_terms' | 'quiz' | 'summary';
  title: string;
  subtitle?: string;
  body?: string;
  image_url?: string | null;
  items?: string[];
  terms?: Array<{ term: string; definition: string }>;
  question?: string;
  options?: string[];
  answer?: number;
}

export interface PresentationData {
  title: string;
  slides: SlideData[];
}

export interface PresentationContext {
  paragraph_title: string;
  chapter_title: string;
  textbook_title: string;
  subject: string;
  grade_level: number;
  textbook_id: number;
  theme?: SlideThemeName;
}

export interface PresentationGenerateResponse {
  presentation: PresentationData;
  context: PresentationContext;
}

// --- SAVE / CRUD ---

export interface PresentationSaveRequest {
  paragraph_id: number;
  class_id?: number;
  language: string;
  slide_count: number;
  title?: string;
  slides_data: Record<string, unknown>;
  context_data: Record<string, unknown>;
}

export interface PresentationUpdateRequest {
  title?: string;
  slides_data?: Record<string, unknown>;
}

export interface PresentationListItem {
  id: number;
  title: string;
  language: string;
  slide_count: number;
  paragraph_id: number;
  class_id: number | null;
  subject: string | null;
  grade_level: number | null;
  created_at: string;
}

export interface PresentationFullResponse {
  id: number;
  title: string;
  teacher_id: number;
  school_id: number;
  paragraph_id: number;
  class_id: number | null;
  language: string;
  slide_count: number;
  slides_data: PresentationData;
  context_data: PresentationContext;
  created_at: string;
  updated_at: string;
}
