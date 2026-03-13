// Types matching backend schemas from backend/app/schemas/gamification.py

export interface GamificationProfile {
  total_xp: number;
  level: number;
  xp_in_current_level: number;
  xp_to_next_level: number;
  current_streak: number;
  longest_streak: number;
  badges_earned_count: number;
}

export interface Achievement {
  id: number;
  code: string;
  name_kk: string;
  name_ru: string;
  description_kk: string | null;
  description_ru: string | null;
  icon: string;
  category: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  xp_reward: number;
}

export interface StudentAchievement {
  id: number;
  achievement: Achievement;
  progress: number;
  is_earned: boolean;
  earned_at: string | null;
}

export interface LeaderboardEntry {
  rank: number;
  student_id: number;
  student_name: string;
  total_xp: number;
  level: number;
}

export interface Leaderboard {
  entries: LeaderboardEntry[];
  student_rank: number;
  student_xp: number;
  student_level: number;
  total_students: number;
  scope: 'school' | 'class';
}

export interface DailyQuest {
  id: number;
  code: string;
  name_kk: string;
  name_ru: string;
  description_kk: string | null;
  description_ru: string | null;
  quest_type: string;
  target_value: number;
  xp_reward: number;
  current_value: number;
  is_completed: boolean;
  completed_at: string | null;
  subject_name_kk?: string | null;
  subject_name_ru?: string | null;
}

export interface XpHistoryEntry {
  id: number;
  amount: number;
  source_type: string;
  source_id: number | null;
  created_at: string;
}
