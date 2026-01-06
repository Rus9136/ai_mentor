import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TextQuestion } from '@/components/homework/TextQuestion';
import {
  StudentQuestionResponse,
  QuestionType,
  SubmissionResult,
} from '@/lib/api/homework';

// Mock question data
const mockShortAnswerQuestion: StudentQuestionResponse = {
  id: 1,
  question_text: 'What is the capital of France?',
  question_type: QuestionType.SHORT_ANSWER,
  options: null,
  points: 10,
  my_answer: null,
  my_selected_options: null,
  is_answered: false,
};

const mockOpenEndedQuestion: StudentQuestionResponse = {
  id: 2,
  question_text: 'Explain the theory of relativity in your own words.',
  question_type: QuestionType.OPEN_ENDED,
  options: null,
  points: 20,
  my_answer: null,
  my_selected_options: null,
  is_answered: false,
};

const mockCorrectResult: SubmissionResult = {
  submission_id: 1,
  question_id: 1,
  is_correct: true,
  score: 10,
  max_score: 10,
  feedback: 'Correct!',
  explanation: 'Paris is the capital of France',
  ai_feedback: null,
  ai_confidence: null,
  needs_review: false,
};

const mockIncorrectResult: SubmissionResult = {
  submission_id: 1,
  question_id: 1,
  is_correct: false,
  score: 0,
  max_score: 10,
  feedback: 'Incorrect',
  explanation: 'Paris is the capital of France',
  ai_feedback: null,
  ai_confidence: null,
  needs_review: false,
};

const mockPendingResult: SubmissionResult = {
  submission_id: 1,
  question_id: 2,
  is_correct: null,
  score: 15,
  max_score: 20,
  feedback: 'Good explanation',
  explanation: null,
  ai_feedback: 'Your explanation covers the main concepts well.',
  ai_confidence: 0.75,
  needs_review: true,
};

describe('TextQuestion', () => {
  const mockOnAnswer = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAnswer.mockResolvedValue(mockCorrectResult);
  });

  describe('Rendering', () => {
    it('renders question text', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(
        screen.getByText('What is the capital of France?')
      ).toBeInTheDocument();
    });

    it('renders input for short answer', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('textbox').tagName).toBe('INPUT');
    });

    it('renders textarea for open-ended', () => {
      render(
        <TextQuestion
          question={mockOpenEndedQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByRole('textbox')).toBeInTheDocument();
      expect(screen.getByRole('textbox').tagName).toBe('TEXTAREA');
    });

    it('renders submit button', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(
        screen.getByRole('button', { name: /submit/i })
      ).toBeInTheDocument();
    });

    it('renders placeholder text', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(
        screen.getByPlaceholderText('textPlaceholder')
      ).toBeInTheDocument();
    });
  });

  describe('Text Input', () => {
    it('allows typing in input', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, 'Paris');

      expect(input).toHaveValue('Paris');
    });

    it('allows typing in textarea', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockOpenEndedQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'The theory of relativity explains...');

      expect(textarea).toHaveValue('The theory of relativity explains...');
    });
  });

  describe('Submit Button State', () => {
    it('disables submit button when input is empty', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toBeDisabled();
    });

    it('disables submit button when input is whitespace only', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, '   ');

      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit button when input has text', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, 'Paris');

      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Answer Submission', () => {
    it('calls onAnswer with trimmed text when submit clicked', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, '  Paris  ');

      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith('Paris');
      });
    });

    it('submits on Enter key for short answer', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, 'Paris{enter}');

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith('Paris');
      });
    });

    it('does not submit on Enter key for open-ended', async () => {
      const user = userEvent.setup();

      render(
        <TextQuestion
          question={mockOpenEndedQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      const textarea = screen.getByRole('textbox');
      await user.type(textarea, 'My answer{enter}');

      expect(mockOnAnswer).not.toHaveBeenCalled();
    });
  });

  describe('Disabled State', () => {
    it('disables input when disabled prop is true', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          disabled={true}
        />
      );

      expect(screen.getByRole('textbox')).toBeDisabled();
    });
  });

  describe('Already Answered State', () => {
    it('disables input when question is already answered', () => {
      const answeredQuestion: StudentQuestionResponse = {
        ...mockShortAnswerQuestion,
        is_answered: true,
        my_answer: 'Paris',
      };

      render(
        <TextQuestion
          question={answeredQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByRole('textbox')).toBeDisabled();
    });

    it('shows pre-filled answer from question data', () => {
      const answeredQuestion: StudentQuestionResponse = {
        ...mockShortAnswerQuestion,
        my_answer: 'Paris',
      };

      render(
        <TextQuestion
          question={answeredQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByRole('textbox')).toHaveValue('Paris');
    });

    it('hides submit button when feedback is provided', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          feedback={mockCorrectResult}
        />
      );

      expect(
        screen.queryByRole('button', { name: /submit/i })
      ).not.toBeInTheDocument();
    });
  });

  describe('Feedback Styling', () => {
    it('shows green border for correct answer', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          feedback={mockCorrectResult}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border-green');
      expect(input.className).toContain('bg-green');
    });

    it('shows red border for incorrect answer', () => {
      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          feedback={mockIncorrectResult}
        />
      );

      const input = screen.getByRole('textbox');
      expect(input.className).toContain('border-red');
      expect(input.className).toContain('bg-red');
    });

    it('shows amber border for pending review (null is_correct)', () => {
      render(
        <TextQuestion
          question={mockOpenEndedQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
          feedback={mockPendingResult}
        />
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea.className).toContain('border-amber');
      expect(textarea.className).toContain('bg-amber');
    });
  });

  describe('Loading State', () => {
    it('shows loading indicator during submission', async () => {
      const user = userEvent.setup();
      // Make onAnswer never resolve to keep loading state
      mockOnAnswer.mockImplementation(
        () => new Promise(() => {})
      );

      render(
        <TextQuestion
          question={mockShortAnswerQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      const input = screen.getByRole('textbox');
      await user.type(input, 'Paris');

      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      // Check for submitting text (translation returns key)
      await waitFor(() => {
        expect(screen.getByText('submitting')).toBeInTheDocument();
      });
    });
  });
});
