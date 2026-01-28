'use client';

import * as React from 'react';
import { useState, useRef, useEffect, useCallback } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

import { cn } from '@/lib/utils';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

interface MathTextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  minHeight?: string;
}

const FORMULA_TEMPLATES = [
  { label: 'Дробь', template: '\\frac{a}{b}', preview: '\\frac{a}{b}' },
  { label: 'Степень', template: 'x^{n}', preview: 'x^{n}' },
  { label: 'Индекс', template: 'x_{i}', preview: 'x_{i}' },
  { label: 'Корень', template: '\\sqrt{x}', preview: '\\sqrt{x}' },
  { label: 'Корень n-й', template: '\\sqrt[n]{x}', preview: '\\sqrt[n]{x}' },
  { label: 'Логарифм', template: '\\log_{a}(x)', preview: '\\log_{a}(x)' },
  { label: 'Натур. лог', template: '\\ln(x)', preview: '\\ln(x)' },
  { label: 'Интеграл', template: '\\int_{a}^{b} f(x) \\, dx', preview: '\\int_{a}^{b}' },
  { label: 'Сумма', template: '\\sum_{i=1}^{n} x_i', preview: '\\sum_{i=1}^{n}' },
  { label: 'Предел', template: '\\lim_{x \\to \\infty}', preview: '\\lim_{x \\to \\infty}' },
  { label: 'Вектор', template: '\\vec{F}', preview: '\\vec{F}' },
  { label: 'Бесконечность', template: '\\infty', preview: '\\infty' },
  { label: 'Плюс-минус', template: '\\pm', preview: '\\pm' },
  { label: 'Умножение', template: '\\cdot', preview: '\\cdot' },
  { label: 'Не равно', template: '\\neq', preview: '\\neq' },
  { label: 'Меньше равно', template: '\\leq', preview: '\\leq' },
  { label: 'Больше равно', template: '\\geq', preview: '\\geq' },
  { label: 'Угол', template: '\\angle', preview: '\\angle' },
  { label: 'Градус', template: '^{\\circ}', preview: '90^{\\circ}' },
  { label: 'Пи', template: '\\pi', preview: '\\pi' },
];

// Chemistry templates
const CHEMISTRY_TEMPLATES = [
  { label: 'H₂O', template: 'H_2O', preview: 'H_2O' },
  { label: 'H₂SO₄', template: 'H_2SO_4', preview: 'H_2SO_4' },
  { label: 'CO₂', template: 'CO_2', preview: 'CO_2' },
  { label: 'Стрелка', template: '\\rightarrow', preview: '\\rightarrow' },
  { label: 'Равновесие', template: '\\rightleftharpoons', preview: '\\rightleftharpoons' },
];

function renderLatexPreview(text: string): string {
  if (!text) return '';

  // Replace display math $$...$$
  let result = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    try {
      return `<div class="my-2">${katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false })}</div>`;
    } catch {
      return `<span class="text-red-500">[Ошибка: ${tex}]</span>`;
    }
  });

  // Replace inline math $...$
  result = result.replace(/\$([^$\n]+?)\$/g, (_, tex) => {
    try {
      return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false });
    } catch {
      return `<span class="text-red-500">[Ошибка: ${tex}]</span>`;
    }
  });

  // Convert newlines to <br> for proper display
  result = result.replace(/\n/g, '<br>');

  return result;
}

function FormulaButton({
  template,
  preview,
  label,
  onClick
}: {
  template: string;
  preview: string;
  label: string;
  onClick: () => void;
}) {
  const [previewHtml, setPreviewHtml] = useState('');

  useEffect(() => {
    try {
      setPreviewHtml(katex.renderToString(preview, { displayMode: false, throwOnError: false }));
    } catch {
      setPreviewHtml(label);
    }
  }, [preview, label]);

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className="h-auto py-1.5 px-2 flex flex-col items-center gap-0.5 hover:bg-muted"
      onClick={onClick}
      title={label}
    >
      <span
        className="text-base"
        dangerouslySetInnerHTML={{ __html: previewHtml }}
      />
      <span className="text-[10px] text-muted-foreground">{label}</span>
    </Button>
  );
}

export function MathTextarea({
  value,
  onChange,
  placeholder = 'Введите текст...',
  className,
  minHeight = '100px',
}: MathTextareaProps) {
  const [preview, setPreview] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [cursorPosition, setCursorPosition] = useState(0);

  // Update preview when value changes
  useEffect(() => {
    setPreview(renderLatexPreview(value));
  }, [value]);

  const insertFormula = useCallback((template: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const formula = `$${template}$`;
    const newValue = value.slice(0, start) + formula + value.slice(end);

    onChange(newValue);

    // Set cursor position after the formula
    setTimeout(() => {
      textarea.focus();
      const newPosition = start + formula.length;
      textarea.setSelectionRange(newPosition, newPosition);
    }, 0);
  }, [value, onChange]);

  const insertBlockFormula = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const formula = '\n$$\n\n$$\n';
    const newValue = value.slice(0, start) + formula + value.slice(end);

    onChange(newValue);

    setTimeout(() => {
      textarea.focus();
      const newPosition = start + 4; // Position cursor inside $$
      textarea.setSelectionRange(newPosition, newPosition);
    }, 0);
  }, [value, onChange]);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    setCursorPosition(e.target.selectionStart);
  };

  // Check if value contains any LaTeX
  const hasLatex = value.includes('$');

  return (
    <div className="space-y-2">
      {/* Toolbar */}
      <div className="flex items-center gap-2 flex-wrap">
        <Popover>
          <PopoverTrigger asChild>
            <Button type="button" variant="outline" size="sm" className="h-8">
              <span className="mr-1">∑</span> Формула
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-2" align="start">
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground px-1">Математика</p>
              <div className="grid grid-cols-5 gap-1">
                {FORMULA_TEMPLATES.map((t) => (
                  <FormulaButton
                    key={t.label}
                    template={t.template}
                    preview={t.preview}
                    label={t.label}
                    onClick={() => insertFormula(t.template)}
                  />
                ))}
              </div>
              <p className="text-xs font-medium text-muted-foreground px-1 pt-2">Химия</p>
              <div className="grid grid-cols-5 gap-1">
                {CHEMISTRY_TEMPLATES.map((t) => (
                  <FormulaButton
                    key={t.label}
                    template={t.template}
                    preview={t.preview}
                    label={t.label}
                    onClick={() => insertFormula(t.template)}
                  />
                ))}
              </div>
            </div>
          </PopoverContent>
        </Popover>

        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-8"
          onClick={insertBlockFormula}
        >
          Блок формулы
        </Button>

        <div className="flex-1" />

        {hasLatex && (
          <Button
            type="button"
            variant={showPreview ? 'default' : 'ghost'}
            size="sm"
            className="h-8"
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? 'Скрыть' : 'Превью'}
          </Button>
        )}
      </div>

      {/* Help text */}
      <p className="text-xs text-muted-foreground">
        Для формул: <code className="bg-muted px-1 rounded">$x^2$</code> — inline,{' '}
        <code className="bg-muted px-1 rounded">$$x^2$$</code> — блок
      </p>

      {/* Textarea */}
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={handleTextareaChange}
        placeholder={placeholder}
        className={cn('font-mono', className)}
        style={{ minHeight }}
      />

      {/* Preview */}
      {showPreview && hasLatex && (
        <div className="rounded-md border bg-muted/30 p-4">
          <p className="text-xs font-medium text-muted-foreground mb-2">Превью:</p>
          <div
            className="prose prose-sm max-w-none dark:prose-invert"
            dangerouslySetInnerHTML={{ __html: preview }}
          />
        </div>
      )}
    </div>
  );
}

// Also export a simple inline component for displaying math in other places
export function MathInline({ children }: { children: string }) {
  const [html, setHtml] = useState('');

  useEffect(() => {
    setHtml(renderLatexPreview(children));
  }, [children]);

  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}
