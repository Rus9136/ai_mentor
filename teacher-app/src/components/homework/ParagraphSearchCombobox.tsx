'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { Search, X, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useParagraphSearch } from '@/lib/hooks/use-content';
import type { ParagraphSearchResult } from '@/types/content';

interface ParagraphSearchComboboxProps {
  value: ParagraphSearchResult | null;
  onSelect: (result: ParagraphSearchResult | null) => void;
  disabled?: boolean;
}

export function ParagraphSearchCombobox({ value, onSelect, disabled }: ParagraphSearchComboboxProps) {
  const t = useTranslations('homework.search');
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(0);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: results, isLoading } = useParagraphSearch(debouncedQuery);

  // Debounce query
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Reset highlight when results change
  useEffect(() => setHighlightIndex(0), [results]);

  const handleSelect = useCallback((result: ParagraphSearchResult) => {
    onSelect(result);
    setQuery('');
    setIsOpen(false);
  }, [onSelect]);

  const handleClear = useCallback(() => {
    onSelect(null);
    setQuery('');
    inputRef.current?.focus();
  }, [onSelect]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!results?.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && isOpen) {
      e.preventDefault();
      handleSelect(results[highlightIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  }, [results, highlightIndex, isOpen, handleSelect]);

  // Show selected value
  if (value) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm min-w-0">
        <span className="truncate flex-1">
          §{value.number}. {value.title}
          <span className="text-muted-foreground ml-1.5 text-xs">
            {value.textbook_title} {value.grade_level}кл
          </span>
        </span>
        {!disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="text-muted-foreground hover:text-foreground shrink-0"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={t('placeholder')}
          disabled={disabled}
          className="pl-8 pr-8"
        />
        {isLoading && (
          <Loader2 className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>

      {isOpen && query.length >= 2 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="p-3 text-sm text-muted-foreground text-center">{t('searching')}</div>
          ) : results && results.length > 0 ? (
            results.map((item, idx) => (
              <button
                key={item.id}
                type="button"
                onClick={() => handleSelect(item)}
                onMouseEnter={() => setHighlightIndex(idx)}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-accent cursor-pointer ${
                  idx === highlightIndex ? 'bg-accent' : ''
                }`}
              >
                <div className="font-medium">§{item.number}. {item.title}</div>
                <div className="text-xs text-muted-foreground">
                  {item.textbook_title} {item.grade_level}кл, {item.chapter_title}
                </div>
              </button>
            ))
          ) : (
            <div className="p-3 text-sm text-muted-foreground text-center">{t('noResults')}</div>
          )}
        </div>
      )}

      {isOpen && query.length > 0 && query.length < 2 && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover shadow-md">
          <div className="p-3 text-sm text-muted-foreground text-center">{t('typeToSearch')}</div>
        </div>
      )}
    </div>
  );
}
