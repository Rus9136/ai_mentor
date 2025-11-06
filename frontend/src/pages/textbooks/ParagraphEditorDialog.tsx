import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  CircularProgress,
  Alert,
  Typography,
  Paper,
  IconButton,
  Chip,
  AppBar,
  Toolbar,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SaveIcon from '@mui/icons-material/Save';
import PreviewIcon from '@mui/icons-material/Preview';
import EditIcon from '@mui/icons-material/Edit';
import { useNotify } from 'react-admin';
import { Editor } from '@tinymce/tinymce-react';
import type { Editor as TinyMCEEditor } from 'tinymce';
import { useDebounce } from 'use-debounce';
import katex from 'katex';
import 'katex/dist/katex.min.css';
import '../../styles/katex-custom.css';
// Import TinyMCE
import 'tinymce/tinymce';
// Import TinyMCE themes and plugins
import 'tinymce/themes/silver';
import 'tinymce/icons/default';
import 'tinymce/models/dom';
import 'tinymce/plugins/advlist';
import 'tinymce/plugins/autolink';
import 'tinymce/plugins/lists';
import 'tinymce/plugins/link';
import 'tinymce/plugins/image';
import 'tinymce/plugins/charmap';
import 'tinymce/plugins/preview';
import 'tinymce/plugins/anchor';
import 'tinymce/plugins/searchreplace';
import 'tinymce/plugins/visualblocks';
import 'tinymce/plugins/code';
import 'tinymce/plugins/fullscreen';
import 'tinymce/plugins/insertdatetime';
import 'tinymce/plugins/media';
import 'tinymce/plugins/table';
import 'tinymce/plugins/help';
import 'tinymce/plugins/wordcount';

import { getAuthToken } from '../../providers/authProvider';
import type { Paragraph } from '../../types';
import { MathFormulaDialog } from '../../components/MathFormulaDialog';
import { setupMathPlugin, insertMathFormula } from '../../utils/tinymce-math-plugin';

// API URLs из environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = `${API_BASE_URL}/api/v1`;

interface ParagraphEditorDialogProps {
  isSchoolTextbook?: boolean;
  open: boolean;
  paragraphId: number;
  onClose: () => void;
  onSuccess: () => void;
}

interface ParagraphMetadata {
  title: string;
  number: number;
  order: number;
  summary: string;
  learning_objective: string;
  lesson_objective: string;
}

/**
 * Fullscreen диалог редактирования параграфа с Rich Text Editor
 *
 * Функциональность:
 * - TinyMCE Rich Text Editor для content
 * - Auto-save content каждые 30 секунд
 * - Manual save для metadata
 * - Preview режим
 * - Status indicator (Сохранение.../Сохранено)
 */
export const ParagraphEditorDialog = ({
  open,
  paragraphId,
  onClose,
  onSuccess,
  isSchoolTextbook = false,
}: ParagraphEditorDialogProps) => {
  // State для данных параграфа
  const [paragraph, setParagraph] = useState<Paragraph | null>(null);
  const [content, setContent] = useState<string>('');
  const [metadata, setMetadata] = useState<ParagraphMetadata>({
    title: '',
    number: 1,
    order: 1,
    summary: '',
    learning_objective: '',
    lesson_objective: '',
  });

  // State для UI
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metadataChanged, setMetadataChanged] = useState(false);
  const [mathDialogOpen, setMathDialogOpen] = useState(false);

  // Refs
  const editorRef = useRef<TinyMCEEditor | null>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  // Debounced content для auto-save
  const [debouncedContent] = useDebounce(content, 30000); // 30 секунд

  const notify = useNotify();

  // Загрузка параграфа
  const fetchParagraph = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = getAuthToken();
      const response = await fetch(
        isSchoolTextbook ? `${API_URL}/admin/school/paragraphs/${paragraphId}` : `${API_URL}/admin/global/paragraphs/${paragraphId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: Paragraph = await response.json();
      setParagraph(data);
      setContent(data.content);
      setMetadata({
        title: data.title,
        number: data.number,
        order: data.order,
        summary: data.summary || '',
        learning_objective: data.learning_objective || '',
        lesson_objective: data.lesson_objective || '',
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка загрузки параграфа';
      setError(message);
      notify(message, { type: 'error' });
    } finally {
      setLoading(false);
    }
  }, [paragraphId, notify]);

  // Загрузка при открытии диалога
  useEffect(() => {
    if (open && paragraphId) {
      fetchParagraph();
    }
  }, [open, paragraphId, fetchParagraph]);

  // Auto-save content при изменении debouncedContent
  useEffect(() => {
    const autoSaveContent = async () => {
      // Не сохраняем если:
      // - Параграф еще не загружен
      // - Content не изменился с момента загрузки
      // - Уже идет процесс сохранения
      if (!paragraph || content === paragraph.content || saving) {
        return;
      }

      setSaving(true);

      try {
        const token = getAuthToken();
        const response = await fetch(
          isSchoolTextbook ? `${API_URL}/admin/school/paragraphs/${paragraphId}` : `${API_URL}/admin/global/paragraphs/${paragraphId}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ content }),
          }
        );

        if (!response.ok) {
          throw new Error('Ошибка автосохранения');
        }

        setLastSaved(new Date());
        // Обновляем paragraph чтобы content считался сохраненным
        setParagraph((prev) => (prev ? { ...prev, content } : null));
      } catch (err) {
        console.error('Auto-save error:', err);
        // Показываем уведомление пользователю об ошибке автосохранения
        notify('Ошибка автосохранения. Нажмите "Сохранить" вручную.', {
          type: 'warning',
          autoHideDuration: 10000, // 10 секунд
        });
      } finally {
        setSaving(false);
      }
    };

    if (debouncedContent && paragraph) {
      autoSaveContent();
    }
  }, [debouncedContent, paragraphId, paragraph, content, saving]);

  // Manual save для metadata и content
  const handleManualSave = async () => {
    if (!paragraph) return;

    setSaving(true);

    try {
      const token = getAuthToken();
      const payload = {
        title: metadata.title.trim(),
        number: metadata.number,
        order: metadata.order,
        summary: metadata.summary.trim() || undefined,
        learning_objective: metadata.learning_objective.trim() || undefined,
        lesson_objective: metadata.lesson_objective.trim() || undefined,
        content: content,
      };

      const response = await fetch(
        isSchoolTextbook ? `${API_URL}/admin/school/paragraphs/${paragraphId}` : `${API_URL}/admin/global/paragraphs/${paragraphId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка сохранения');
      }

      const updatedParagraph: Paragraph = await response.json();
      setParagraph(updatedParagraph);
      setLastSaved(new Date());
      setMetadataChanged(false);
      notify('Параграф успешно сохранен', { type: 'success' });
      onSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ошибка сохранения параграфа';
      notify(message, { type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  // Обработчик изменения content в TinyMCE
  const handleEditorChange = (newContent: string) => {
    setContent(newContent);
  };

  // Обработчик изменения metadata
  const handleMetadataChange = (field: keyof ParagraphMetadata, value: string | number) => {
    setMetadata((prev) => ({ ...prev, [field]: value }));
    setMetadataChanged(true);
  };

  // KaTeX rendering в preview режиме
  useEffect(() => {
    if (previewMode && previewRef.current) {
      // Рендерим все math формулы через KaTeX
      const mathElements = previewRef.current.querySelectorAll('.math-tex');
      mathElements.forEach((element) => {
        const latexCode = element.textContent?.replace(/^\$\$?/, '').replace(/\$\$?$/, '') || '';
        const displayMode = element.classList.contains('display-mode');

        try {
          katex.render(latexCode, element as HTMLElement, {
            throwOnError: false,
            displayMode: displayMode,
            strict: false,
          });
        } catch (error) {
          console.error('KaTeX render error:', error);
          // Оставляем LaTeX код как есть при ошибке
        }
      });
    }
  }, [previewMode, content]);

  // Toggle preview режима
  const handleTogglePreview = () => {
    setPreviewMode((prev) => !prev);
  };

  // Обработчики для MathFormulaDialog
  const handleOpenMathDialog = () => {
    setMathDialogOpen(true);
  };

  const handleCloseMathDialog = () => {
    setMathDialogOpen(false);
  };

  const handleInsertFormula = (latex: string, displayMode: boolean) => {
    if (editorRef.current) {
      insertMathFormula(editorRef.current, latex, displayMode);
    }
  };

  // Закрытие диалога
  const handleClose = () => {
    // Проверка несохраненных изменений в metadata
    if (metadataChanged) {
      const confirmClose = window.confirm(
        'Есть несохраненные изменения в метаданных. Вы уверены, что хотите закрыть?'
      );
      if (!confirmClose) {
        return; // Пользователь отменил закрытие
      }
    }

    setPreviewMode(false);
    setMetadataChanged(false);
    setMathDialogOpen(false);
    onClose();
  };

  // Render loading state
  if (loading) {
    return (
      <Dialog open={open} fullScreen>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100vh',
          }}
        >
          <CircularProgress size={60} />
        </Box>
      </Dialog>
    );
  }

  // Render error state
  if (error || !paragraph) {
    return (
      <Dialog open={open} fullScreen>
        <AppBar sx={{ position: 'relative' }}>
          <Toolbar>
            <Typography variant="h6" sx={{ flex: 1 }}>
              Ошибка
            </Typography>
            <IconButton edge="end" color="inherit" onClick={handleClose}>
              <CloseIcon />
            </IconButton>
          </Toolbar>
        </AppBar>
        <DialogContent>
          <Alert severity="error" sx={{ mt: 2 }}>
            {error || 'Параграф не найден'}
          </Alert>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} fullScreen>
      {/* AppBar с заголовком и кнопками */}
      <AppBar sx={{ position: 'relative' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flex: 1 }}>
            Редактирование: §{paragraph.number}. {paragraph.title}
          </Typography>

          {/* Status indicator */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mr: 2 }}>
            {saving && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} color="inherit" />
                <Typography variant="body2">Сохранение...</Typography>
              </Box>
            )}
            {!saving && lastSaved && (
              <Typography variant="body2">
                Сохранено {lastSaved.toLocaleTimeString('ru-RU')}
              </Typography>
            )}
            {metadataChanged && (
              <Chip
                label="Есть несохраненные изменения"
                size="small"
                color="warning"
                variant="outlined"
              />
            )}
          </Box>

          {/* Action buttons */}
          <Button
            color="inherit"
            startIcon={previewMode ? <EditIcon /> : <PreviewIcon />}
            onClick={handleTogglePreview}
            sx={{ mr: 1 }}
          >
            {previewMode ? 'Редактировать' : 'Превью'}
          </Button>
          <Button
            color="inherit"
            startIcon={<SaveIcon />}
            onClick={handleManualSave}
            disabled={saving}
            sx={{ mr: 1 }}
          >
            Сохранить
          </Button>
          <IconButton edge="end" color="inherit" onClick={handleClose}>
            <CloseIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <DialogContent sx={{ p: 3 }}>
        {/* Metadata form */}
        <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Метаданные параграфа
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Название параграфа"
              value={metadata.title}
              onChange={(e) => handleMetadataChange('title', e.target.value)}
              fullWidth
              required
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Номер параграфа"
                type="number"
                value={metadata.number}
                onChange={(e) =>
                  handleMetadataChange('number', parseInt(e.target.value) || 1)
                }
                required
                inputProps={{ min: 1 }}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Порядок отображения"
                type="number"
                value={metadata.order}
                onChange={(e) =>
                  handleMetadataChange('order', parseInt(e.target.value) || 1)
                }
                required
                inputProps={{ min: 1 }}
                sx={{ flex: 1 }}
              />
            </Box>

            <TextField
              label="Краткое описание"
              value={metadata.summary}
              onChange={(e) => handleMetadataChange('summary', e.target.value)}
              multiline
              rows={2}
              fullWidth
            />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label="Цель обучения"
                value={metadata.learning_objective}
                onChange={(e) =>
                  handleMetadataChange('learning_objective', e.target.value)
                }
                multiline
                rows={2}
                fullWidth
              />
              <TextField
                label="Цель урока"
                value={metadata.lesson_objective}
                onChange={(e) =>
                  handleMetadataChange('lesson_objective', e.target.value)
                }
                multiline
                rows={2}
                fullWidth
              />
            </Box>
          </Box>
        </Paper>

        {/* Content editor or preview */}
        <Paper elevation={2} sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Содержание параграфа
          </Typography>

          {previewMode ? (
            // Preview mode
            <Box
              ref={previewRef}
              sx={{
                border: '1px solid #ddd',
                borderRadius: 1,
                p: 3,
                minHeight: 500,
                backgroundColor: '#fff',
              }}
              dangerouslySetInnerHTML={{ __html: content }}
            />
          ) : (
            // Editor mode
            <Editor
              apiKey="no-api-key"
              value={content}
              onInit={(_evt, editor) => {
                editorRef.current = editor;
              }}
              init={{
                skin_url: '/tinymce/skins/ui/oxide',
                content_css: '/tinymce/skins/content/default/content.min.css',
                height: 500,
                menubar: false,
                plugins: [
                  'advlist',
                  'autolink',
                  'lists',
                  'link',
                  'image',
                  'charmap',
                  'preview',
                  'anchor',
                  'searchreplace',
                  'visualblocks',
                  'code',
                  'fullscreen',
                  'insertdatetime',
                  'media',
                  'table',
                  'help',
                  'wordcount',
                ],
                toolbar:
                  'undo redo | blocks | bold italic underline strikethrough | ' +
                  'alignleft aligncenter alignright alignjustify | ' +
                  'bullist numlist outdent indent | ' +
                  'link image table | math | ' +
                  'forecolor backcolor | ' +
                  'removeformat | code preview | help',
                content_style:
                  'body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; }',
                branding: false,
                setup: (editor: TinyMCEEditor) => {
                  // Регистрация math plugin
                  setupMathPlugin(editor, {
                    onOpenDialog: handleOpenMathDialog,
                  });
                },
                // Image upload handler
                images_upload_handler: async (blobInfo, _progress) => {
                  try {
                    const formData = new FormData();
                    formData.append('file', blobInfo.blob(), blobInfo.filename());

                    const token = getAuthToken();
                    const response = await fetch(`${API_URL}/upload/image`, {
                      method: 'POST',
                      headers: {
                        Authorization: `Bearer ${token}`,
                      },
                      body: formData,
                    });

                    if (!response.ok) {
                      const errorData = await response.json();
                      throw new Error(errorData.detail || 'Ошибка загрузки изображения');
                    }

                    const data = await response.json();
                    // Возвращаем full URL для изображения
                    return `${API_BASE_URL}${data.url}`;
                  } catch (error) {
                    const message = error instanceof Error ? error.message : 'Ошибка загрузки';
                    notify(message, { type: 'error' });
                    throw error;
                  }
                },
                // Автоматическая загрузка изображений
                automatic_uploads: true,
                // Типы файлов для file picker
                file_picker_types: 'image',
              }}
              onEditorChange={handleEditorChange}
            />
          )}
        </Paper>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
          Auto-save: каждые 30 секунд после изменения content
        </Typography>
        <Button onClick={handleClose} disabled={saving}>
          Закрыть
        </Button>
      </DialogActions>

      {/* Math Formula Dialog */}
      <MathFormulaDialog
        open={mathDialogOpen}
        onClose={handleCloseMathDialog}
        onInsert={handleInsertFormula}
      />
    </Dialog>
  );
};
