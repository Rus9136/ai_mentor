import React, { useState, useEffect, useRef } from 'react';
import {
  Dialog,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Button,
  TextField,
  RadioGroup,
  FormControlLabel,
  Radio,
  Box,
  Paper,
  Chip,
  Alert,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface MathFormulaDialogProps {
  open: boolean;
  onClose: () => void;
  onInsert: (latex: string, displayMode: boolean) => void;
}

// Примеры формул для помощи пользователю
const FORMULA_EXAMPLES = [
  { label: 'Квадратное уравнение', latex: 'x^2 + 2x + 1 = 0' },
  { label: 'Дробь', latex: '\\frac{a}{b}' },
  { label: 'Корень', latex: '\\sqrt{x^2 + y^2}' },
  { label: 'Интеграл', latex: '\\int_0^\\infty f(x)dx' },
  { label: 'Сумма', latex: '\\sum_{i=1}^{n} x_i' },
  { label: 'Предел', latex: '\\lim_{x \\to \\infty} f(x)' },
  { label: 'Матрица', latex: '\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}' },
  { label: 'Система', latex: '\\begin{cases} x + y = 1 \\\\ x - y = 0 \\end{cases}' },
];

export const MathFormulaDialog: React.FC<MathFormulaDialogProps> = ({
  open,
  onClose,
  onInsert,
}) => {
  const [latex, setLatex] = useState('');
  const [displayMode, setDisplayMode] = useState(false);
  const [renderError, setRenderError] = useState<string | null>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  // Live preview с KaTeX
  useEffect(() => {
    if (!previewRef.current || !latex.trim()) {
      setRenderError(null);
      return;
    }

    try {
      katex.render(latex, previewRef.current, {
        throwOnError: true,
        displayMode: displayMode,
        strict: false,
      });
      setRenderError(null);
    } catch (error) {
      if (error instanceof Error) {
        setRenderError(error.message);
      }
    }
  }, [latex, displayMode]);

  const handleInsert = () => {
    if (!latex.trim()) {
      return;
    }
    onInsert(latex, displayMode);
    handleClose();
  };

  const handleClose = () => {
    setLatex('');
    setDisplayMode(false);
    setRenderError(null);
    onClose();
  };

  const handleExampleClick = (exampleLatex: string) => {
    setLatex(exampleLatex);
  };

  return (
    <Dialog fullScreen open={open} onClose={handleClose}>
      <AppBar sx={{ position: 'relative' }}>
        <Toolbar>
          <IconButton edge="start" color="inherit" onClick={handleClose} aria-label="close">
            <CloseIcon />
          </IconButton>
          <Typography sx={{ ml: 2, flex: 1 }} variant="h6" component="div">
            Вставить математическую формулу
          </Typography>
          <Button
            autoFocus
            color="inherit"
            onClick={handleInsert}
            disabled={!latex.trim() || renderError !== null}
          >
            Вставить
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 3, maxWidth: '900px', mx: 'auto', width: '100%' }}>
        {/* Режим формулы */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Режим отображения:
          </Typography>
          <RadioGroup
            row
            value={displayMode ? 'display' : 'inline'}
            onChange={(e) => setDisplayMode(e.target.value === 'display')}
          >
            <FormControlLabel
              value="inline"
              control={<Radio />}
              label="Inline (в строке текста)"
            />
            <FormControlLabel
              value="display"
              control={<Radio />}
              label="Display (отдельная строка, центрировано)"
            />
          </RadioGroup>
        </Paper>

        {/* Ввод LaTeX */}
        <TextField
          fullWidth
          multiline
          rows={4}
          label="LaTeX код формулы"
          placeholder="Например: x^2 + y^2 = z^2"
          value={latex}
          onChange={(e) => setLatex(e.target.value)}
          helperText="Введите формулу в формате LaTeX"
          sx={{ mb: 3 }}
        />

        {/* Preview */}
        <Paper sx={{ p: 3, mb: 3, minHeight: '100px', backgroundColor: '#f5f5f5' }}>
          <Typography variant="subtitle2" gutterBottom>
            Предпросмотр:
          </Typography>
          {renderError ? (
            <Alert severity="error" sx={{ mt: 1 }}>
              Ошибка: {renderError}
            </Alert>
          ) : latex.trim() ? (
            <Box
              ref={previewRef}
              sx={{
                mt: 2,
                fontSize: '1.2rem',
                textAlign: displayMode ? 'center' : 'left',
              }}
            />
          ) : (
            <Typography color="text.secondary" sx={{ mt: 2, fontStyle: 'italic' }}>
              Введите формулу для предпросмотра
            </Typography>
          )}
        </Paper>

        {/* Примеры формул */}
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Примеры формул (нажмите для вставки):
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
            {FORMULA_EXAMPLES.map((example) => (
              <Chip
                key={example.label}
                label={example.label}
                onClick={() => handleExampleClick(example.latex)}
                variant="outlined"
                clickable
              />
            ))}
          </Box>
        </Box>

        {/* Подсказки */}
        <Paper sx={{ p: 2, mt: 3, backgroundColor: '#e3f2fd' }}>
          <Typography variant="subtitle2" gutterBottom>
            Полезные команды LaTeX:
          </Typography>
          <Typography variant="body2" component="div">
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              <li>
                <code>^</code> - степень: <code>x^2</code>
              </li>
              <li>
                <code>_</code> - индекс: <code>x_i</code>
              </li>
              <li>
                <code>\frac{'{'}{'{'}...{'}'}{'{'}{'{'}...{'}'}</code> - дробь
              </li>
              <li>
                <code>\sqrt{'{'}{'{'}...{'}'}</code> - корень
              </li>
              <li>
                <code>\int</code>, <code>\sum</code>, <code>\prod</code> - интеграл, сумма,
                произведение
              </li>
              <li>
                <code>\alpha</code>, <code>\beta</code>, <code>\gamma</code> - греческие буквы
              </li>
              <li>
                <code>{'{'} ... {'}'}</code> - группировка
              </li>
            </ul>
          </Typography>
        </Paper>
      </Box>
    </Dialog>
  );
};
