/**
 * QuestionDeleteDialog - диалог подтверждения удаления вопроса
 *
 * Функциональность:
 * - Простой confirmation dialog
 * - Показывает: "Удалить вопрос {order}?"
 * - Предупреждение о каскадном удалении вариантов
 * - API: DELETE /api/v1/admin/global/questions/{question_id}
 * - Loading state и обработка ошибок
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Button,
  Alert,
  CircularProgress,
  Box,
} from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';
import { useNotify } from 'react-admin';
import { getAuthToken } from '../../../providers/authProvider';
import type { Question } from '../../../types';

const API_URL = 'http://localhost:8000/api/v1';

interface QuestionDeleteDialogProps {
  open: boolean;
  question: Question;
  onClose: () => void;
  onConfirm: () => void;
}

export const QuestionDeleteDialog: React.FC<QuestionDeleteDialogProps> = ({
  open,
  question,
  onClose,
  onConfirm,
}) => {
  const [submitting, setSubmitting] = useState(false);
  const notify = useNotify();

  // Обработчик удаления
  const handleDelete = async () => {
    setSubmitting(true);

    try {
      const token = getAuthToken();

      // DELETE запрос для удаления вопроса (каскадно удалит все options)
      const response = await fetch(
        `${API_URL}/admin/global/questions/${question.id}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка удаления вопроса');
      }

      notify('Вопрос успешно удален', { type: 'success' });
      onConfirm(); // Обновить список вопросов
      onClose();
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Ошибка удаления вопроса',
        { type: 'error' }
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Получение типа вопроса для отображения
  const getQuestionTypeLabel = (type: string) => {
    switch (type) {
      case 'single_choice':
        return 'Один ответ';
      case 'multiple_choice':
        return 'Несколько ответов';
      case 'true_false':
        return 'Верно/Неверно';
      case 'short_answer':
        return 'Короткий ответ';
      default:
        return type;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          Подтверждение удаления
        </Box>
      </DialogTitle>

      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Вы действительно хотите удалить <strong>Вопрос {question.order}</strong>?
        </DialogContentText>

        {/* Информация о вопросе */}
        <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
          <DialogContentText variant="body2" sx={{ mb: 1 }}>
            <strong>Тип:</strong> {getQuestionTypeLabel(question.question_type)}
          </DialogContentText>
          <DialogContentText variant="body2" sx={{ mb: 1 }}>
            <strong>Баллы:</strong> {question.points}
          </DialogContentText>
          <DialogContentText variant="body2">
            <strong>Текст вопроса:</strong>{' '}
            {question.question_text.length > 100
              ? `${question.question_text.substring(0, 100)}...`
              : question.question_text}
          </DialogContentText>
        </Box>

        {/* Предупреждение */}
        <Alert severity="warning">
          <strong>Внимание!</strong> При удалении вопроса будут также удалены все варианты
          ответов ({question.options?.length || 0} вариантов). Это действие нельзя отменить
          через интерфейс.
        </Alert>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={submitting}>
          Отмена
        </Button>
        <Button
          onClick={handleDelete}
          variant="contained"
          color="error"
          disabled={submitting}
          startIcon={submitting && <CircularProgress size={16} />}
        >
          {submitting ? 'Удаление...' : 'Удалить'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
