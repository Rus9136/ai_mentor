/**
 * QuestionForm - форма создания/редактирования вопроса
 *
 * Поля:
 * - Тип вопроса (SelectInput, 4 типа)
 * - Текст вопроса (TextField multiline, required, maxLength 1000)
 * - Варианты ответов (динамический список для single/multiple choice)
 * - Пояснение (TextField multiline, optional)
 * - Баллы (NumberInput)
 *
 * Валидация:
 * - Текст вопроса обязателен
 * - Минимум 2 варианта для single/multiple choice
 * - Минимум 1 правильный ответ
 * - Для single_choice: только 1 правильный ответ
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  MenuItem,
  Button,
  IconButton,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  Checkbox,
  Alert,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import type { Question, QuestionType as QuestionTypeEnum } from '../../../types';
import { QuestionType } from '../../../types';

interface QuestionFormProps {
  question?: Question;
  onSave: (question: Partial<Question>) => void;
  onCancel: () => void;
}

interface OptionFormData {
  id?: number;
  option_text: string;
  is_correct: boolean;
  order: number;
}

interface QuestionFormData {
  question_type: QuestionTypeEnum;
  question_text: string;
  explanation: string;
  points: number;
  options: OptionFormData[];
}

export const QuestionForm: React.FC<QuestionFormProps> = ({
  question,
  onSave,
  onCancel,
}) => {
  // Инициализация формы
  const [formData, setFormData] = useState<QuestionFormData>({
    question_type: question?.question_type || QuestionType.SINGLE_CHOICE,
    question_text: question?.question_text || '',
    explanation: question?.explanation || '',
    points: question?.points || 1,
    options: question?.options?.map((opt) => ({
      id: opt.id,
      option_text: opt.option_text,
      is_correct: opt.is_correct,
      order: opt.order,
    })) || [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Инициализация опций для true_false
  useEffect(() => {
    if (formData.question_type === QuestionType.TRUE_FALSE && formData.options.length === 0) {
      setFormData((prev) => ({
        ...prev,
        options: [
          { option_text: 'Верно', is_correct: false, order: 1 },
          { option_text: 'Неверно', is_correct: false, order: 2 },
        ],
      }));
    }
  }, [formData.question_type, formData.options.length]);

  // Обработчик изменения типа вопроса
  const handleTypeChange = (newType: QuestionTypeEnum) => {
    setFormData((prev) => {
      // Если переключаемся на true_false, заменяем опции
      if (newType === QuestionType.TRUE_FALSE) {
        return {
          ...prev,
          question_type: newType,
          options: [
            { option_text: 'Верно', is_correct: false, order: 1 },
            { option_text: 'Неверно', is_correct: false, order: 2 },
          ],
        };
      }
      // Если переключаемся на short_answer, очищаем опции
      if (newType === QuestionType.SHORT_ANSWER) {
        return {
          ...prev,
          question_type: newType,
          options: [],
        };
      }
      // Для single/multiple choice - оставляем текущие опции или создаем пустые
      return {
        ...prev,
        question_type: newType,
        options: prev.options.length > 0 ? prev.options : [
          { option_text: '', is_correct: false, order: 1 },
          { option_text: '', is_correct: false, order: 2 },
        ],
      };
    });
  };

  // Добавление нового варианта ответа
  const handleAddOption = () => {
    setFormData((prev) => ({
      ...prev,
      options: [
        ...prev.options,
        {
          option_text: '',
          is_correct: false,
          order: prev.options.length + 1,
        },
      ],
    }));
  };

  // Удаление варианта ответа
  const handleRemoveOption = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index).map((opt, i) => ({
        ...opt,
        order: i + 1,
      })),
    }));
  };

  // Изменение текста варианта
  const handleOptionTextChange = (index: number, text: string) => {
    setFormData((prev) => ({
      ...prev,
      options: prev.options.map((opt, i) =>
        i === index ? { ...opt, option_text: text } : opt
      ),
    }));
  };

  // Переключение правильного ответа (для single_choice)
  const handleRadioChange = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      options: prev.options.map((opt, i) => ({
        ...opt,
        is_correct: i === index,
      })),
    }));
  };

  // Переключение правильного ответа (для multiple_choice и true_false)
  const handleCheckboxChange = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      options: prev.options.map((opt, i) =>
        i === index ? { ...opt, is_correct: !opt.is_correct } : opt
      ),
    }));
  };

  // Валидация формы
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Проверка текста вопроса
    if (!formData.question_text.trim()) {
      newErrors.question_text = 'Текст вопроса обязателен';
    }
    if (formData.question_text.length > 1000) {
      newErrors.question_text = 'Текст вопроса не должен превышать 1000 символов';
    }

    // Проверка баллов
    if (formData.points < 0.1) {
      newErrors.points = 'Баллы должны быть не менее 0.1';
    }

    // Проверка опций для single/multiple choice и true_false
    if (
      formData.question_type === QuestionType.SINGLE_CHOICE ||
      formData.question_type === QuestionType.MULTIPLE_CHOICE ||
      formData.question_type === QuestionType.TRUE_FALSE
    ) {
      // Минимум 2 варианта
      if (formData.options.length < 2) {
        newErrors.options = 'Должно быть минимум 2 варианта ответа';
      }

      // Проверка на пустые варианты
      const hasEmptyOptions = formData.options.some((opt) => !opt.option_text.trim());
      if (hasEmptyOptions) {
        newErrors.options = 'Все варианты ответов должны иметь текст';
      }

      // Проверка наличия правильного ответа
      const correctCount = formData.options.filter((opt) => opt.is_correct).length;
      if (correctCount === 0) {
        newErrors.options = 'Должен быть выбран хотя бы один правильный ответ';
      }

      // Для single_choice - только один правильный
      if (formData.question_type === QuestionType.SINGLE_CHOICE && correctCount > 1) {
        newErrors.options = 'Для типа "Один ответ" должен быть выбран только один правильный вариант';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Сохранение формы
  const handleSubmit = () => {
    if (!validateForm()) {
      return;
    }

    // Передаем данные формы как Partial<Question>
    // OptionFormData совместим с QuestionOption для создания/обновления
    onSave(formData as Partial<Question>);
  };

  // Нужны ли опции для текущего типа вопроса
  const needsOptions =
    formData.question_type === QuestionType.SINGLE_CHOICE ||
    formData.question_type === QuestionType.MULTIPLE_CHOICE ||
    formData.question_type === QuestionType.TRUE_FALSE;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Тип вопроса */}
      <TextField
        select
        fullWidth
        label="Тип вопроса"
        value={formData.question_type}
        onChange={(e) => handleTypeChange(e.target.value as QuestionTypeEnum)}
      >
        <MenuItem value={QuestionType.SINGLE_CHOICE}>Один ответ</MenuItem>
        <MenuItem value={QuestionType.MULTIPLE_CHOICE}>Несколько ответов</MenuItem>
        <MenuItem value={QuestionType.TRUE_FALSE}>Верно/Неверно</MenuItem>
        <MenuItem value={QuestionType.SHORT_ANSWER}>Короткий ответ</MenuItem>
      </TextField>

      {/* Текст вопроса */}
      <TextField
        fullWidth
        multiline
        rows={4}
        label="Текст вопроса *"
        value={formData.question_text}
        onChange={(e) => setFormData((prev) => ({ ...prev, question_text: e.target.value }))}
        error={!!errors.question_text}
        helperText={errors.question_text || `${formData.question_text.length}/1000 символов`}
      />

      {/* Баллы */}
      <TextField
        fullWidth
        type="number"
        label="Баллы"
        value={formData.points}
        onChange={(e) => setFormData((prev) => ({ ...prev, points: parseFloat(e.target.value) || 1 }))}
        inputProps={{ min: 0.1, step: 0.5 }}
        error={!!errors.points}
        helperText={errors.points || 'Количество баллов за правильный ответ'}
      />

      {/* Варианты ответов */}
      {needsOptions && (
        <>
          <Divider />
          <Typography variant="subtitle1" fontWeight="bold">
            Варианты ответов
          </Typography>

          {errors.options && (
            <Alert severity="error">{errors.options}</Alert>
          )}

          {formData.question_type === QuestionType.SINGLE_CHOICE && (
            <RadioGroup value={formData.options.findIndex((opt) => opt.is_correct)}>
              {formData.options.map((option, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <FormControlLabel
                    value={index}
                    control={<Radio onChange={() => handleRadioChange(index)} />}
                    label=""
                    sx={{ margin: 0 }}
                  />
                  <TextField
                    fullWidth
                    size="small"
                    label={`Вариант ${index + 1}`}
                    value={option.option_text}
                    onChange={(e) => handleOptionTextChange(index, e.target.value)}
                  />
                  <IconButton
                    color="error"
                    onClick={() => handleRemoveOption(index)}
                    disabled={formData.options.length <= 2}
                    aria-label="Удалить вариант"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              ))}
            </RadioGroup>
          )}

          {(formData.question_type === QuestionType.MULTIPLE_CHOICE ||
            formData.question_type === QuestionType.TRUE_FALSE) && (
            <>
              {formData.options.map((option, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={option.is_correct}
                        onChange={() => handleCheckboxChange(index)}
                      />
                    }
                    label=""
                    sx={{ margin: 0 }}
                  />
                  <TextField
                    fullWidth
                    size="small"
                    label={`Вариант ${index + 1}`}
                    value={option.option_text}
                    onChange={(e) => handleOptionTextChange(index, e.target.value)}
                    disabled={formData.question_type === QuestionType.TRUE_FALSE}
                  />
                  {formData.question_type !== QuestionType.TRUE_FALSE && (
                    <IconButton
                      color="error"
                      onClick={() => handleRemoveOption(index)}
                      disabled={formData.options.length <= 2}
                      aria-label="Удалить вариант"
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
                </Box>
              ))}
            </>
          )}

          {formData.question_type !== QuestionType.TRUE_FALSE && (
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleAddOption}
              sx={{ alignSelf: 'flex-start' }}
            >
              Добавить вариант
            </Button>
          )}
        </>
      )}

      {/* Пояснение для short_answer */}
      {formData.question_type === QuestionType.SHORT_ANSWER && (
        <Alert severity="info">
          Короткий ответ будет проверяться вручную учителем или системой проверки
        </Alert>
      )}

      {/* Пояснение */}
      <TextField
        fullWidth
        multiline
        rows={3}
        label="Пояснение (необязательно)"
        value={formData.explanation}
        onChange={(e) => setFormData((prev) => ({ ...prev, explanation: e.target.value }))}
        helperText="Объяснение правильного ответа для учеников"
      />

      {/* Кнопки действий */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button variant="outlined" onClick={onCancel}>
          Отмена
        </Button>
        <Button variant="contained" onClick={handleSubmit}>
          Сохранить
        </Button>
      </Box>
    </Box>
  );
};
