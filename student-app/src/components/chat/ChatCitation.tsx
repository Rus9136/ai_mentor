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
      className="block p-3 bg-purple-50 border border-purple-100 rounded-lg hover:bg-purple-100 transition-colors group"
    >
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
          <BookOpen className="w-4 h-4 text-purple-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-purple-900 truncate">
            {citation.paragraph_title}
          </p>
          <p className="text-xs text-purple-600 truncate">
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
