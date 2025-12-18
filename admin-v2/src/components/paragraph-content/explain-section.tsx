'use client';

import { useState, useEffect } from 'react';
import { FileText, Save, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { StatusBadge } from './status-badge';
import type { ParagraphContent } from '@/types';

interface ExplainSectionProps {
  content: ParagraphContent | null | undefined;
  paragraphId: number;
  language: string;
  onSave: (explainText: string) => void;
  isLoading?: boolean;
}

export function ExplainSection({
  content,
  paragraphId,
  language,
  onSave,
  isLoading = false,
}: ExplainSectionProps) {
  const [text, setText] = useState('');
  const [isDirty, setIsDirty] = useState(false);

  // Sync local state with content
  useEffect(() => {
    setText(content?.explain_text || '');
    setIsDirty(false);
  }, [content?.explain_text, paragraphId, language]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    setIsDirty(e.target.value !== (content?.explain_text || ''));
  };

  const handleSave = () => {
    onSave(text);
    setIsDirty(false);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Объяснение</CardTitle>
        </div>
        <StatusBadge status={content?.status_explain || 'empty'} />
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          value={text}
          onChange={handleChange}
          placeholder="Введите переработанный текст параграфа простыми словами для школьника..."
          className="min-h-[200px] resize-y"
        />
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={!isDirty || isLoading}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Сохранить
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
