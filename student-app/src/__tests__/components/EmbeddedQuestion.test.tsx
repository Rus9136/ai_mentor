import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EmbeddedQuestion } from '@/components/learning/EmbeddedQuestion';
import { EmbeddedQuestion as EmbeddedQuestionType, AnswerResult } from '@/lib/api/textbooks';

// Mock question data
const mockSingleChoiceQuestion: EmbeddedQuestionType = {
  id: 1,
  paragraph_id: 1,
  question_text: 'What is the capital of Kazakhstan?',
  question_type: 'single_choice',
  options: [
    { id: 'a', text: 'Astana' },
    { id: 'b', text: 'Almaty' },
    { id: 'c', text: 'Shymkent' },
  ],
  hint: 'It was renamed in 2019',
  sort_order: 1,
};

const mockMultipleChoiceQuestion: EmbeddedQuestionType = {
  id: 2,
  paragraph_id: 1,
  question_text: 'Select all prime numbers:',
  question_type: 'multiple_choice',
  options: [
    { id: 'a', text: '2' },
    { id: 'b', text: '3' },
    { id: 'c', text: '4' },
    { id: 'd', text: '5' },
  ],
  hint: null,
  sort_order: 2,
};

const mockTrueFalseQuestion: EmbeddedQuestionType = {
  id: 3,
  paragraph_id: 1,
  question_text: 'Is the Earth round?',
  question_type: 'true_false',
  options: null,
  hint: 'Think about NASA photos',
  sort_order: 3,
};

const mockCorrectResult: AnswerResult = {
  is_correct: true,
  correct_answer: 'a',
  explanation: 'Correct! Astana is the capital.',
  attempts_count: 1,
};

const mockIncorrectResult: AnswerResult = {
  is_correct: false,
  correct_answer: 'a',
  explanation: 'The correct answer is Astana.',
  attempts_count: 1,
};

describe('EmbeddedQuestion', () => {
  const mockOnAnswer = vi.fn();
  const mockOnNext = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders question text', () => {
      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('question-text')).toHaveTextContent('What is the capital of Kazakhstan?');
    });

    it('renders question number', () => {
      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('question-number')).toBeInTheDocument();
    });

    it('renders all options for single choice', () => {
      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('option-a')).toBeInTheDocument();
      expect(screen.getByTestId('option-b')).toBeInTheDocument();
      expect(screen.getByTestId('option-c')).toBeInTheDocument();
    });

    it('renders all options for multiple choice', () => {
      render(
        <EmbeddedQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('option-a')).toBeInTheDocument();
      expect(screen.getByTestId('option-b')).toBeInTheDocument();
      expect(screen.getByTestId('option-c')).toBeInTheDocument();
      expect(screen.getByTestId('option-d')).toBeInTheDocument();
    });

    it('renders true/false options', () => {
      render(
        <EmbeddedQuestion
          question={mockTrueFalseQuestion}
          questionNumber={3}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('option-true')).toBeInTheDocument();
      expect(screen.getByTestId('option-false')).toBeInTheDocument();
    });

    it('renders hint button when hint is available', () => {
      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('show-hint')).toBeInTheDocument();
    });

    it('does not render hint button when hint is not available', () => {
      render(
        <EmbeddedQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.queryByTestId('show-hint')).not.toBeInTheDocument();
    });
  });

  describe('Single Choice Selection', () => {
    it('allows selecting single option', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));

      // Option should be selected (visual state)
      const optionA = screen.getByTestId('option-a');
      expect(optionA.className).toContain('amber');
    });

    it('deselects previous option when new one is selected', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('option-b'));

      const optionB = screen.getByTestId('option-b');
      expect(optionB.className).toContain('amber');
    });
  });

  describe('Multiple Choice Selection', () => {
    it('allows selecting multiple options', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('option-b'));

      // Both options should be selected
      const optionA = screen.getByTestId('option-a');
      const optionB = screen.getByTestId('option-b');
      expect(optionA.className).toContain('amber');
      expect(optionB.className).toContain('amber');
    });

    it('allows deselecting options', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('option-a')); // Deselect

      const optionA = screen.getByTestId('option-a');
      // When deselected, should have gray border (not amber-500 which is selected state)
      expect(optionA.className).toContain('border-gray-200');
      expect(optionA.className).not.toContain('border-amber-500');
    });
  });

  describe('Hint Functionality', () => {
    it('shows hint when clicked', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.queryByTestId('hint-box')).not.toBeInTheDocument();

      await user.click(screen.getByTestId('show-hint'));

      expect(screen.getByTestId('hint-box')).toBeInTheDocument();
      expect(screen.getByTestId('hint-box')).toHaveTextContent('It was renamed in 2019');
    });

    it('hides hint when clicked again', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('show-hint'));
      expect(screen.getByTestId('hint-box')).toBeInTheDocument();

      await user.click(screen.getByTestId('show-hint'));
      expect(screen.queryByTestId('hint-box')).not.toBeInTheDocument();
    });
  });

  describe('Submit Button State', () => {
    it('disables submit button when no option selected', () => {
      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      expect(screen.getByTestId('submit-answer')).toBeDisabled();
    });

    it('enables submit button when option is selected', async () => {
      const user = userEvent.setup();

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));

      expect(screen.getByTestId('submit-answer')).toBeEnabled();
    });
  });

  describe('Answer Submission', () => {
    it('calls onAnswer with correct answer for single choice', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith(1, 'a');
      });
    });

    it('calls onAnswer with multiple answers for multiple choice', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockMultipleChoiceQuestion}
          questionNumber={2}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('option-b'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(mockOnAnswer).toHaveBeenCalledWith(2, ['a', 'b']);
      });
    });
  });

  describe('Feedback Display', () => {
    it('shows correct feedback after correct answer', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.getByTestId('feedback-correct')).toBeInTheDocument();
      });
    });

    it('shows incorrect feedback after wrong answer', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockIncorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-b'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.getByTestId('feedback-incorrect')).toBeInTheDocument();
      });
    });

    it('displays explanation in feedback', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.getByTestId('feedback-correct')).toHaveTextContent('Correct! Astana is the capital.');
      });
    });
  });

  describe('After Answer State', () => {
    it('disables options after answer submitted', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.getByTestId('option-a')).toBeDisabled();
        expect(screen.getByTestId('option-b')).toBeDisabled();
        expect(screen.getByTestId('option-c')).toBeDisabled();
      });
    });

    it('shows next button after answer submitted', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.getByTestId('next-question')).toBeInTheDocument();
      });
    });

    it('hides submit button after answer submitted', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.queryByTestId('submit-answer')).not.toBeInTheDocument();
      });
    });

    it('hides hint button after answer submitted', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.queryByTestId('show-hint')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('calls onNext when next button clicked', async () => {
      const user = userEvent.setup();
      mockOnAnswer.mockResolvedValue(mockCorrectResult);

      render(
        <EmbeddedQuestion
          question={mockSingleChoiceQuestion}
          questionNumber={1}
          totalQuestions={3}
          onAnswer={mockOnAnswer}
          onNext={mockOnNext}
        />
      );

      await user.click(screen.getByTestId('option-a'));
      await user.click(screen.getByTestId('submit-answer'));

      await waitFor(() => {
        expect(screen.getByTestId('next-question')).toBeInTheDocument();
      });

      await user.click(screen.getByTestId('next-question'));

      expect(mockOnNext).toHaveBeenCalled();
    });
  });
});
