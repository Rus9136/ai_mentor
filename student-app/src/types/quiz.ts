// Quiz Battle types — supports classic, team, self-paced, quick question modes

export enum QuizState {
  JOIN = 'join',
  LOBBY = 'lobby',
  QUESTION = 'question',
  ANSWERED = 'answered',
  RESULT = 'result',
  FINISHED = 'finished',
  // Self-paced states
  SELF_PACED_QUESTION = 'self_paced_question',
  SELF_PACED_FEEDBACK = 'self_paced_feedback',
  // Quick question states
  QUICK_ANSWER = 'quick_answer',
  QUICK_WAITING = 'quick_waiting',
}

// ── WebSocket messages (server → client) ──

export interface WsParticipantJoined {
  type: 'participant_joined';
  data: { student_name: string; count: number };
}

export interface WsQuizStarted {
  type: 'quiz_started';
  data: { total_questions: number; mode?: string };
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

// Team mode messages
export interface WsTeamAssigned {
  type: 'team_assigned';
  data: { team_id: number; team_name: string; team_color: string };
}

export interface WsTeamLeaderboard {
  type: 'team_leaderboard';
  data: { teams: TeamEntry[] };
}

// Quick question messages
export interface WsQuickQuestion {
  type: 'quick_question';
  data: { question_text: string; options: string[] };
}

export interface WsQuickAnswerAccepted {
  type: 'quick_answer_accepted';
  data: { selected_option: number };
}

export interface WsQuickQuestionEnd {
  type: 'quick_question_end';
  data: { responses: Record<string, number>; total: number };
}

export type WsServerMessage =
  | WsParticipantJoined
  | WsQuizStarted
  | WsQuestion
  | WsAnswerAccepted
  | WsQuestionResult
  | WsQuizFinished
  | WsError
  | WsTeamAssigned
  | WsTeamLeaderboard
  | WsQuickQuestion
  | WsQuickAnswerAccepted
  | WsQuickQuestionEnd;

// ── Client → Server ──

export interface WsAnswer {
  type: 'answer';
  data: { question_index: number; selected_option: number; answer_time_ms: number };
}

// ── Data types ──

export interface QuizFinishedData {
  leaderboard: LeaderboardEntry[];
  team_leaderboard?: TeamEntry[];
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

export interface TeamEntry {
  id: number;
  name: string;
  color: string;
  total_score: number;
  correct_answers: number;
  member_count: number;
  rank?: number;
}

export interface JoinQuizResponse {
  quiz_session_id: number;
  ws_url: string;
  status: string;
  participant_count: number;
  mode?: string;
  team_id?: number;
  team_name?: string;
  team_color?: string;
}

// ── Self-paced types ──

export interface SelfPacedNextQuestion {
  question: QuizQuestionData;
  answered_count: number;
  total_questions: number;
  is_last: boolean;
}

export interface SelfPacedAnswerResult {
  is_correct: boolean;
  correct_option: number;
  score: number;
  total_score: number;
  correct_answers: number;
  answered_count: number;
  total_questions: number;
  is_finished: boolean;
}
