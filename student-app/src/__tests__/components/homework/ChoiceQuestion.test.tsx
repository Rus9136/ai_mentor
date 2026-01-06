import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChoiceQuestion } from '@/components/homework/ChoiceQuestion';
import {
  StudentQuestionResponse,
  QuestionType,
  SubmissionResult,
} from '@/lib/api/homework';

// Mock question data
const mockSingleChoiceQuestion: StudentQuestionResponse = {
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

const mockMultipleChoiceQuestion: StudentQuestionResponse = {
  id: 2,
  question_text: 'Select all even numbers:',
  question_type: QuestionType.MULTIPLE_CHOICE,
  options: [
    { id: 'a', text: '2' },
    { id: 'b', text: '3' },
    { id: 'c', text: '4' },
    { id: 'd', text: '5' },
  ],
  points: 20,
  my_answer: null,
  my_selected_options: null,
  is_answered: false,
};

const mockTrueFalseQuestion: StudentQuestionResponse = {
  id: 3,
  question_text: 'Is the Earth round?',
  question_type: QuestionType.TRUE_FALSE,
  options: [
    { id: 'true', text: 'True' },
    { id: 'false', text: 'False' },
  ],
  points: 5,
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
  explanation: '2 + 2 equals 4',
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
  explanation: '2 + 2 equals 4, not 3',
  ai_feedback: null,
  ai_confidence: null,
  needs_review: false,
};

describe('ChoiceQuestion', () => {
  const mockOnAnswer = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnAnswer.mockResolvedValue(mockCorrectResult);
  });

  describe('Rendering', () => {
    it('renders question text', () => {
      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByText('What is 2 + 2?')).toBeInTheDocument();
    });

    it('renders question number', () => {
      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      // Mock translation returns the key, so check for number key pattern
      expect(screen.getByText(/number/i)).toBeInTheDocument();
    });

    it('renders all options for single choice', () => {
      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('renders all options for multiple choice', () => {
      render(
        <ChoiceQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('renders true/false options', () => {
      render(
        <ChoiceQuestion
          question={mockTrueFalseQuestion}
          questionNumber={3}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByText('True')).toBeInTheDocument();
      expect(screen.getByText('False')).toBeInTheDocument();
    });

    it('renders option letters (A, B, C)', () => {
      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
      expect(screen.getByText('C')).toBeInTheDocument();
    });
  });

  describe('Single Choice Selection', () => {
    it('submits immediately when option clicked', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      await user.click(screen.getByText('4'));

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith(['b']);
      });
    });

    it('selects new option and submits', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      // Click first option
      await user.click(screen.getByText('3'));

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith(['a']);
      });
    });
  });

  describe('Multiple Choice Selection', () => {
    it('allows selecting multiple options before submit', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      // Select options 2 and 4
      await user.click(screen.getByText('2'));
      await user.click(screen.getByText('4'));

      // Should not submit yet
      expect(mockOnAnswer).not.toHaveBeenCalled();

      // Verify visual selection (check for primary color class)
      const option2 = screen.getByText('2').closest('button');
      expect(option2?.className).toContain('border-primary');
    });

    it('deselects option when clicked again', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      // Select and deselect
      await user.click(screen.getByText('2'));
      await user.click(screen.getByText('2'));

      // Option should be deselected - check it has gray border (not selected state)
      const option2 = screen.getByText('2').closest('button');
      // When deselected, should have border-gray-200 style
      expect(option2?.className).toContain('border-gray-200');
    });

    it('submits multiple selections when submit button clicked', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      // Select options
      await user.click(screen.getByText('2'));
      await user.click(screen.getByText('4'));

      // Click submit button (translation mock returns key)
      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith(['a', 'c']);
      });
    });

    it('disables submit button when no options selected', () => {
      render(
        <ChoiceQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit button when options are selected', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      await user.click(screen.getByText('2'));

      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Disabled State', () => {
    it('disables options when disabled prop is true', async () => {
      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          disabled={true}
        />
      );

      await user.click(screen.getByText('4'));

      expect(mockOnAnswer).not.toHaveBeenCalled();
    });
  });

  describe('Already Answered State', () => {
    it('disables options when question is already answered', async () => {
      const answeredQuestion: StudentQuestionResponse = {
        ...mockSingleChoiceQuestion,
        is_answered: true,
        my_selected_options: ['b'],
      };

      const user = userEvent.setup();

      render(
        <ChoiceQuestion
          question={answeredQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
        />
      );

      await user.click(screen.getByText('3'));

      expect(mockOnAnswer).not.toHaveBeenCalled();
    });

    it('shows feedback styling when feedback is provided', () => {
      render(
        <ChoiceQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          feedback={mockCorrectResult}
        />
      );

      // Options should be disabled
      const option = screen.getByText('4').closest('button');
      expect(option).toBeDisabled();
    });
  });

  describe('Feedback Display', () => {
    it('shows green styling for correct answer', () => {
      const questionWithSelection = {
        ...mockSingleChoiceQuestion,
        my_selected_options: ['b'],
      };

      render(
        <ChoiceQuestion
          question={questionWithSelection}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          feedback={mockCorrectResult}
        />
      );

      const correctOption = screen.getByText('4').closest('button');
      expect(correctOption?.className).toContain('border-green');
      expect(correctOption?.className).toContain('bg-green');
    });

    it('shows red styling for incorrect answer', () => {
      const questionWithSelection = {
        ...mockSingleChoiceQuestion,
        my_selected_options: ['a'],
      };

      render(
        <ChoiceQuestion
          question={questionWithSelection}
          questionNumber={1}
          onAnswer={mockOnAnswer}
          feedback={mockIncorrectResult}
        />
      );

      const incorrectOption = screen.getByText('3').closest('button');
      expect(incorrectOption?.className).toContain('border-red');
      expect(incorrectOption?.className).toContain('bg-red');
    });
  });

  describe('Pre-selected Options', () => {
    it('shows pre-selected options from question data', () => {
      const questionWithSelection = {
        ...mockMultipleChoiceQuestion,
        my_selected_options: ['a', 'c'],
      };

      render(
        <ChoiceQuestion
          question={questionWithSelection}
          questionNumber={2}
          onAnswer={mockOnAnswer}
        />
      );

      const option2 = screen.getByText('2').closest('button');
      const option4 = screen.getByText('4').closest('button');

      expect(option2?.className).toContain('border-primary');
      expect(option4?.className).toContain('border-primary');
    });
  });
});
