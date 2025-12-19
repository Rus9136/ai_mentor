import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SelfAssessment } from '@/components/learning/SelfAssessment';

describe('SelfAssessment', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders component with data-testid', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      expect(screen.getByTestId('self-assessment')).toBeInTheDocument();
    });

    it('renders title', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      expect(screen.getByTestId('self-assessment-title')).toBeInTheDocument();
    });

    it('renders three rating options', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      expect(screen.getByTestId('rating-understood')).toBeInTheDocument();
      expect(screen.getByTestId('rating-questions')).toBeInTheDocument();
      expect(screen.getByTestId('rating-difficult')).toBeInTheDocument();
    });

    it('renders submit button', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      expect(screen.getByTestId('submit-assessment')).toBeInTheDocument();
    });
  });

  describe('Rating Selection', () => {
    it('allows selecting "understood" rating', async () => {
      const user = userEvent.setup();

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));

      // Check visual feedback (button should have selected styling)
      const understoodBtn = screen.getByTestId('rating-understood');
      expect(understoodBtn.className).toMatch(/green|selected/);
    });

    it('allows selecting "questions" rating', async () => {
      const user = userEvent.setup();

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-questions'));

      const questionsBtn = screen.getByTestId('rating-questions');
      expect(questionsBtn.className).toMatch(/amber|selected/);
    });

    it('allows selecting "difficult" rating', async () => {
      const user = userEvent.setup();

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-difficult'));

      const difficultBtn = screen.getByTestId('rating-difficult');
      expect(difficultBtn.className).toMatch(/red|selected/);
    });

    it('changes selection when different rating clicked', async () => {
      const user = userEvent.setup();

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));
      await user.click(screen.getByTestId('rating-difficult'));

      // Difficult should be selected, understood should not
      const difficultBtn = screen.getByTestId('rating-difficult');
      expect(difficultBtn.className).toMatch(/red|selected/);
    });
  });

  describe('Submit Button State', () => {
    it('disables submit button when no rating selected', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      expect(screen.getByTestId('submit-assessment')).toBeDisabled();
    });

    it('enables submit button when rating is selected', async () => {
      const user = userEvent.setup();

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));

      expect(screen.getByTestId('submit-assessment')).toBeEnabled();
    });
  });

  describe('Submission', () => {
    it('calls onSubmit with "understood" rating', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));
      await user.click(screen.getByTestId('submit-assessment'));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('understood');
      });
    });

    it('calls onSubmit with "questions" rating', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-questions'));
      await user.click(screen.getByTestId('submit-assessment'));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('questions');
      });
    });

    it('calls onSubmit with "difficult" rating', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-difficult'));
      await user.click(screen.getByTestId('submit-assessment'));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith('difficult');
      });
    });
  });

  describe('After Submission', () => {
    it('shows submitted confirmation', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));
      await user.click(screen.getByTestId('submit-assessment'));

      await waitFor(() => {
        expect(screen.getByTestId('assessment-submitted')).toBeInTheDocument();
      });
    });

    it('hides submit button after submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));
      await user.click(screen.getByTestId('submit-assessment'));

      await waitFor(() => {
        expect(screen.queryByTestId('submit-assessment')).not.toBeInTheDocument();
      });
    });

    it('disables rating buttons after submission', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockResolvedValue(undefined);

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));
      await user.click(screen.getByTestId('submit-assessment'));

      await waitFor(() => {
        expect(screen.getByTestId('rating-understood')).toBeDisabled();
        expect(screen.getByTestId('rating-questions')).toBeDisabled();
        expect(screen.getByTestId('rating-difficult')).toBeDisabled();
      });
    });
  });

  describe('Pre-selected Rating', () => {
    it('shows pre-selected rating when currentRating provided', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} currentRating="understood" />);

      // Should show as already submitted
      expect(screen.getByTestId('assessment-submitted')).toBeInTheDocument();
    });

    it('disables all buttons when currentRating provided', () => {
      render(<SelfAssessment onSubmit={mockOnSubmit} currentRating="understood" />);

      expect(screen.getByTestId('rating-understood')).toBeDisabled();
      expect(screen.getByTestId('rating-questions')).toBeDisabled();
      expect(screen.getByTestId('rating-difficult')).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('handles submission error gracefully', async () => {
      const user = userEvent.setup();
      mockOnSubmit.mockRejectedValue(new Error('Submission failed'));

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      await user.click(screen.getByTestId('rating-understood'));
      await user.click(screen.getByTestId('submit-assessment'));

      // Should not show submitted state on error
      await waitFor(() => {
        expect(screen.queryByTestId('assessment-submitted')).not.toBeInTheDocument();
      });

      // Submit button should still be visible
      expect(screen.getByTestId('submit-assessment')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('rating buttons are keyboard accessible', async () => {
      const user = userEvent.setup();

      render(<SelfAssessment onSubmit={mockOnSubmit} />);

      // Tab to first rating
      await user.tab();
      await user.tab();
      await user.tab();

      // Should be able to navigate with keyboard
      const activeElement = document.activeElement;
      expect(activeElement?.getAttribute('data-testid')).toMatch(/rating-/);
    });
  });
});
