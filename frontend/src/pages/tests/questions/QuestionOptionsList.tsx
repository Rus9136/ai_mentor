/**
 * QuestionOptionsList - отображение вариантов ответов (read-only)
 *
 * Функциональность:
 * - Список вариантов ответов с визуальным разделением
 * - Правильные ответы выделены (зеленый Chip + CheckCircleIcon)
 * - Неправильные - обычный текст с серым цветом
 * - Для short_answer: показывает специальный текст об ручной проверке
 */

import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Alert,
  Typography,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
} from '@mui/icons-material';
import type { QuestionOption, QuestionType } from '../../../types';
import { QuestionType as QuestionTypeEnum } from '../../../types';

interface QuestionOptionsListProps {
  options: QuestionOption[];
  questionType: QuestionType;
}

export const QuestionOptionsList: React.FC<QuestionOptionsListProps> = ({
  options,
  questionType,
}) => {
  // Для short_answer вариантов нет
  if (questionType === QuestionTypeEnum.SHORT_ANSWER) {
    return (
      <Alert severity="info" icon={false}>
        <Typography variant="body2">
          <strong>Короткий ответ</strong> — ответ проверяется вручную учителем или автоматической системой проверки
        </Typography>
      </Alert>
    );
  }

  // Если нет вариантов (на случай ошибки данных)
  if (!options || options.length === 0) {
    return (
      <Alert severity="warning">
        <Typography variant="body2">
          Варианты ответов не добавлены
        </Typography>
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
        Варианты ответов:
      </Typography>
      <List dense disablePadding>
        {options
          .sort((a, b) => a.order - b.order)
          .map((option) => (
            <ListItem
              key={option.id}
              sx={{
                py: 0.5,
                px: 0,
                alignItems: 'flex-start',
              }}
            >
              <ListItemIcon sx={{ minWidth: 32, mt: 0.5 }}>
                {option.is_correct ? (
                  <CheckCircleIcon color="success" fontSize="small" />
                ) : (
                  <RadioButtonUncheckedIcon
                    sx={{ color: 'text.disabled' }}
                    fontSize="small"
                  />
                )}
              </ListItemIcon>
              <ListItemText
                primary={
                  option.is_correct ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" component="span">
                        {option.option_text}
                      </Typography>
                      <Chip
                        label="Правильно"
                        color="success"
                        size="small"
                        sx={{ height: 20, fontSize: '0.75rem' }}
                      />
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      {option.option_text}
                    </Typography>
                  )
                }
              />
            </ListItem>
          ))}
      </List>
    </Box>
  );
};
