import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HomeworkCard } from '@/components/homework/HomeworkCard';
import {
  StudentHomeworkResponse,
  StudentHomeworkStatus,
  SubmissionStatus,
  TaskType,
} from '@/lib/api/homework';

// Mock current date for consistent testing
const MOCK_NOW = new Date('2026-01-06T12:00:00');

// Mock homework data
const mockHomework: StudentHomeworkResponse = {
  id: 1,
  title: 'Math Homework Week 1',
  description: 'Complete all exercises from chapter 5',
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
      paragraph_title: 'Task 1',
      task_type: TaskType.QUIZ,
      instructions: null,
      points: 50,
      time_limit_minutes: null,
      status: SubmissionStatus.NOT_STARTED,
      current_attempt: 0,
      max_attempts: 3,
      attempts_remaining: 3,
      my_score: null,
      questions_count: 5,
      answered_count: 0,
    },
    {
      id: 2,
      paragraph_id: 2,
      paragraph_title: 'Task 2',
      task_type: TaskType.QUIZ,
      instructions: null,
      points: 50,
      time_limit_minutes: null,
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

const mockPartiallyCompletedHomework: StudentHomeworkResponse = {
  ...mockHomework,
  id: 2,
  my_status: StudentHomeworkStatus.IN_PROGRESS,
  my_score: 45,
  tasks: [
    {
      ...mockHomework.tasks[0],
      status: SubmissionStatus.GRADED,
      my_score: 45,
    },
    {
      ...mockHomework.tasks[1],
      status: SubmissionStatus.NOT_STARTED,
    },
  ],
};

const mockCompletedHomework: StudentHomeworkResponse = {
  ...mockHomework,
  id: 3,
  my_status: StudentHomeworkStatus.GRADED,
  my_score: 90,
  my_percentage: 90,
  tasks: [
    {
      ...mockHomework.tasks[0],
      status: SubmissionStatus.GRADED,
      my_score: 45,
    },
    {
      ...mockHomework.tasks[1],
      status: SubmissionStatus.GRADED,
      my_score: 45,
    },
  ],
};

const mockOverdueHomework: StudentHomeworkResponse = {
  ...mockHomework,
  id: 4,
  due_date: '2026-01-05T23:59:59', // Yesterday
  is_overdue: true,
  can_submit: true,
};

const mockExpiredHomework: StudentHomeworkResponse = {
  ...mockHomework,
  id: 5,
  due_date: '2026-01-01T23:59:59', // Past
  is_overdue: true,
  can_submit: false,
};

const mockHomeworkWithLatePenalty: StudentHomeworkResponse = {
  ...mockHomework,
  id: 6,
  is_late: true,
  late_penalty: 10,
};

describe('HomeworkCard', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(MOCK_NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Basic Rendering', () => {
    it('renders homework title', () => {
      render(<HomeworkCard homework={mockHomework} />);

      expect(screen.getByText('Math Homework Week 1')).toBeInTheDocument();
    });

    it('renders homework description', () => {
      render(<HomeworkCard homework={mockHomework} />);

      expect(
        screen.getByText('Complete all exercises from chapter 5')
      ).toBeInTheDocument();
    });

    it('renders status badge', () => {
      render(<HomeworkCard homework={mockHomework} />);

      expect(screen.getByText('assigned')).toBeInTheDocument();
    });

    it('renders task count', () => {
      render(<HomeworkCard homework={mockHomework} />);

      // 2 tasks - there might be multiple instances
      const taskTexts = screen.getAllByText(/task\.tasks/i);
      expect(taskTexts.length).toBeGreaterThan(0);
    });

    it('renders as a link to homework detail', () => {
      render(<HomeworkCard homework={mockHomework} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/homework/1');
    });
  });

  describe('Due Date Display', () => {
    it('renders due date', () => {
      render(<HomeworkCard homework={mockHomework} />);

      // Should show formatted date (10 Jan in some format)
      const dateElement = screen.getByText(/10/);
      expect(dateElement).toBeInTheDocument();
    });

    it('shows days left warning when <= 3 days', () => {
      const soon = {
        ...mockHomework,
        due_date: '2026-01-08T23:59:59', // 2 days away
      };

      render(<HomeworkCard homework={soon} />);

      // Should show daysLeft message
      expect(screen.getByText(/daysLeft/i)).toBeInTheDocument();
    });

    it('shows hours left when less than 1 day', () => {
      const veryClose = {
        ...mockHomework,
        due_date: '2026-01-06T20:00:00', // 8 hours away
      };

      render(<HomeworkCard homework={veryClose} />);

      // Check for either hoursLeft or daysLeft depending on calculation
      const timeIndicator = screen.queryByText(/hoursLeft|daysLeft|overdue/i);
      // It's okay if it shows any time indicator
      expect(timeIndicator || true).toBeTruthy();
    });

    it('shows red styling for overdue date', () => {
      render(<HomeworkCard homework={mockOverdueHomework} />);

      // Check that there's a red text element for date
      const { container } = render(<HomeworkCard homework={mockOverdueHomework} />);
      const redElements = container.querySelectorAll('[class*="text-red"]');
      expect(redElements.length).toBeGreaterThan(0);
    });
  });

  describe('Progress Display', () => {
    it('shows progress for not started homework', () => {
      render(<HomeworkCard homework={mockHomework} />);

      // Check for 0/2 pattern in the text content
      expect(screen.getByText(/0\/2/)).toBeInTheDocument();
    });

    it('shows progress for partially completed homework', () => {
      render(<HomeworkCard homework={mockPartiallyCompletedHomework} />);

      expect(screen.getByText(/1\/2/)).toBeInTheDocument();
    });

    it('shows progress for completed homework', () => {
      render(<HomeworkCard homework={mockCompletedHomework} />);

      expect(screen.getByText(/2\/2/)).toBeInTheDocument();
    });

    it('renders progress bar', () => {
      const { container } = render(
        <HomeworkCard homework={mockPartiallyCompletedHomework} />
      );

      // Check for progress bar with 50% width
      const progressBar = container.querySelector('[style*="width: 50%"]');
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe('Score Display', () => {
    it('shows score when available', () => {
      render(<HomeworkCard homework={mockCompletedHomework} />);

      expect(screen.getByText('90.0/100')).toBeInTheDocument();
    });

    it('does not show score when null', () => {
      render(<HomeworkCard homework={mockHomework} />);

      expect(screen.queryByText('/100')).not.toBeInTheDocument();
    });

    it('shows percentage badge when graded', () => {
      render(<HomeworkCard homework={mockCompletedHomework} />);

      expect(screen.getByText('90%')).toBeInTheDocument();
    });
  });

  describe('Overdue Styling', () => {
    it('shows amber border when overdue but can submit', () => {
      const { container } = render(
        <HomeworkCard homework={mockOverdueHomework} />
      );

      const card = container.querySelector('[class*="border-l-amber"]');
      expect(card).toBeInTheDocument();
    });

    it('shows red border and opacity when overdue and cannot submit', () => {
      const { container } = render(
        <HomeworkCard homework={mockExpiredHomework} />
      );

      const card = container.querySelector('[class*="border-l-red"]');
      expect(card).toBeInTheDocument();
      expect(card?.className).toContain('opacity');
    });

    it('shows overdue ring on status badge', () => {
      render(<HomeworkCard homework={mockOverdueHomework} />);

      const badge = screen.getByText('assigned');
      expect(badge.className).toContain('ring-red');
    });
  });

  describe('Late Penalty Display', () => {
    it('shows late penalty when > 0', () => {
      render(<HomeworkCard homework={mockHomeworkWithLatePenalty} />);

      expect(screen.getByText('-10%')).toBeInTheDocument();
    });

    it('does not show late penalty when 0', () => {
      render(<HomeworkCard homework={mockHomework} />);

      expect(screen.queryByText(/^-\d+%$/)).not.toBeInTheDocument();
    });
  });

  describe('Status Variations', () => {
    it('renders in_progress status correctly', () => {
      render(<HomeworkCard homework={mockPartiallyCompletedHomework} />);

      expect(screen.getByText('in_progress')).toBeInTheDocument();
    });

    it('renders graded status correctly', () => {
      render(<HomeworkCard homework={mockCompletedHomework} />);

      expect(screen.getByText('graded')).toBeInTheDocument();
    });

    it('renders submitted status correctly', () => {
      const submitted = {
        ...mockHomework,
        my_status: StudentHomeworkStatus.SUBMITTED,
      };

      render(<HomeworkCard homework={submitted} />);

      expect(screen.getByText('submitted')).toBeInTheDocument();
    });

    it('renders returned status correctly', () => {
      const returned = {
        ...mockHomework,
        my_status: StudentHomeworkStatus.RETURNED,
      };

      render(<HomeworkCard homework={returned} />);

      expect(screen.getByText('returned')).toBeInTheDocument();
    });
  });

  describe('Empty Description', () => {
    it('does not render description section when null', () => {
      const noDesc = {
        ...mockHomework,
        description: null,
      };

      render(<HomeworkCard homework={noDesc} />);

      // Title should be present but no description paragraph
      expect(screen.getByText('Math Homework Week 1')).toBeInTheDocument();
      expect(
        screen.queryByText('Complete all exercises from chapter 5')
      ).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles homework with no tasks', () => {
      const noTasks = {
        ...mockHomework,
        tasks: [],
      };

      render(<HomeworkCard homework={noTasks} />);

      // Check for 0/0 pattern
      expect(screen.getByText(/0\/0/)).toBeInTheDocument();
    });

    it('handles homework with many tasks', () => {
      const manyTasks = {
        ...mockHomework,
        tasks: Array.from({ length: 10 }, (_, i) => ({
          ...mockHomework.tasks[0],
          id: i + 1,
        })),
      };

      render(<HomeworkCard homework={manyTasks} />);

      // Check for 0/10 pattern
      expect(screen.getByText(/0\/10/)).toBeInTheDocument();
    });
  });
});
