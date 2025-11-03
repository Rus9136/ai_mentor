/**
 * QuestionCard - карточка одного вопроса
 *
 * Два режима:
 * - View режим (default): отображение вопроса с вариантами
 * - Edit режим: встроенная форма QuestionForm
 */

import { useState } from 'react';
import {
  Paper,
  Box,
  Typography,
  Chip,
  IconButton,
  Alert,
  Tooltip,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ToggleOnIcon from '@mui/icons-material/ToggleOn';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import type { Question, QuestionType as QuestionTypeEnum } from '../../../types';
import { QuestionForm } from './QuestionForm';
import { QuestionOptionsList } from './QuestionOptionsList';
import { QuestionDeleteDialog } from './QuestionDeleteDialog';

interface QuestionCardProps {
  question: Question;
  onUpdate: (question: Question) => void;
  onDelete: (questionId: number) => void;
}

// Маппинг типов вопросов на русский язык с цветами и иконками
const questionTypeConfig: Record<
  QuestionTypeEnum,
  {
    label: string;
    color: 'primary' | 'secondary' | 'success' | 'warning';
    icon: React.ReactElement;
  }
> = {
  single_choice: {
    label: 'Один ответ',
    color: 'primary',
    icon: <RadioButtonCheckedIcon fontSize="small" />
  },
  multiple_choice: {
    label: 'Несколько ответов',
    color: 'secondary',
    icon: <CheckBoxIcon fontSize="small" />
  },
  true_false: {
    label: 'Верно/Неверно',
    color: 'success',
    icon: <ToggleOnIcon fontSize="small" />
  },
  short_answer: {
    label: 'Короткий ответ',
    color: 'warning',
    icon: <TextFieldsIcon fontSize="small" />
  },
};

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  onUpdate,
  onDelete,
}) => {
  const [editing, setEditing] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Edit режим: встроенная форма
  if (editing) {
    return (
      <Paper
        elevation={3}
        sx={{
          p: 2,
          mb: 2,
          border: '2px solid',
          borderColor: 'primary.main',
          backgroundColor: 'background.paper',
        }}
      >
        <QuestionForm
          question={question}
          onSave={async (updatedQuestion) => {
            // Объединяем с существующими данными
            await onUpdate({
              ...question,
              ...updatedQuestion,
            });
            setEditing(false);
          }}
          onCancel={() => setEditing(false)}
        />
      </Paper>
    );
  }

  // View режим: отображение вопроса
  const typeConfig = questionTypeConfig[question.question_type];

  return (
    <>
      <Paper
        elevation={2}
        sx={{
          p: 2,
          mb: 2,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 2,
          transition: 'box-shadow 0.2s, transform 0.2s',
          '&:hover': {
            elevation: 4,
            boxShadow: 4,
            transform: 'translateY(-2px)',
          },
        }}
      >
        {/* Основное содержимое */}
        <Box sx={{ flex: 1 }}>
          {/* Заголовок с типом и баллами */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle1" fontWeight="bold" color="text.primary">
              Вопрос {question.order}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                label={typeConfig.label}
                color={typeConfig.color}
                size="small"
                icon={typeConfig.icon}
              />
              <Chip
                label={`${question.points} ${question.points === 1 ? 'балл' : 'балла'}`}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>

          {/* Текст вопроса */}
          <Typography variant="body1" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
            {question.question_text}
          </Typography>

          {/* Список вариантов ответов */}
          <QuestionOptionsList
            options={question.options}
            questionType={question.question_type}
          />

          {/* Пояснение к правильному ответу */}
          {question.explanation && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Пояснение:</strong> {question.explanation}
              </Typography>
            </Alert>
          )}
        </Box>

        {/* Кнопки действий */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Tooltip title="Редактировать вопрос" placement="left">
            <IconButton
              onClick={() => setEditing(true)}
              color="primary"
              size="small"
              aria-label="Редактировать вопрос"
              sx={{
                transition: 'all 0.2s',
                '&:hover': {
                  backgroundColor: 'primary.light',
                  transform: 'scale(1.1)',
                },
              }}
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Удалить вопрос" placement="left">
            <IconButton
              onClick={() => setDeleteDialogOpen(true)}
              color="error"
              size="small"
              aria-label="Удалить вопрос"
              sx={{
                transition: 'all 0.2s',
                '&:hover': {
                  backgroundColor: 'error.light',
                  transform: 'scale(1.1)',
                },
              }}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Диалог подтверждения удаления */}
      <QuestionDeleteDialog
        open={deleteDialogOpen}
        question={question}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={() => {
          onDelete(question.id);
          setDeleteDialogOpen(false);
        }}
      />
    </>
  );
};
