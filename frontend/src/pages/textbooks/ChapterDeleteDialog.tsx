import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import { useNotify } from 'react-admin';
import type { Chapter } from '../../types';
import { getAuthToken } from '../../providers/authProvider';

const API_URL = 'http://localhost:8000/api/v1';

interface ChapterDeleteDialogProps {
  isSchoolTextbook?: boolean;
  open: boolean;
  chapter: Chapter;
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * Диалог подтверждения удаления главы
 *
 * Показывает предупреждение о том, что:
 * - Удаление главы приведет к каскадному удалению всех параграфов
 * - Это действие необратимо (soft delete в БД, но нельзя восстановить через UI)
 */
export const ChapterDeleteDialog = ({
  open,
  chapter,
  onClose,
  onSuccess,
  isSchoolTextbook = false,
}: ChapterDeleteDialogProps) => {
  const [submitting, setSubmitting] = useState(false);
  const notify = useNotify();

  const handleDelete = async () => {
    setSubmitting(true);

    try {
      const token = getAuthToken();
      const response = await fetch(isSchoolTextbook ? `${API_URL}/admin/school/chapters/${chapter.id}` : `${API_URL}/admin/global/chapters/${chapter.id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка удаления главы');
      }

      notify('Глава успешно удалена', { type: 'success' });
      onSuccess();
    } catch (error) {
      notify(
        error instanceof Error ? error.message : 'Ошибка удаления главы',
        { type: 'error' }
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="warning" />
        Подтверждение удаления
      </DialogTitle>

      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          Вы действительно хотите удалить главу <strong>{chapter.number}. {chapter.title}</strong>?
        </DialogContentText>

        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>Внимание!</strong> При удалении главы будут также удалены все параграфы,
          относящиеся к этой главе. Это действие нельзя отменить через интерфейс.
        </Alert>

        {chapter.description && (
          <DialogContentText variant="body2" color="text.secondary">
            Описание главы: {chapter.description}
          </DialogContentText>
        )}
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
