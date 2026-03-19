export interface Lab {
  id: number;
  subject_id: number;
  textbook_id: number | null;
  title: string;
  description: string | null;
  lab_type: 'map' | 'molecule_3d' | 'simulation' | 'anatomy';
  config: Record<string, unknown>;
  is_active: boolean;
  thumbnail_url: string | null;
}

export interface LabProgress {
  id: number;
  lab_id: number;
  progress_data: Record<string, unknown>;
  xp_earned: number;
  completed_at: string | null;
}

export interface LabTask {
  id: number;
  lab_id: number;
  title: string;
  task_type: 'find_on_map' | 'order_events' | 'choose_epoch' | 'quiz';
  task_data: Record<string, unknown>;
  xp_reward: number;
  order_index: number;
}

export interface LabTaskAnswerResponse {
  is_correct: boolean;
  explanation: string | null;
  xp_earned: number;
}

export interface EpochData {
  id: string;
  name: string;
  period: string;
  start_year: number;
  end_year: number;
  description: string;
  paragraph_id: number | null;
  color: string;
}
