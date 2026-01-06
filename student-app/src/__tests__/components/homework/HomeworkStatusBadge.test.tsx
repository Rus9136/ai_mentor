import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HomeworkStatusBadge } from '@/components/homework/HomeworkStatusBadge';
import { StudentHomeworkStatus } from '@/lib/api/homework';

describe('HomeworkStatusBadge', () => {
  describe('Rendering', () => {
    it('renders assigned status', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.ASSIGNED} />);
      expect(screen.getByText('assigned')).toBeInTheDocument();
    });

    it('renders in_progress status', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.IN_PROGRESS} />);
      expect(screen.getByText('in_progress')).toBeInTheDocument();
    });

    it('renders submitted status', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.SUBMITTED} />);
      expect(screen.getByText('submitted')).toBeInTheDocument();
    });

    it('renders graded status', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.GRADED} />);
      expect(screen.getByText('graded')).toBeInTheDocument();
    });

    it('renders returned status', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.RETURNED} />);
      expect(screen.getByText('returned')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('applies blue styling for assigned', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.ASSIGNED} />);
      const badge = screen.getByText('assigned');
      expect(badge.className).toContain('bg-blue-100');
      expect(badge.className).toContain('text-blue-700');
    });

    it('applies amber styling for in_progress', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.IN_PROGRESS} />);
      const badge = screen.getByText('in_progress');
      expect(badge.className).toContain('bg-amber-100');
      expect(badge.className).toContain('text-amber-700');
    });

    it('applies green styling for submitted', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.SUBMITTED} />);
      const badge = screen.getByText('submitted');
      expect(badge.className).toContain('bg-green-100');
      expect(badge.className).toContain('text-green-700');
    });

    it('applies purple styling for graded', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.GRADED} />);
      const badge = screen.getByText('graded');
      expect(badge.className).toContain('bg-purple-100');
      expect(badge.className).toContain('text-purple-700');
    });

    it('applies orange styling for returned', () => {
      render(<HomeworkStatusBadge status={StudentHomeworkStatus.RETURNED} />);
      const badge = screen.getByText('returned');
      expect(badge.className).toContain('bg-orange-100');
      expect(badge.className).toContain('text-orange-700');
    });
  });

  describe('Overdue state', () => {
    it('adds ring styling when overdue', () => {
      render(
        <HomeworkStatusBadge
          status={StudentHomeworkStatus.ASSIGNED}
          isOverdue={true}
        />
      );
      const badge = screen.getByText('assigned');
      expect(badge.className).toContain('ring-2');
      expect(badge.className).toContain('ring-red-400');
    });

    it('does not add ring styling when not overdue', () => {
      render(
        <HomeworkStatusBadge
          status={StudentHomeworkStatus.ASSIGNED}
          isOverdue={false}
        />
      );
      const badge = screen.getByText('assigned');
      expect(badge.className).not.toContain('ring-2');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(
        <HomeworkStatusBadge
          status={StudentHomeworkStatus.ASSIGNED}
          className="my-custom-class"
        />
      );
      const badge = screen.getByText('assigned');
      expect(badge.className).toContain('my-custom-class');
    });
  });
});
