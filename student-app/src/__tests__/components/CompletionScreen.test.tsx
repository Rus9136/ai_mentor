import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen
 } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CompletionScreen } from '@/components/learning/CompletionScreen';

// Mock canvas-confetti
vi.mock('canvas-confetti', () => ({
  default: vi.fn(),
}));

// Default props for testing
const defaultProps = {
  paragraphTitle: 'Бронзовый век на территории Казахстана',
  paragraphNumber: 3,
  questionsTotal: 5,
  questionsCorrect: 4,
  timeSpentSeconds: 180,
  selfAssessment: 'understood' as const,
  nextParagraphId: 4,
  chapterId: 1,
  chapterTitle: 'Древняя история Казахстана',
  isLastInChapter: false,
  onGoToNext: vi.fn(),
  onGoToChapter: vi.fn(),
};

describe('CompletionScreen', () => {
  const mockOnGoToNext = vi.fn();
  const mockOnGoToChapter = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders component with data-testid', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('completion-screen')).toBeInTheDocument();
    });

    it('renders trophy icon', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('completion-trophy')).toBeInTheDocument();
    });

    it('renders stats section', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('completion-stats')).toBeInTheDocument();
    });

    it('renders paragraph title and number', () => {
      render(<CompletionScreen {...defaultProps} />);

      // Should show paragraph info
      expect(screen.getByText(/§3\. Бронзовый век/)).toBeInTheDocument();
    });

    it('renders paragraph number only when title is null', () => {
      render(<CompletionScreen {...defaultProps} paragraphTitle={null} />);

      expect(screen.getByText('§3')).toBeInTheDocument();
    });
  });

  describe('Score Display', () => {
    it('renders score display', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('score-display')).toBeInTheDocument();
    });

    it('displays correct score', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('score-value')).toHaveTextContent('4/5');
    });

    it('displays perfect score', () => {
      render(
        <CompletionScreen
          {...defaultProps}
          questionsTotal={5}
          questionsCorrect={5}
        />
      );

      expect(screen.getByTestId('score-value')).toHaveTextContent('5/5');
    });

    it('displays zero correct answers', () => {
      render(
        <CompletionScreen
          {...defaultProps}
          questionsTotal={5}
          questionsCorrect={0}
        />
      );

      expect(screen.getByTestId('score-value')).toHaveTextContent('0/5');
    });

    it('displays dash when no questions', () => {
      render(
        <CompletionScreen
          {...defaultProps}
          questionsTotal={0}
          questionsCorrect={0}
        />
      );

      expect(screen.getByTestId('score-value')).toHaveTextContent('-');
    });
  });

  describe('Time Display', () => {
    it('renders time display', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('time-display')).toBeInTheDocument();
    });

    it('displays time in minutes', () => {
      render(<CompletionScreen {...defaultProps} timeSpentSeconds={180} />);

      // 180 seconds = 3 minutes
      expect(screen.getByTestId('time-value')).toHaveTextContent('3');
    });

    it('displays less than 1 minute', () => {
      render(<CompletionScreen {...defaultProps} timeSpentSeconds={30} />);

      expect(screen.getByTestId('time-value')).toHaveTextContent('<1');
    });

    it('displays 0 as less than 1 minute', () => {
      render(<CompletionScreen {...defaultProps} timeSpentSeconds={0} />);

      expect(screen.getByTestId('time-value')).toHaveTextContent('<1');
    });
  });

  describe('Assessment Display', () => {
    it('renders assessment display', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('assessment-display')).toBeInTheDocument();
    });

    it('displays understood assessment', () => {
      render(<CompletionScreen {...defaultProps} selfAssessment="understood" />);

      expect(screen.getByTestId('assessment-value')).toBeInTheDocument();
    });

    it('displays questions assessment', () => {
      render(<CompletionScreen {...defaultProps} selfAssessment="questions" />);

      expect(screen.getByTestId('assessment-value')).toBeInTheDocument();
    });

    it('displays difficult assessment', () => {
      render(<CompletionScreen {...defaultProps} selfAssessment="difficult" />);

      expect(screen.getByTestId('assessment-value')).toBeInTheDocument();
    });

    it('displays dash when no assessment', () => {
      render(<CompletionScreen {...defaultProps} selfAssessment={null} />);

      expect(screen.getByTestId('assessment-value')).toHaveTextContent('-');
    });
  });

  describe('Action Buttons', () => {
    it('renders to chapter button', () => {
      render(<CompletionScreen {...defaultProps} />);

      expect(screen.getByTestId('to-chapter-btn')).toBeInTheDocument();
    });

    it('renders next paragraph button when nextParagraphId exists', () => {
      render(<CompletionScreen {...defaultProps} nextParagraphId={4} isLastInChapter={false} />);

      expect(screen.getByTestId('next-paragraph-btn')).toBeInTheDocument();
    });

    it('does not render next paragraph button when nextParagraphId is null', () => {
      render(<CompletionScreen {...defaultProps} nextParagraphId={null} />);

      expect(screen.queryByTestId('next-paragraph-btn')).not.toBeInTheDocument();
    });

    it('does not render next paragraph button when isLastInChapter is true', () => {
      render(<CompletionScreen {...defaultProps} isLastInChapter={true} />);

      expect(screen.queryByTestId('next-paragraph-btn')).not.toBeInTheDocument();
    });
  });

  describe('Button Interactions', () => {
    it('calls onGoToChapter when to chapter button clicked', async () => {
      const user = userEvent.setup();

      render(
        <CompletionScreen
          {...defaultProps}
          onGoToChapter={mockOnGoToChapter}
        />
      );

      await user.click(screen.getByTestId('to-chapter-btn'));

      expect(mockOnGoToChapter).toHaveBeenCalledTimes(1);
    });

    it('calls onGoToNext when next paragraph button clicked', async () => {
      const user = userEvent.setup();

      render(
        <CompletionScreen
          {...defaultProps}
          nextParagraphId={4}
          isLastInChapter={false}
          onGoToNext={mockOnGoToNext}
        />
      );

      await user.click(screen.getByTestId('next-paragraph-btn'));

      expect(mockOnGoToNext).toHaveBeenCalledTimes(1);
    });
  });

  describe('Chapter Complete State', () => {
    it('shows chapter complete message when isLastInChapter is true', () => {
      render(<CompletionScreen {...defaultProps} isLastInChapter={true} />);

      // Should show chapter title somewhere in completion message
      expect(screen.getByText(defaultProps.chapterTitle)).toBeInTheDocument();
    });

    it('does not show chapter complete message when isLastInChapter is false', () => {
      render(<CompletionScreen {...defaultProps} isLastInChapter={false} />);

      // Chapter title should not be prominently displayed
      const chapterCompleteElements = screen.queryAllByText(/chapterComplete/);
      expect(chapterCompleteElements.length).toBe(0);
    });
  });

  describe('Score Color Styling', () => {
    it('applies green styling for high score (>=80%)', () => {
      render(
        <CompletionScreen
          {...defaultProps}
          questionsTotal={5}
          questionsCorrect={4}
        />
      );

      const scoreDisplay = screen.getByTestId('score-display');
      // Check that green class is applied (80% = 4/5)
      expect(scoreDisplay.innerHTML).toContain('green');
    });

    it('applies amber styling for medium score (60-79%)', () => {
      render(
        <CompletionScreen
          {...defaultProps}
          questionsTotal={5}
          questionsCorrect={3}
        />
      );

      const scoreDisplay = screen.getByTestId('score-display');
      // Check that amber class is applied (60% = 3/5)
      expect(scoreDisplay.innerHTML).toContain('amber');
    });

    it('applies red styling for low score (<60%)', () => {
      render(
        <CompletionScreen
          {...defaultProps}
          questionsTotal={5}
          questionsCorrect={2}
        />
      );

      const scoreDisplay = screen.getByTestId('score-display');
      // Check that red class is applied (40% = 2/5)
      expect(scoreDisplay.innerHTML).toContain('red');
    });
  });

  describe('Accessibility', () => {
    it('buttons are keyboard accessible', async () => {
      const user = userEvent.setup();

      render(
        <CompletionScreen
          {...defaultProps}
          onGoToChapter={mockOnGoToChapter}
          onGoToNext={mockOnGoToNext}
        />
      );

      // Tab to first button
      await user.tab();

      // Should be able to navigate to buttons
      const activeElement = document.activeElement;
      expect(activeElement?.tagName).toBe('BUTTON');
    });

    it('allows Enter key to activate buttons', async () => {
      const user = userEvent.setup();

      render(
        <CompletionScreen
          {...defaultProps}
          onGoToChapter={mockOnGoToChapter}
        />
      );

      const toChapterBtn = screen.getByTestId('to-chapter-btn');
      toChapterBtn.focus();

      await user.keyboard('{Enter}');

      expect(mockOnGoToChapter).toHaveBeenCalledTimes(1);
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<CompletionScreen {...defaultProps} className="custom-class" />);

      expect(screen.getByTestId('completion-screen')).toHaveClass('custom-class');
    });
  });
});
