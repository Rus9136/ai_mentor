/**
 * TinyMCE Math Plugin
 * Добавляет кнопку для вставки LaTeX формул в TinyMCE редактор
 */

import type { Editor } from 'tinymce';

export interface MathPluginCallbacks {
  onOpenDialog: () => void;
}

/**
 * Настройка math plugin для TinyMCE editor
 * Регистрирует кнопку "Σ" (формула) в toolbar
 *
 * @param editor - TinyMCE editor instance
 * @param callbacks - Callback функции
 */
export const setupMathPlugin = (editor: Editor, callbacks: MathPluginCallbacks) => {
  // Регистрация кнопки "Вставить формулу"
  editor.ui.registry.addButton('math', {
    text: 'Σ',
    tooltip: 'Вставить формулу (LaTeX)',
    onAction: () => {
      // Открыть MathFormulaDialog через callback
      callbacks.onOpenDialog();
    },
  });

  // Регистрация menu item (опционально, для context menu)
  editor.ui.registry.addMenuItem('math', {
    text: 'Математическая формула',
    icon: 'math',
    onAction: () => {
      callbacks.onOpenDialog();
    },
  });
};

/**
 * Вспомогательная функция для вставки LaTeX формулы в editor
 *
 * @param editor - TinyMCE editor instance
 * @param latex - LaTeX код формулы
 * @param displayMode - Режим отображения (true = display, false = inline)
 */
export const insertMathFormula = (editor: Editor, latex: string, displayMode: boolean) => {
  // Определяем class и delimiters
  const className = displayMode ? 'math-tex display-mode' : 'math-tex';
  const delimiter = displayMode ? '$$' : '$';

  // Формируем HTML
  // Сохраняем LaTeX в data-атрибуте для последующего редактирования (опционально)
  const html = `<span class="${className}" data-latex="${escapeHtml(
    latex
  )}">${delimiter}${escapeHtml(latex)}${delimiter}</span>`;

  // Вставляем в редактор
  editor.insertContent(html);

  // Добавляем пробел после формулы (для удобства)
  if (!displayMode) {
    editor.insertContent('&nbsp;');
  }
};

/**
 * Экранирование HTML для безопасной вставки
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Извлечение LaTeX из span элемента (для редактирования существующих формул)
 * Опциональная функция для будущего расширения
 */
export const extractLatexFromElement = (element: HTMLElement): string | null => {
  if (element.classList.contains('math-tex')) {
    // Сначала пробуем data-атрибут
    const dataLatex = element.getAttribute('data-latex');
    if (dataLatex) {
      return dataLatex;
    }

    // Fallback: извлекаем текст и убираем delimiters
    const text = element.textContent || '';
    return text.replace(/^\$\$?/, '').replace(/\$\$?$/, '');
  }
  return null;
};

/**
 * Проверка, является ли элемент math формулой
 */
export const isMathElement = (element: HTMLElement | null): boolean => {
  return element !== null && element.classList.contains('math-tex');
};
