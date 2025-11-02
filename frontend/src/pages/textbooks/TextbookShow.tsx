import { useState, useEffect } from 'react';
import {
  Show,
  TextField,
  NumberField,
  DateField,
  TabbedShowLayout,
  Tab,
  useRecordContext,
  FunctionField,
} from 'react-admin';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Chip,
  Box,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import type { Textbook, Chapter, Paragraph } from '../../types';
import { getAuthToken } from '../../providers/authProvider';
import { TextbookStructureEditor } from './TextbookStructureEditor';

const API_URL = 'http://localhost:8000/api/v1';

// Компонент для отображения параграфов главы
const ParagraphsList = ({ chapterId }: { chapterId: number }) => {
  const [paragraphs, setParagraphs] = useState<Paragraph[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchParagraphs = async () => {
      try {
        const token = getAuthToken();
        const response = await fetch(
          `${API_URL}/admin/global/chapters/${chapterId}/paragraphs`,
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
        setParagraphs(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Ошибка загрузки параграфов');
      } finally {
        setLoading(false);
      }
    };

    fetchParagraphs();
  }, [chapterId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Ошибка: {error}</Alert>;
  }

  if (paragraphs.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
        Нет параграфов в главе
      </Typography>
    );
  }

  return (
    <List dense>
      {paragraphs.map((para) => (
        <ListItem key={para.id}>
          <ListItemText
            primary={
              <Typography variant="body2">
                §{para.number}. {para.title}
              </Typography>
            }
            secondary={para.summary || 'Нет описания'}
          />
        </ListItem>
      ))}
    </List>
  );
};

// Компонент для отображения одной главы с Accordion
const ChapterAccordion = ({ chapter }: { chapter: Chapter }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      sx={{ mb: 1 }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="subtitle1">
            Глава {chapter.number}: {chapter.title}
          </Typography>
          {chapter.description && (
            <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
              {chapter.description}
            </Typography>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        {expanded && <ParagraphsList chapterId={chapter.id} />}
      </AccordionDetails>
    </Accordion>
  );
};

// Компонент для вкладки "Редактор структуры"
const EditorTab = () => {
  const record = useRecordContext<Textbook>();

  if (!record?.id) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        Загрузка учебника...
      </Alert>
    );
  }

  return <TextbookStructureEditor textbookId={record.id} />;
};

// Компонент для вкладки "Структура" со списком глав
const ChaptersTab = () => {
  const record = useRecordContext<Textbook>();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (record?.id) {
      const fetchChapters = async () => {
        try {
          const token = getAuthToken();
          const response = await fetch(
            `${API_URL}/admin/global/textbooks/${record.id}/chapters`,
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
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Ошибка загрузки глав');
        } finally {
          setLoading(false);
        }
      };

      fetchChapters();
    }
  }, [record?.id]);

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
        Ошибка загрузки глав: {error}
      </Alert>
    );
  }

  if (chapters.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        В учебнике нет глав
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Структура учебника ({chapters.length} глав)
      </Typography>
      {chapters.map((chapter) => (
        <ChapterAccordion key={chapter.id} chapter={chapter} />
      ))}
    </Box>
  );
};

// Основной компонент TextbookShow
export const TextbookShow = () => (
  <Show title="Просмотр учебника">
    <TabbedShowLayout>
      {/* Вкладка 1: Информация об учебнике */}
      <Tab label="Информация">
        <TextField source="id" label="ID" />
        <TextField source="title" label="Название" />
        <TextField source="subject" label="Предмет" />
        <NumberField source="grade_level" label="Класс" />
        <TextField source="author" label="Автор" emptyText="Не указан" />
        <TextField source="publisher" label="Издательство" emptyText="Не указано" />
        <NumberField source="year" label="Год издания" emptyText="-" />
        <TextField source="isbn" label="ISBN" emptyText="-" />
        <TextField source="description" label="Описание" emptyText="Нет описания" />
        <NumberField source="version" label="Версия" />
        <FunctionField
          label="Статус"
          render={(record: Textbook) => (
            <Chip
              label={record.is_active ? 'Активен' : 'Неактивен'}
              color={record.is_active ? 'success' : 'default'}
              size="small"
            />
          )}
        />
        <DateField
          source="created_at"
          label="Дата создания"
          showTime
          locales="ru-RU"
        />
        <DateField
          source="updated_at"
          label="Обновлено"
          showTime
          locales="ru-RU"
        />
      </Tab>

      {/* Вкладка 2: Структура учебника (главы + параграфы) read-only */}
      <Tab label="Просмотр структуры" path="chapters">
        <ChaptersTab />
      </Tab>

      {/* Вкладка 3: Редактор структуры (CRUD для глав и параграфов) */}
      <Tab label="Редактор структуры" path="editor">
        <EditorTab />
      </Tab>
    </TabbedShowLayout>
  </Show>
);
