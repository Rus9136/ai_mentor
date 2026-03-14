// Quiz Battle types

export enum QuizState {
  JOIN = 'join',
  LOBBY = 'lobby',
  QUESTION = 'question',
  ANSWERED = 'answered',
  RESULT = 'result',
  FINISHED = 'finished',
}

// ── WebSocket messages (server → client) ──

export interface WsParticipantJoined {
  type: 'participant_joined';
  data: { student_name: string; count: number };
}

export interface WsQuizStarted {
  type: 'quiz_started';
  data: { total_questions: number };
}

export interface WsQuestion {
  type: 'question';
  data: QuizQuestionData;
}

export interface QuizQuestionData {
  index: number;
  text: string;
  options: string[];
  time_limit_ms: number;
  image_url: string | null;
}

export interface WsAnswerAccepted {
  type: 'answer_accepted';
  data: {
    is_correct: boolean;
    score: number;
    streak_bonus: number;
    total_score: number;
    current_streak: number;
    max_streak: number;
  };
}

export interface WsQuestionResult {
  type: 'question_result';
  data: {
    correct_option: number;
    stats: Record<string, number>;
    leaderboard_top5: LeaderboardEntry[];
  };
}

export interface WsQuizFinished {
  type: 'quiz_finished';
  data: QuizFinishedData;
}

export interface WsError {
  type: 'error';
  data: { message: string };
}

export type WsServerMessage =
  | WsParticipantJoined
  | WsQuizStarted
  | WsQuestion
  | WsAnswerAccepted
  | WsQuestionResult
  | WsQuizFinished
  | WsError;

// ── Client → Server ──

export interface WsAnswer {
  type: 'answer';
  data: { question_index: number; selected_option: number; answer_time_ms: number };
}

// ── Data types ──

export interface QuizFinishedData {
  leaderboard: LeaderboardEntry[];
  your_rank: number | null;
  your_score: number;
  your_correct: number;
  xp_earned: number;
  correct_answers: number;
  total_questions: number;
}

export interface LeaderboardEntry {
  rank: number;
  student_name: string;
  total_score: number;
  correct_answers?: number;
  xp_earned?: number;
}

export interface JoinQuizResponse {
  quiz_session_id: number;
  ws_url: string;
  status: string;
  participant_count: number;
}
