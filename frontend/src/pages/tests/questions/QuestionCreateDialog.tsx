/**
 * QuestionCreateDialog - диалог создания нового вопроса
 *
 * Функциональность:
 * - Material UI Dialog (не fullscreen, maxWidth="md")
 * - Использует QuestionForm внутри
 * - Автоматически определяет order
 * - API вызов: POST /api/v1/admin/global/tests/{testId}/questions
 * - Loading state и обработка ошибок
 * - Уведомления через useNotify
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  CircularProgress,
  Box,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useNotify } from 'react-admin';
import { QuestionForm } from './QuestionForm';
import { getAuthToken } from '../../../providers/authProvider';
import type { Question } from '../../../types';

const API_URL = 'http://localhost:8000/api/v1';

interface QuestionCreateDialogProps {
  open: boolean;
  testId: number;
  order: number;
  onClose: () => void;
  onSuccess: () => void;
  isSchoolTest?: boolean;
}

export const QuestionCreateDialog: React.FC<QuestionCreateDialogProps> = ({
  open,
  testId,
  order,
  onClose,
  onSuccess,
  isSchoolTest = false,
}) => {
  const [submitting, setSubmitting] = useState(false);
  const notify = useNotify();

  // Обработчик сохранения вопроса
  const handleSave = async (questionData: Partial<Question>) => {
    setSubmitting(true);

    try {
      const token = getAuthToken();

      // Подготовка payload
      const payload = {
        test_id: testId,
        order,
        question_type: questionData.question_type,
        question_text: questionData.question_text?.trim(),
        explanation: questionData.explanation?.trim() || undefined,
        points: questionData.points || 1,
        options: questionData.options || [],
      };

      // POST запрос для создания вопроса (с вложенными options)
      const endpoint = isSchoolTest
        ? `${API_URL}/admin/school/tests/${testId}/questions`
        : `${API_URL}/admin/global/tests/${testId}/questions`;
      const response = await fetch(
        endpoint,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка создания вопроса');
      }

      notify('Вопрос успешно создан', { type: 'success' });
      onSuccess(); // Обновить список вопросов
      handleClose();
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Ошибка создания вопроса',
        { type: 'error' }
      );
    } finally {
      setSubmitting(false);
    }
  };

  // Закрытие диалога
  const handleClose = () => {
    if (!submitting) {
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={submitting}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Добавить вопрос
          <IconButton
            onClick={handleClose}
            disabled={submitting}
            aria-label="Закрыть"
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        {submitting ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: 300,
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          <QuestionForm
            onSave={handleSave}
            onCancel={handleClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};
