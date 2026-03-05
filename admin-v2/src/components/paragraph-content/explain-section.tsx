'use client';

import { useState, useEffect, useCallback } from 'react';
import { FileText, Save, Loader2, Volume2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RichTextEditor } from '@/components/ui/rich-text-editor';
import { Button } from '@/components/ui/button';
import { StatusBadge } from './status-badge';
import type { ParagraphContent, Paragraph } from '@/types';

type Tab = 'explain' | 'audio_text';

interface ExplainSectionProps {
  content: ParagraphContent | null | undefined;
  paragraph: Paragraph | null | undefined;
  paragraphId: number;
  language: string;
  onSave: (explainText: string) => void;
  onSaveAudioText: (audioText: string) => void;
  isLoading?: boolean;
  isLoadingAudioText?: boolean;
}

export function ExplainSection({
  content,
  paragraph,
  paragraphId,
  language,
  onSave,
  onSaveAudioText,
  isLoading = false,
  isLoadingAudioText = false,
}: ExplainSectionProps) {
  const [activeTab, setActiveTab] = useState<Tab>('explain');
  const [text, setText] = useState('');
  const [audioText, setAudioText] = useState('');
  const [isDirty, setIsDirty] = useState(false);
  const [isAudioDirty, setIsAudioDirty] = useState(false);

  // Sync explain text with content
  useEffect(() => {
    setText(content?.explain_text || '');
    setIsDirty(false);
  }, [content?.explain_text, paragraphId, language]);

  // Sync audio text with paragraph
  useEffect(() => {
    setAudioText(paragraph?.audio_text || '');
    setIsAudioDirty(false);
  }, [paragraph?.audio_text, paragraphId]);

  const handleChange = useCallback((newValue: string) => {
    setText(newValue);
    setIsDirty(newValue !== (content?.explain_text || ''));
  }, [content?.explain_text]);

  const handleAudioTextChange = useCallback((newValue: string) => {
    setAudioText(newValue);
    setIsAudioDirty(newValue !== (paragraph?.audio_text || ''));
  }, [paragraph?.audio_text]);

  const handleSave = () => {
    onSave(text);
    setIsDirty(false);
  };

  const handleSaveAudioText = () => {
    onSaveAudioText(audioText);
    setIsAudioDirty(false);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-lg">Объяснение</CardTitle>
        </div>
        {activeTab === 'explain' && (
          <StatusBadge status={content?.status_explain || 'empty'} />
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Tabs */}
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          <button
            onClick={() => setActiveTab('explain')}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === 'explain'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText className="h-3.5 w-3.5 inline-block mr-1.5 -mt-0.5" />
            Текст
          </button>
          <button
            onClick={() => setActiveTab('audio_text')}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              activeTab === 'audio_text'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Volume2 className="h-3.5 w-3.5 inline-block mr-1.5 -mt-0.5" />
            Текст для аудио
          </button>
        </div>

        {/* Explain text tab */}
        {activeTab === 'explain' && (
          <>
            <RichTextEditor
              value={text}
              onChange={handleChange}
              placeholder="Введите переработанный текст параграфа простыми словами для школьника..."
              disabled={isLoading}
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
          </>
        )}

        {/* Audio text tab */}
        {activeTab === 'audio_text' && (
          <>
            <RichTextEditor
              value={audioText}
              onChange={handleAudioTextChange}
              placeholder="Введите текст, который будет преобразован в аудио..."
              disabled={isLoadingAudioText}
            />
            <div className="flex justify-end">
              <Button onClick={handleSaveAudioText} disabled={!isAudioDirty || isLoadingAudioText}>
                {isLoadingAudioText ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Сохранить
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
