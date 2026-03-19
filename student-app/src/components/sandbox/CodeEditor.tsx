'use client';

import { useCallback } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { keymap } from '@codemirror/view';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  onRun?: () => void;
  readOnly?: boolean;
  height?: string;
}

export function CodeEditor({
  value,
  onChange,
  onRun,
  readOnly = false,
  height = '100%',
}: CodeEditorProps) {
  const runKeymap = useCallback(() => {
    if (!onRun) return [];
    return [
      keymap.of([
        {
          key: 'Ctrl-Enter',
          mac: 'Cmd-Enter',
          run: () => {
            onRun();
            return true;
          },
        },
      ]),
    ];
  }, [onRun]);

  return (
    <CodeMirror
      value={value}
      onChange={onChange}
      height={height}
      extensions={[python(), ...runKeymap()]}
      readOnly={readOnly}
      basicSetup={{
        lineNumbers: true,
        highlightActiveLineGutter: true,
        highlightActiveLine: true,
        foldGutter: true,
        autocompletion: true,
        bracketMatching: true,
        indentOnInput: true,
        tabSize: 4,
      }}
      className="text-sm border border-border rounded-lg overflow-hidden"
    />
  );
}
