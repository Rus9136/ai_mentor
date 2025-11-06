/**
 * QuestionsEditor - главный компонент редактора вопросов
 * Встраивается во вкладку "Вопросы" в TestShow
 *
 * Функциональность:
 * - Загрузка списка вопросов через API
 * - Отображение вопросов в виде списка карточек
 * - Кнопка "Добавить вопрос"
 * - Loading и Empty states
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Fade,
  Collapse,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useNotify } from 'react-admin';
import type { Question } from '../../../types';
import { getAuthToken } from '../../../providers/authProvider';
import { QuestionCard } from './QuestionCard';
import { QuestionCreateDialog } from './QuestionCreateDialog';

const API_URL = 'http://localhost:8000/api/v1';

interface QuestionsEditorProps {
  testId: number;
  isSchoolTest?: boolean;
  readOnly?: boolean;
}

export const QuestionsEditor: React.FC<QuestionsEditorProps> = ({ testId, isSchoolTest = false, readOnly = false }) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const notify = useNotify();

  // Загрузка списка вопросов
  const fetchQuestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = getAuthToken();
      const endpoint = isSchoolTest
        ? `${API_URL}/admin/school/tests/${testId}/questions`
        : `${API_URL}/admin/global/tests/${testId}/questions`;
      const response = await fetch(
        endpoint,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setQuestions(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка загрузки вопросов';
      setError(errorMessage);
      notify(errorMessage, { type: 'error' });
    } finally {
      setLoading(false);
    }
  }, [testId, isSchoolTest, notify]);

  // Загрузка при монтировании
  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);

  // Обработчик обновления вопроса
  const handleUpdateQuestion = useCallback(
    async (updatedQuestion: Question) => {
      try {
        const token = getAuthToken();

        // 1. Обновляем вопрос (без options)
        const questionEndpoint = isSchoolTest
          ? `${API_URL}/admin/school/questions/${updatedQuestion.id}`
          : `${API_URL}/admin/global/questions/${updatedQuestion.id}`;
        const questionResponse = await fetch(
          questionEndpoint,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              order: updatedQuestion.order,
              question_type: updatedQuestion.question_type,
              question_text: updatedQuestion.question_text,
              explanation: updatedQuestion.explanation || undefined,
              points: updatedQuestion.points,
            }),
          }
        );

        if (!questionResponse.ok) {
          const errorData = await questionResponse.json();
          throw new Error(errorData.detail || 'Ошибка обновления вопроса');
        }

        // 2. Обработка options
        const oldOptions = questions.find(q => q.id === updatedQuestion.id)?.options || [];
        const newOptions = updatedQuestion.options || [];

        // 2a. Удаляем options, которых нет в новом списке
        for (const oldOption of oldOptions) {
          const stillExists = newOptions.some(opt => opt.id === oldOption.id);
          if (!stillExists && oldOption.id) {
            await fetch(isSchoolTest ? `${API_URL}/admin/school/options/${oldOption.id}` : `${API_URL}/admin/global/options/${oldOption.id}`, {
              method: 'DELETE',
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });
          }
        }

        // 2b. Создаем или обновляем options
        for (const option of newOptions) {
          if (option.id) {
            // Обновляем существующий option
            await fetch(isSchoolTest ? `${API_URL}/admin/school/options/${option.id}` : `${API_URL}/admin/global/options/${option.id}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                order: option.order,
                option_text: option.option_text,
                is_correct: option.is_correct,
              }),
            });
          } else {
            // Создаем новый option
            await fetch(isSchoolTest ? `${API_URL}/admin/school/questions/${updatedQuestion.id}/options` : `${API_URL}/admin/global/questions/${updatedQuestion.id}/options`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify({
                order: option.order,
                option_text: option.option_text,
                is_correct: option.is_correct,
              }),
            });
          }
        }

        notify('Вопрос успешно обновлен', { type: 'success' });
        await fetchQuestions(); // Перезагрузка списка
      } catch (error) {
        notify(
          error instanceof Error ? error.message : 'Ошибка обновления вопроса',
          { type: 'error' }
        );
      }
    },
    [notify, fetchQuestions, questions]
  );

  // Обработчик удаления вопроса
  const handleDeleteQuestion = useCallback(
    async (questionId: number) => {
      try {
        const token = getAuthToken();
        const response = await fetch(
          isSchoolTest ? `${API_URL}/admin/school/questions/${questionId}` : `${API_URL}/admin/global/questions/${questionId}`,
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
        await fetchQuestions(); // Перезагрузка списка
      } catch (error) {
        notify(
          error instanceof Error ? error.message : 'Ошибка удаления вопроса',
          { type: 'error' }
        );
      }
    },
    [notify, fetchQuestions]
  );

  // Loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button onClick={fetchQuestions} variant="outlined">
          Повторить попытку
        </Button>
      </Box>
    );
  }

  return (
    <Fade in timeout={500}>
      <Box sx={{ p: 3 }}>
        {/* Заголовок с счетчиком и кнопкой "Добавить" */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" color="text.primary">
            Вопросы теста ({questions.length})
          </Typography>
          {!readOnly && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-2px)',
                },
              }}
            >
              Добавить вопрос
            </Button>
          )}
        </Box>

        {/* Empty state */}
        <Collapse in={questions.length === 0}>
          <Alert severity="info">
            Вопросов пока нет. Нажмите "Добавить вопрос" чтобы создать первый вопрос.
          </Alert>
        </Collapse>

        {/* Список вопросов */}
        {questions.length > 0 && (
          <Box>
            {questions
              .sort((a, b) => a.order - b.order)
              .map((question, index) => (
                <Fade
                  key={question.id}
                  in
                  timeout={300}
                  style={{ transitionDelay: `${index * 50}ms` }}
                >
                  <div>
                    <QuestionCard
                      question={question}
                      onUpdate={handleUpdateQuestion}
                      onDelete={handleDeleteQuestion}
                      readOnly={readOnly}
                    />
                  </div>
                </Fade>
              ))}
          </Box>
        )}

        {/* Диалог создания вопроса */}
        <QuestionCreateDialog
          open={createDialogOpen}
          testId={testId}
          order={questions.length + 1}
          onClose={() => setCreateDialogOpen(false)}
          onSuccess={fetchQuestions}
          isSchoolTest={isSchoolTest}
        />
      </Box>
    </Fade>
  );
};
