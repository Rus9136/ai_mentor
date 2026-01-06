import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuestionFeedback } from '@/components/homework/QuestionFeedback';
import { SubmissionResult } from '@/lib/api/homework';

// Mock feedback data
const mockCorrectFeedback: SubmissionResult = {
  submission_id: 1,
  question_id: 1,
  is_correct: true,
  score: 10,
  max_score: 10,
  feedback: 'Well done!',
  explanation: '2 + 2 = 4',
  ai_feedback: null,
  ai_confidence: null,
  needs_review: false,
};

const mockIncorrectFeedback: SubmissionResult = {
  submission_id: 1,
  question_id: 1,
  is_correct: false,
  score: 0,
  max_score: 10,
  feedback: 'Try again',
  explanation: 'The correct answer is 4',
  ai_feedback: null,
  ai_confidence: null,
  needs_review: false,
};

const mockPendingFeedback: SubmissionResult = {
  submission_id: 1,
  question_id: 2,
  is_correct: null,
  score: 15,
  max_score: 20,
  feedback: 'Your answer is being reviewed',
  explanation: null,
  ai_feedback: 'Good explanation of the main concepts',
  ai_confidence: 0.75,
  needs_review: true,
};

const mockPartialFeedback: SubmissionResult = {
  submission_id: 1,
  question_id: 1,
  is_correct: true,
  score: 7,
  max_score: 10,
  feedback: 'Partially correct',
  explanation: 'You got most of it right',
  ai_feedback: 'Consider adding more detail',
  ai_confidence: 0.85,
  needs_review: false,
};

describe('QuestionFeedback', () => {
  describe('Correct Answer Display', () => {
    it('shows correct status text', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      // Translation returns key
      expect(screen.getByText('correct')).toBeInTheDocument();
    });

    it('shows green styling for correct answer', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      // The main container should have green styling
      const container = screen.getByText('correct').closest('div')?.parentElement;
      expect(container?.className).toContain('bg-green');
      expect(container?.className).toContain('border-green');
    });

    it('shows CheckCircle2 icon for correct answer', () => {
      const { container } = render(
        <QuestionFeedback feedback={mockCorrectFeedback} />
      );

      // Lucide icons render as SVG
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Incorrect Answer Display', () => {
    it('shows incorrect status text', () => {
      render(<QuestionFeedback feedback={mockIncorrectFeedback} />);

      expect(screen.getByText('incorrect')).toBeInTheDocument();
    });

    it('shows red styling for incorrect answer', () => {
      render(<QuestionFeedback feedback={mockIncorrectFeedback} />);

      const container = screen.getByText('incorrect').closest('div')?.parentElement;
      expect(container?.className).toContain('bg-red');
      expect(container?.className).toContain('border-red');
    });
  });

  describe('Pending Review Display', () => {
    it('shows needs review status text', () => {
      render(<QuestionFeedback feedback={mockPendingFeedback} />);

      // Should show needsReview (translation key) - there might be multiple
      const reviewTexts = screen.getAllByText('needsReview');
      expect(reviewTexts.length).toBeGreaterThan(0);
    });

    it('shows amber styling for pending review', () => {
      const { container } = render(<QuestionFeedback feedback={mockPendingFeedback} />);

      // Check for amber styling on the main container
      const amberElement = container.querySelector('[class*="bg-amber"]');
      expect(amberElement).toBeInTheDocument();
    });
  });

  describe('Score Display', () => {
    it('shows score in correct format', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.getByText('10.0/10')).toBeInTheDocument();
    });

    it('shows partial score', () => {
      render(<QuestionFeedback feedback={mockPartialFeedback} />);

      expect(screen.getByText('7.0/10')).toBeInTheDocument();
    });

    it('shows zero score for incorrect', () => {
      render(<QuestionFeedback feedback={mockIncorrectFeedback} />);

      expect(screen.getByText('0.0/10')).toBeInTheDocument();
    });
  });

  describe('Feedback Text', () => {
    it('shows feedback text when provided', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.getByText('Well done!')).toBeInTheDocument();
    });

    it('does not show feedback section when empty', () => {
      const feedbackNoText: SubmissionResult = {
        ...mockCorrectFeedback,
        feedback: null,
      };

      render(<QuestionFeedback feedback={feedbackNoText} />);

      expect(screen.queryByText('Well done!')).not.toBeInTheDocument();
    });
  });

  describe('Explanation Display', () => {
    it('shows explanation when showExplanation is true (default)', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.getByText('2 + 2 = 4')).toBeInTheDocument();
    });

    it('shows explanation header', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.getByText('explanation')).toBeInTheDocument();
    });

    it('hides explanation when showExplanation is false', () => {
      render(
        <QuestionFeedback
          feedback={mockCorrectFeedback}
          showExplanation={false}
        />
      );

      expect(screen.queryByText('2 + 2 = 4')).not.toBeInTheDocument();
    });

    it('does not show explanation section when explanation is null', () => {
      const feedbackNoExplanation: SubmissionResult = {
        ...mockCorrectFeedback,
        explanation: null,
      };

      render(<QuestionFeedback feedback={feedbackNoExplanation} />);

      expect(screen.queryByText(/explanation/i)).not.toBeInTheDocument();
    });
  });

  describe('AI Feedback Display', () => {
    it('shows AI feedback when provided', () => {
      render(<QuestionFeedback feedback={mockPendingFeedback} />);

      expect(
        screen.getByText('Good explanation of the main concepts')
      ).toBeInTheDocument();
    });

    it('shows AI feedback header', () => {
      render(<QuestionFeedback feedback={mockPendingFeedback} />);

      expect(screen.getByText('aiFeedback')).toBeInTheDocument();
    });

    it('does not show AI feedback section when ai_feedback is null', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.queryByText('aiFeedback')).not.toBeInTheDocument();
    });
  });

  describe('AI Confidence Display', () => {
    it('shows AI confidence percentage', () => {
      render(<QuestionFeedback feedback={mockPendingFeedback} />);

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('shows confidence bar', () => {
      const { container } = render(
        <QuestionFeedback feedback={mockPendingFeedback} />
      );

      // Check for progress bar element with correct width
      const progressBar = container.querySelector('[style*="width: 75%"]');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows green bar for high confidence (>= 0.7)', () => {
      const { container } = render(
        <QuestionFeedback feedback={mockPendingFeedback} />
      );

      const progressBar = container.querySelector('[style*="width: 75%"]');
      expect(progressBar?.className).toContain('bg-green');
    });

    it('shows amber bar for medium confidence (0.4-0.7)', () => {
      const mediumConfidence: SubmissionResult = {
        ...mockPendingFeedback,
        ai_confidence: 0.5,
      };

      const { container } = render(
        <QuestionFeedback feedback={mediumConfidence} />
      );

      const progressBar = container.querySelector('[style*="width: 50%"]');
      expect(progressBar?.className).toContain('bg-amber');
    });

    it('shows red bar for low confidence (< 0.4)', () => {
      const lowConfidence: SubmissionResult = {
        ...mockPendingFeedback,
        ai_confidence: 0.3,
      };

      const { container } = render(
        <QuestionFeedback feedback={lowConfidence} />
      );

      const progressBar = container.querySelector('[style*="width: 30%"]');
      expect(progressBar?.className).toContain('bg-red');
    });

    it('does not show confidence when ai_confidence is null', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.queryByText('%')).not.toBeInTheDocument();
    });
  });

  describe('Needs Review Badge', () => {
    it('shows needs review badge when needs_review is true', () => {
      render(<QuestionFeedback feedback={mockPendingFeedback} />);

      // There should be multiple needsReview texts (header and badge)
      const needsReviewElements = screen.getAllByText('needsReview');
      expect(needsReviewElements.length).toBeGreaterThan(1);
    });

    it('does not show needs review badge when needs_review is false', () => {
      render(<QuestionFeedback feedback={mockCorrectFeedback} />);

      expect(screen.queryByText('needsReview')).not.toBeInTheDocument();
    });
  });
});
