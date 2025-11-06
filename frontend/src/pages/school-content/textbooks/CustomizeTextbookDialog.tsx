import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Box,
  Typography,
} from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { useNotify, useRedirect, useRefresh } from 'react-admin';
import type { Textbook } from '../../../types';
import { customizeTextbook } from '../../../providers/dataProvider';

/**
 * CustomizeTextbookDialog - Диалог для кастомизации (fork) глобального учебника
 *
 * Позволяет школьному администратору создать адаптированную копию глобального учебника
 * для своей школы с возможностью последующего редактирования.
 *
 * Процесс:
 * 1. Показывает информацию об исходном учебнике
 * 2. Запрашивает новое название (с default значением)
 * 3. Опция копирования всего контента (главы + параграфы)
 * 4. Вызывает POST /api/v1/admin/school/textbooks/{id}/customize
 * 5. Редиректит на страницу редактирования нового учебника
 */

interface CustomizeTextbookDialogProps {
  open: boolean;
  onClose: () => void;
  textbook: Textbook;
}

export const CustomizeTextbookDialog = ({
  open,
  onClose,
  textbook,
}: CustomizeTextbookDialogProps) => {
  const notify = useNotify();
  const redirect = useRedirect();
  const refresh = useRefresh();

  const [newTitle, setNewTitle] = useState(`${textbook.title} (адаптировано)`);
  const [copyContent, setCopyContent] = useState(true);
  const [loading, setLoading] = useState(false);

  /**
   * Обработчик кастомизации учебника
   */
  const handleCustomize = async () => {
    setLoading(true);

    try {
      // Вызываем API для fork учебника
      const result = await customizeTextbook(textbook.id, {
        title: newTitle,
        copy_content: copyContent,
      });

      notify('Учебник успешно кастомизирован', { type: 'success' });

      // Закрываем диалог
      onClose();

      // Обновляем список (чтобы увидеть новый учебник во вкладке "Наши учебники")
      refresh();

      // Редиректим на страницу редактирования нового учебника
      // Используем небольшую задержку, чтобы дать время на refresh
      setTimeout(() => {
        redirect('edit', 'school-textbooks', result.id);
      }, 500);
    } catch (error: any) {
      console.error('Ошибка кастомизации учебника:', error);
      notify(
        error.message || 'Ошибка при кастомизации учебника. Попробуйте позже.',
        { type: 'error' }
      );
    } finally {
      setLoading(false);
    }
  };

  /**
   * Обработчик отмены (reset состояния)
   */
  const handleClose = () => {
    if (!loading) {
      setNewTitle(`${textbook.title} (адаптировано)`);
      setCopyContent(true);
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="customize-textbook-dialog-title"
    >
      <DialogTitle id="customize-textbook-dialog-title">
        <Box display="flex" alignItems="center" gap={1}>
          <ContentCopyIcon color="primary" />
          <Typography variant="h6">Кастомизация учебника</Typography>
        </Box>
      </DialogTitle>

      <DialogContent dividers>
        <Alert severity="info" sx={{ mb: 3 }}>
          Вы создаете адаптированную копию учебника для своей школы.
          <br />
          После кастомизации вы сможете редактировать содержимое учебника.
        </Alert>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Исходный учебник:
          </Typography>
          <Typography variant="body1" fontWeight="medium">
            {textbook.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {textbook.subject} • {textbook.grade_level} класс • Версия {textbook.version}
          </Typography>
          {textbook.author && (
            <Typography variant="body2" color="text.secondary">
              Автор: {textbook.author}
            </Typography>
          )}
        </Box>

        <TextField
          label="Новое название учебника"
          fullWidth
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          disabled={loading}
          sx={{ mb: 2 }}
          helperText="Укажите название для адаптированной версии учебника"
          required
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={copyContent}
              onChange={(e) => setCopyContent(e.target.checked)}
              disabled={loading}
            />
          }
          label={
            <Box>
              <Typography variant="body2">
                Скопировать все главы и параграфы
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Если отключено, будет создан пустой учебник
              </Typography>
            </Box>
          }
        />

        {loading && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              mt: 3,
              p: 2,
              bgcolor: 'action.hover',
              borderRadius: 1,
            }}
          >
            <CircularProgress size={24} />
            <Typography variant="body2" color="text.secondary">
              {copyContent
                ? 'Копирование учебника с главами и параграфами...'
                : 'Создание учебника...'}
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Отмена
        </Button>
        <Button
          onClick={handleCustomize}
          variant="contained"
          disabled={loading || !newTitle.trim()}
          startIcon={loading ? <CircularProgress size={20} /> : <ContentCopyIcon />}
        >
          {loading ? 'Кастомизация...' : 'Кастомизировать'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
