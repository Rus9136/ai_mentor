import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import {
  listMyHomework,
  getHomeworkDetail,
  startTask,
  getTaskQuestions,
  submitAnswer,
  completeSubmission,
  getSubmissionResults,
  StudentHomeworkStatus,
  SubmissionStatus,
  TaskType,
  QuestionType,
  StudentHomeworkResponse,
  StudentTaskResponse,
  StudentQuestionResponse,
  SubmissionResult,
  TaskSubmissionResult,
} from '@/lib/api/homework';
import { apiClient } from '@/lib/api/client';

// Mock the API client
vi.mock('@/lib/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock data
const mockHomework: StudentHomeworkResponse = {
  id: 1,
  title: 'Math Homework',
  description: 'Complete chapter 5 exercises',
  due_date: '2026-01-10T23:59:59',
  is_overdue: false,
  can_submit: true,
  my_status: StudentHomeworkStatus.ASSIGNED,
  my_score: null,
  max_score: 100,
  my_percentage: null,
  is_late: false,
  late_penalty: 0,
  show_explanations: true,
  tasks: [
    {
      id: 1,
      paragraph_id: 1,
      paragraph_title: 'Quadratic Equations',
      task_type: TaskType.QUIZ,
      instructions: 'Answer all questions',
      points: 50,
      time_limit_minutes: 30,
      status: SubmissionStatus.NOT_STARTED,
      current_attempt: 0,
      max_attempts: 3,
      attempts_remaining: 3,
      my_score: null,
      questions_count: 5,
      answered_count: 0,
    },
  ],
};

const mockTask: StudentTaskResponse = {
  id: 1,
  paragraph_id: 1,
  paragraph_title: 'Quadratic Equations',
  task_type: TaskType.QUIZ,
  instructions: 'Answer all questions',
  points: 50,
  time_limit_minutes: 30,
  status: SubmissionStatus.IN_PROGRESS,
  current_attempt: 1,
  max_attempts: 3,
  attempts_remaining: 2,
  my_score: null,
  questions_count: 5,
  answered_count: 0,
  submission_id: 1,
};

const mockQuestion: StudentQuestionResponse = {
  id: 1,
  question_text: 'What is 2 + 2?',
  question_type: QuestionType.SINGLE_CHOICE,
  options: [
    { id: 'a', text: '3' },
    { id: 'b', text: '4' },
    { id: 'c', text: '5' },
  ],
  points: 10,
  my_answer: null,
  my_selected_options: null,
  is_answered: false,
};

const mockSubmissionResult: SubmissionResult = {
  submission_id: 1,
  question_id: 1,
  is_correct: true,
  score: 10,
  max_score: 10,
  feedback: 'Correct!',
  explanation: '2 + 2 = 4',
  ai_feedback: null,
  ai_confidence: null,
  needs_review: false,
};

const mockTaskSubmissionResult: TaskSubmissionResult = {
  submission_id: 1,
  task_id: 1,
  status: SubmissionStatus.GRADED,
  attempt_number: 1,
  total_score: 45,
  max_score: 50,
  percentage: 90,
  is_late: false,
  late_penalty_applied: 0,
  original_score: null,
  answers: [mockSubmissionResult],
  correct_count: 4,
  incorrect_count: 1,
  needs_review_count: 0,
};

describe('Homework API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listMyHomework', () => {
    it('fetches homework list without params', async () => {
      (apiClient.get as Mock).mockResolvedValue({ data: [mockHomework] });

      const result = await listMyHomework();

      expect(apiClient.get).toHaveBeenCalledWith('/students/homework', {
        params: undefined,
      });
      expect(result).toEqual([mockHomework]);
    });

    it('fetches homework list with status filter', async () => {
      (apiClient.get as Mock).mockResolvedValue({ data: [mockHomework] });

      const result = await listMyHomework({
        status: StudentHomeworkStatus.IN_PROGRESS,
      });

      expect(apiClient.get).toHaveBeenCalledWith('/students/homework', {
        params: { status: StudentHomeworkStatus.IN_PROGRESS },
      });
      expect(result).toEqual([mockHomework]);
    });

    it('fetches homework list with include_completed', async () => {
      (apiClient.get as Mock).mockResolvedValue({ data: [mockHomework] });

      const result = await listMyHomework({ include_completed: true });

      expect(apiClient.get).toHaveBeenCalledWith('/students/homework', {
        params: { include_completed: true },
      });
      expect(result).toEqual([mockHomework]);
    });
  });

  describe('getHomeworkDetail', () => {
    it('fetches homework detail by id', async () => {
      (apiClient.get as Mock).mockResolvedValue({ data: mockHomework });

      const result = await getHomeworkDetail(1);

      expect(apiClient.get).toHaveBeenCalledWith('/students/homework/1');
      expect(result).toEqual(mockHomework);
    });
  });

  describe('startTask', () => {
    it('starts a task and returns task response', async () => {
      (apiClient.post as Mock).mockResolvedValue({ data: mockTask });

      const result = await startTask(1, 1);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/students/homework/1/tasks/1/start'
      );
      expect(result).toEqual(mockTask);
      expect(result.submission_id).toBe(1);
      expect(result.status).toBe(SubmissionStatus.IN_PROGRESS);
    });
  });

  describe('getTaskQuestions', () => {
    it('fetches questions for a task', async () => {
      (apiClient.get as Mock).mockResolvedValue({ data: [mockQuestion] });

      const result = await getTaskQuestions(1, 1);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/students/homework/1/tasks/1/questions'
      );
      expect(result).toEqual([mockQuestion]);
      expect(result[0].question_type).toBe(QuestionType.SINGLE_CHOICE);
    });
  });

  describe('submitAnswer', () => {
    it('submits answer with selected options', async () => {
      (apiClient.post as Mock).mockResolvedValue({ data: mockSubmissionResult });

      const result = await submitAnswer(1, {
        question_id: 1,
        selected_options: ['b'],
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/students/homework/submissions/1/answer',
        { question_id: 1, selected_options: ['b'] }
      );
      expect(result).toEqual(mockSubmissionResult);
      expect(result.is_correct).toBe(true);
    });

    it('submits answer with text', async () => {
      const textResult: SubmissionResult = {
        ...mockSubmissionResult,
        is_correct: null,
        ai_feedback: 'Good explanation',
        ai_confidence: 0.85,
        needs_review: false,
      };
      (apiClient.post as Mock).mockResolvedValue({ data: textResult });

      const result = await submitAnswer(1, {
        question_id: 2,
        answer_text: 'My written answer',
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/students/homework/submissions/1/answer',
        { question_id: 2, answer_text: 'My written answer' }
      );
      expect(result.ai_feedback).toBe('Good explanation');
      expect(result.ai_confidence).toBe(0.85);
    });
  });

  describe('completeSubmission', () => {
    it('completes submission and returns results', async () => {
      (apiClient.post as Mock).mockResolvedValue({
        data: mockTaskSubmissionResult,
      });

      const result = await completeSubmission(1);

      expect(apiClient.post).toHaveBeenCalledWith(
        '/students/homework/submissions/1/complete'
      );
      expect(result).toEqual(mockTaskSubmissionResult);
      expect(result.percentage).toBe(90);
      expect(result.correct_count).toBe(4);
    });

    it('handles late submission with penalty', async () => {
      const lateResult: TaskSubmissionResult = {
        ...mockTaskSubmissionResult,
        is_late: true,
        late_penalty_applied: 10,
        original_score: 45,
        total_score: 40.5,
        percentage: 81,
      };
      (apiClient.post as Mock).mockResolvedValue({ data: lateResult });

      const result = await completeSubmission(1);

      expect(result.is_late).toBe(true);
      expect(result.late_penalty_applied).toBe(10);
      expect(result.original_score).toBe(45);
    });
  });

  describe('getSubmissionResults', () => {
    it('fetches submission results with feedback', async () => {
      const questionWithFeedback = {
        ...mockQuestion,
        is_correct: true,
        score: 10,
        max_score: 10,
        explanation: '2 + 2 = 4',
        ai_feedback: null,
        ai_confidence: null,
      };
      (apiClient.get as Mock).mockResolvedValue({ data: [questionWithFeedback] });

      const result = await getSubmissionResults(1);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/students/homework/submissions/1/results'
      );
      expect(result[0].is_correct).toBe(true);
      expect(result[0].explanation).toBe('2 + 2 = 4');
    });
  });
});

describe('Homework Enums', () => {
  describe('StudentHomeworkStatus', () => {
    it('has correct values', () => {
      expect(StudentHomeworkStatus.ASSIGNED).toBe('assigned');
      expect(StudentHomeworkStatus.IN_PROGRESS).toBe('in_progress');
      expect(StudentHomeworkStatus.SUBMITTED).toBe('submitted');
      expect(StudentHomeworkStatus.GRADED).toBe('graded');
      expect(StudentHomeworkStatus.RETURNED).toBe('returned');
    });
  });

  describe('SubmissionStatus', () => {
    it('has correct values', () => {
      expect(SubmissionStatus.NOT_STARTED).toBe('not_started');
      expect(SubmissionStatus.IN_PROGRESS).toBe('in_progress');
      expect(SubmissionStatus.SUBMITTED).toBe('submitted');
      expect(SubmissionStatus.GRADED).toBe('graded');
    });
  });

  describe('TaskType', () => {
    it('has correct values', () => {
      expect(TaskType.READ).toBe('read');
      expect(TaskType.QUIZ).toBe('quiz');
      expect(TaskType.OPEN_QUESTION).toBe('open_question');
      expect(TaskType.ESSAY).toBe('essay');
      expect(TaskType.PRACTICE).toBe('practice');
      expect(TaskType.CODE).toBe('code');
    });
  });

  describe('QuestionType', () => {
    it('has correct values', () => {
      expect(QuestionType.SINGLE_CHOICE).toBe('single_choice');
      expect(QuestionType.MULTIPLE_CHOICE).toBe('multiple_choice');
      expect(QuestionType.TRUE_FALSE).toBe('true_false');
      expect(QuestionType.SHORT_ANSWER).toBe('short_answer');
      expect(QuestionType.OPEN_ENDED).toBe('open_ended');
      expect(QuestionType.CODE).toBe('code');
    });
  });
});
