'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { StudentTextbook } from '@/lib/api/textbooks';
import { TextbookCard } from './TextbookCard';

interface TextbookSectionProps {
  title: string;
  textbooks: StudentTextbook[];
  defaultOpen?: boolean;
  icon?: React.ReactNode;
}

export function TextbookSection({
  title,
  textbooks,
  defaultOpen = true,
  icon,
}: TextbookSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (textbooks.length === 0) return null;

  return (
    <section className="mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 mb-4 w-full text-left group"
      >
        {icon}
        <h2 className="text-lg font-bold text-foreground">{title}</h2>
        <span className="text-sm text-muted-foreground ml-1">({textbooks.length})</span>
        <ChevronDown
          className={`h-5 w-5 text-muted-foreground ml-auto transition-transform ${
            isOpen ? '' : '-rotate-90'
          }`}
        />
      </button>

      {isOpen && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {textbooks.map((textbook) => (
            <TextbookCard key={textbook.id} textbook={textbook} />
          ))}
        </div>
      )}
    </section>
  );
}
