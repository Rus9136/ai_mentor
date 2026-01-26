'use client';

import { Link } from '@/i18n/routing';
import { BookOpen } from 'lucide-react';
import type { Citation } from '@/lib/api/chat';

interface ChatCitationProps {
  citation: Citation;
}

export function ChatCitation({ citation }: ChatCitationProps) {
  return (
    <Link
      href={`/paragraphs/${citation.paragraph_id}`}
      className="block p-3 bg-success/10 border border-success/20 rounded-lg hover:bg-success/20 transition-colors group"
    >
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 w-8 h-8 bg-success/20 rounded-lg flex items-center justify-center group-hover:bg-success/30 transition-colors">
          <BookOpen className="w-4 h-4 text-success" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground truncate">
            {citation.paragraph_title}
          </p>
          <p className="text-xs text-success truncate">
            {citation.chapter_title}
          </p>
          {citation.chunk_text && (
            <p className="mt-1 text-xs text-gray-600 line-clamp-2">
              {citation.chunk_text}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
