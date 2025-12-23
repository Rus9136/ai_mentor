'use client';

import { useEditor, EditorContent, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Underline } from '@tiptap/extension-underline';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import { Highlight } from '@tiptap/extension-highlight';
import { TextAlign } from '@tiptap/extension-text-align';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';
import { useCallback, useEffect } from 'react';
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Table as TableIcon,
  TableCellsMerge,
  Trash2,
  Plus,
  Minus,
  Palette,
  Highlighter,
  Undo,
  Redo,
  Pilcrow,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from './dropdown-menu';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './popover';

interface RichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

// Text colors palette
const TEXT_COLORS = [
  { name: 'По умолчанию', color: null },
  { name: 'Чёрный', color: '#000000' },
  { name: 'Серый', color: '#6b7280' },
  { name: 'Красный', color: '#dc2626' },
  { name: 'Оранжевый', color: '#ea580c' },
  { name: 'Жёлтый', color: '#ca8a04' },
  { name: 'Зелёный', color: '#16a34a' },
  { name: 'Синий', color: '#2563eb' },
  { name: 'Фиолетовый', color: '#9333ea' },
  { name: 'Розовый', color: '#db2777' },
];

// Highlight colors palette
const HIGHLIGHT_COLORS = [
  { name: 'Без выделения', color: null },
  { name: 'Жёлтый', color: '#fef08a' },
  { name: 'Зелёный', color: '#bbf7d0' },
  { name: 'Голубой', color: '#bae6fd' },
  { name: 'Розовый', color: '#fbcfe8' },
  { name: 'Оранжевый', color: '#fed7aa' },
  { name: 'Фиолетовый', color: '#e9d5ff' },
];

// Toolbar button component
function ToolbarButton({
  onClick,
  isActive = false,
  disabled = false,
  children,
  title,
}: {
  onClick: () => void;
  isActive?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  title?: string;
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={cn(
        'h-8 w-8 p-0',
        isActive && 'bg-accent text-accent-foreground'
      )}
    >
      {children}
    </Button>
  );
}

// Toolbar separator
function ToolbarSeparator() {
  return <div className="mx-1 h-6 w-px bg-border" />;
}

// Main toolbar component
function Toolbar({ editor }: { editor: Editor | null }) {
  if (!editor) return null;

  const addTable = useCallback(() => {
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
  }, [editor]);

  return (
    <div className="flex flex-wrap items-center gap-0.5 border-b bg-muted/30 p-1">
      {/* Undo/Redo */}
      <ToolbarButton
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        title="Отменить"
      >
        <Undo className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        title="Повторить"
      >
        <Redo className="h-4 w-4" />
      </ToolbarButton>

      <ToolbarSeparator />

      {/* Text formatting */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBold().run()}
        isActive={editor.isActive('bold')}
        title="Жирный"
      >
        <Bold className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleItalic().run()}
        isActive={editor.isActive('italic')}
        title="Курсив"
      >
        <Italic className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        isActive={editor.isActive('underline')}
        title="Подчёркнутый"
      >
        <UnderlineIcon className="h-4 w-4" />
      </ToolbarButton>

      <ToolbarSeparator />

      {/* Headings */}
      <ToolbarButton
        onClick={() => editor.chain().focus().setParagraph().run()}
        isActive={editor.isActive('paragraph')}
        title="Параграф"
      >
        <Pilcrow className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        isActive={editor.isActive('heading', { level: 1 })}
        title="Заголовок 1"
      >
        <Heading1 className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        isActive={editor.isActive('heading', { level: 2 })}
        title="Заголовок 2"
      >
        <Heading2 className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        isActive={editor.isActive('heading', { level: 3 })}
        title="Заголовок 3"
      >
        <Heading3 className="h-4 w-4" />
      </ToolbarButton>

      <ToolbarSeparator />

      {/* Lists */}
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        isActive={editor.isActive('bulletList')}
        title="Маркированный список"
      >
        <List className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        isActive={editor.isActive('orderedList')}
        title="Нумерованный список"
      >
        <ListOrdered className="h-4 w-4" />
      </ToolbarButton>

      <ToolbarSeparator />

      {/* Text alignment */}
      <ToolbarButton
        onClick={() => editor.chain().focus().setTextAlign('left').run()}
        isActive={editor.isActive({ textAlign: 'left' })}
        title="По левому краю"
      >
        <AlignLeft className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().setTextAlign('center').run()}
        isActive={editor.isActive({ textAlign: 'center' })}
        title="По центру"
      >
        <AlignCenter className="h-4 w-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => editor.chain().focus().setTextAlign('right').run()}
        isActive={editor.isActive({ textAlign: 'right' })}
        title="По правому краю"
      >
        <AlignRight className="h-4 w-4" />
      </ToolbarButton>

      <ToolbarSeparator />

      {/* Text color */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="Цвет текста"
          >
            <Palette className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-2">
          <div className="grid grid-cols-5 gap-1">
            {TEXT_COLORS.map((item) => (
              <button
                key={item.name}
                type="button"
                onClick={() => {
                  if (item.color) {
                    editor.chain().focus().setColor(item.color).run();
                  } else {
                    editor.chain().focus().unsetColor().run();
                  }
                }}
                className={cn(
                  'h-6 w-6 rounded border border-border',
                  !item.color && 'bg-gradient-to-br from-white to-gray-300'
                )}
                style={item.color ? { backgroundColor: item.color } : undefined}
                title={item.name}
              />
            ))}
          </div>
        </PopoverContent>
      </Popover>

      {/* Highlight color */}
      <Popover>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="Выделение"
          >
            <Highlighter className="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-2">
          <div className="grid grid-cols-4 gap-1">
            {HIGHLIGHT_COLORS.map((item) => (
              <button
                key={item.name}
                type="button"
                onClick={() => {
                  if (item.color) {
                    editor.chain().focus().toggleHighlight({ color: item.color }).run();
                  } else {
                    editor.chain().focus().unsetHighlight().run();
                  }
                }}
                className={cn(
                  'h-6 w-6 rounded border border-border',
                  !item.color && 'bg-gradient-to-br from-white to-gray-300 relative after:content-["×"] after:absolute after:inset-0 after:flex after:items-center after:justify-center after:text-gray-400'
                )}
                style={item.color ? { backgroundColor: item.color } : undefined}
                title={item.name}
              />
            ))}
          </div>
        </PopoverContent>
      </Popover>

      <ToolbarSeparator />

      {/* Table */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={cn(
              'h-8 w-8 p-0',
              editor.isActive('table') && 'bg-accent text-accent-foreground'
            )}
            title="Таблица"
          >
            <TableIcon className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={addTable}>
            <Plus className="mr-2 h-4 w-4" />
            Вставить таблицу
          </DropdownMenuItem>
          {editor.isActive('table') && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => editor.chain().focus().addColumnAfter().run()}>
                <TableCellsMerge className="mr-2 h-4 w-4" />
                Добавить столбец
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => editor.chain().focus().addRowAfter().run()}>
                <Plus className="mr-2 h-4 w-4" />
                Добавить строку
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => editor.chain().focus().deleteColumn().run()}>
                <Minus className="mr-2 h-4 w-4" />
                Удалить столбец
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => editor.chain().focus().deleteRow().run()}>
                <Minus className="mr-2 h-4 w-4" />
                Удалить строку
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => editor.chain().focus().deleteTable().run()}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Удалить таблицу
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

export function RichTextEditor({
  value,
  onChange,
  placeholder = 'Начните писать...',
  className,
  disabled = false,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Underline,
      TextStyle,
      Color,
      Highlight.configure({
        multicolor: true,
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    content: value,
    editable: !disabled,
    editorProps: {
      attributes: {
        class: cn(
          'prose prose-sm dark:prose-invert max-w-none',
          'min-h-[200px] p-4 focus:outline-none',
          'prose-headings:mt-4 prose-headings:mb-2',
          'prose-p:my-2 prose-p:leading-relaxed',
          'prose-ul:my-2 prose-ol:my-2',
          'prose-li:my-0.5',
          'prose-table:border-collapse',
          'prose-td:border prose-td:border-border prose-td:p-2',
          'prose-th:border prose-th:border-border prose-th:p-2 prose-th:bg-muted'
        ),
      },
    },
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
  });

  // Sync external value changes
  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value);
    }
  }, [value, editor]);

  // Update editable state
  useEffect(() => {
    if (editor) {
      editor.setEditable(!disabled);
    }
  }, [disabled, editor]);

  return (
    <div
      className={cn(
        'rounded-md border bg-background',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      <Toolbar editor={editor} />
      <EditorContent
        editor={editor}
        className="rich-text-editor"
      />
    </div>
  );
}

