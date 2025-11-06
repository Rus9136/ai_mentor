import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  IconButton,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import { useNotify } from 'react-admin';
import type { Chapter, Paragraph } from '../../types';
import { getAuthToken } from '../../providers/authProvider';
import { ChapterCreateDialog } from './ChapterCreateDialog';
import { ChapterEditDialog } from './ChapterEditDialog';
import { ChapterDeleteDialog } from './ChapterDeleteDialog';
import { ParagraphCreateDialog } from './ParagraphCreateDialog';
import { ParagraphEditorDialog } from './ParagraphEditorDialog';

const API_URL = 'http://localhost:8000/api/v1';

interface TextbookStructureEditorProps {
  textbookId: number;
  isSchoolTextbook?: boolean;
}

/**
 * Компонент редактора структуры учебника
 *
 * Отображает дерево глав и параграфов с возможностью:
 * - Добавления новых глав
 * - Редактирования глав
 * - Удаления глав
 * - Просмотра параграфов (позже добавим CRUD для параграфов)
 */
export const TextbookStructureEditor = ({ textbookId, isSchoolTextbook = false }: TextbookStructureEditorProps) => {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [paragraphsMap, setParagraphsMap] = useState<Record<number, Paragraph[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Состояния для диалогов глав
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null);

  // Состояния для диалогов параграфов
  const [paragraphCreateDialogOpen, setParagraphCreateDialogOpen] = useState(false);
  const [paragraphEditDialogOpen, setParagraphEditDialogOpen] = useState(false);
  const [selectedParagraph, setSelectedParagraph] = useState<Paragraph | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);

  const notify = useNotify();

  // Загрузка глав
  const fetchChapters = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      const endpoint = isSchoolTextbook
        ? `${API_URL}/admin/school/textbooks/${textbookId}/chapters`
        : `${API_URL}/admin/global/textbooks/${textbookId}/chapters`;
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
      setChapters(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки глав');
      notify('Ошибка загрузки глав', { type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  // Загрузка параграфов для конкретной главы
  const fetchParagraphs = async (chapterId: number) => {
    try {
      const token = getAuthToken();
      const endpoint = isSchoolTextbook
        ? `${API_URL}/admin/school/chapters/${chapterId}/paragraphs`
        : `${API_URL}/admin/global/chapters/${chapterId}/paragraphs`;
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
      setParagraphsMap((prev) => ({ ...prev, [chapterId]: data }));
    } catch (err) {
      console.error(`Ошибка загрузки параграфов для главы ${chapterId}:`, err);
    }
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    fetchChapters();
  }, [textbookId]);

  // Обработчики диалогов
  const handleCreateChapter = () => {
    setCreateDialogOpen(true);
  };

  const handleEditChapter = (chapter: Chapter) => {
    setSelectedChapter(chapter);
    setEditDialogOpen(true);
  };

  const handleDeleteChapter = (chapter: Chapter) => {
    setSelectedChapter(chapter);
    setDeleteDialogOpen(true);
  };

  const handleDialogClose = () => {
    setCreateDialogOpen(false);
    setEditDialogOpen(false);
    setDeleteDialogOpen(false);
    setSelectedChapter(null);
  };

  const handleSuccess = () => {
    fetchChapters();
    handleDialogClose();
  };

  // Обработчики диалогов параграфов
  const handleAddParagraph = (chapterId: number) => {
    setSelectedChapterId(chapterId);
    setParagraphCreateDialogOpen(true);
  };

  const handleEditParagraph = (paragraph: Paragraph) => {
    setSelectedParagraph(paragraph);
    setParagraphEditDialogOpen(true);
  };

  const handleDeleteParagraph = async (paragraphId: number, chapterId: number) => {
    if (!confirm('Вы уверены, что хотите удалить этот параграф? Это действие нельзя отменить.')) {
      return;
    }

    try {
      const token = getAuthToken();
      const endpoint = isSchoolTextbook
        ? `${API_URL}/admin/school/paragraphs/${paragraphId}`
        : `${API_URL}/admin/global/paragraphs/${paragraphId}`;
      const response = await fetch(
        endpoint,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Ошибка удаления параграфа');
      }

      notify('Параграф успешно удален', { type: 'success' });
      // Перезагружаем параграфы для главы
      fetchParagraphs(chapterId);
    } catch (err) {
      notify(
        err instanceof Error ? err.message : 'Ошибка удаления параграфа',
        { type: 'error' }
      );
    }
  };

  const handleParagraphDialogClose = () => {
    setParagraphCreateDialogOpen(false);
    setParagraphEditDialogOpen(false);
    setSelectedParagraph(null);
    setSelectedChapterId(null);
  };

  const handleParagraphSuccess = () => {
    // Перезагружаем параграфы для текущей главы
    if (selectedChapterId) {
      fetchParagraphs(selectedChapterId);
    }
    if (selectedParagraph) {
      fetchParagraphs(selectedParagraph.chapter_id);
    }
    handleParagraphDialogClose();
  };

  // Обработчик раскрытия узла дерева (загрузка параграфов)
  const handleNodeToggle = (_event: React.SyntheticEvent | null, itemIds: string[]) => {
    itemIds.forEach((itemId) => {
      if (itemId.startsWith('chapter-')) {
        const chapterId = parseInt(itemId.replace('chapter-', ''));
        if (!paragraphsMap[chapterId]) {
          fetchParagraphs(chapterId);
        }
      }
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        Ошибка загрузки структуры: {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {/* Заголовок и кнопка добавления главы */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Структура учебника ({chapters.length} глав)
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleCreateChapter}
        >
          Добавить главу
        </Button>
      </Box>

      {/* Дерево глав и параграфов */}
      {chapters.length === 0 ? (
        <Alert severity="info">
          В учебнике пока нет глав. Нажмите "Добавить главу" для создания первой главы.
        </Alert>
      ) : (
        <SimpleTreeView
          slots={{
            collapseIcon: ExpandMoreIcon,
            expandIcon: ChevronRightIcon,
          }}
          onExpandedItemsChange={handleNodeToggle}
          sx={{ flexGrow: 1 }}
        >
          {chapters.map((chapter) => (
            <TreeItem
              key={`chapter-${chapter.id}`}
              itemId={`chapter-${chapter.id}`}
              label={
                <Card sx={{ my: 1 }}>
                  <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                          Глава {chapter.number}: {chapter.title}
                        </Typography>
                        {chapter.description && (
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                            {chapter.description}
                          </Typography>
                        )}
                        {chapter.learning_objective && (
                          <Chip
                            label={`Цель: ${chapter.learning_objective}`}
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <IconButton
                          size="small"
                          color="success"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAddParagraph(chapter.id);
                          }}
                          title="Добавить параграф"
                        >
                          <AddIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditChapter(chapter);
                          }}
                          title="Редактировать главу"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteChapter(chapter);
                          }}
                          title="Удалить главу"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              }
            >
              {/* Параграфы главы */}
              {paragraphsMap[chapter.id] ? (
                paragraphsMap[chapter.id].length > 0 ? (
                  paragraphsMap[chapter.id].map((paragraph) => (
                    <TreeItem
                      key={`paragraph-${paragraph.id}`}
                      itemId={`paragraph-${paragraph.id}`}
                      label={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1, px: 2 }}>
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body2">
                              §{paragraph.number}. {paragraph.title}
                            </Typography>
                            {paragraph.summary && (
                              <Typography variant="caption" color="text.secondary">
                                {paragraph.summary}
                              </Typography>
                            )}
                          </Box>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditParagraph(paragraph);
                              }}
                              title="Редактировать параграф"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              color="error"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteParagraph(paragraph.id, paragraph.chapter_id);
                              }}
                              title="Удалить параграф"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        </Box>
                      }
                    />
                  ))
                ) : (
                  <TreeItem
                    itemId={`no-paragraphs-${chapter.id}`}
                    label={
                      <Typography variant="body2" color="text.secondary" sx={{ py: 1, px: 2 }}>
                        Нет параграфов в главе
                      </Typography>
                    }
                  />
                )
              ) : (
                <TreeItem
                  itemId={`loading-${chapter.id}`}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1, px: 2 }}>
                      <CircularProgress size={16} />
                      <Typography variant="body2" color="text.secondary">
                        Загрузка параграфов...
                      </Typography>
                    </Box>
                  }
                />
              )}
            </TreeItem>
          ))}
        </SimpleTreeView>
      )}

      {/* Диалоги */}
      <ChapterCreateDialog
        open={createDialogOpen}
        textbookId={textbookId}
        onClose={handleDialogClose}
        onSuccess={handleSuccess}
        isSchoolTextbook={isSchoolTextbook}
      />

      {selectedChapter && (
        <>
          <ChapterEditDialog
            open={editDialogOpen}
            chapter={selectedChapter}
            onClose={handleDialogClose}
            onSuccess={handleSuccess}
            isSchoolTextbook={isSchoolTextbook}
          />

          <ChapterDeleteDialog
            open={deleteDialogOpen}
            chapter={selectedChapter}
            onClose={handleDialogClose}
            onSuccess={handleSuccess}
            isSchoolTextbook={isSchoolTextbook}
          />
        </>
      )}

      {/* Диалоги параграфов */}
      {selectedChapterId && (
        <ParagraphCreateDialog
          open={paragraphCreateDialogOpen}
          chapterId={selectedChapterId}
          onClose={handleParagraphDialogClose}
          onSuccess={handleParagraphSuccess}
          isSchoolTextbook={isSchoolTextbook}
        />
      )}

      {selectedParagraph && (
        <ParagraphEditorDialog
          open={paragraphEditDialogOpen}
          paragraphId={selectedParagraph.id}
          onClose={handleParagraphDialogClose}
          isSchoolTextbook={isSchoolTextbook}
          onSuccess={handleParagraphSuccess}
        />
      )}
    </Box>
  );
};
