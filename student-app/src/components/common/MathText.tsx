'use client';

import { useEffect, useRef, memo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface MathTextProps {
  children: string;
  className?: string;
  as?: 'span' | 'div' | 'p';
}

/**
 * Renders text with LaTeX math formulas.
 *
 * Supports:
 * - Inline math: $formula$ (e.g., $x^2 + 1$)
 * - Display math: $$formula$$ (e.g., $$\int_0^1 x dx$$)
 *
 * @example
 * <MathText>Решите уравнение $x^2 - 5x + 6 = 0$</MathText>
 * <MathText>Вычислите интеграл: $$\int_1^3 \frac{4}{x} dx$$</MathText>
 */
function MathTextComponent({ children, className, as: Component = 'span' }: MathTextProps) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!ref.current || !children) return;

    let html = children;

    // Replace display math $$...$$ first (must be before inline to avoid conflicts)
    html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
      try {
        return katex.renderToString(tex.trim(), {
          displayMode: true,
          throwOnError: false,
          strict: false,
        });
      } catch {
        return `<span class="text-red-500">[Math Error: ${tex}]</span>`;
      }
    });

    // Replace inline math $...$
    html = html.replace(/\$([^$\n]+?)\$/g, (_, tex) => {
      try {
        return katex.renderToString(tex.trim(), {
          displayMode: false,
          throwOnError: false,
          strict: false,
        });
      } catch {
        return `<span class="text-red-500">[Math Error: ${tex}]</span>`;
      }
    });

    // Replace newlines with <br> for proper display
    html = html.replace(/\n/g, '<br>');

    ref.current.innerHTML = html;
  }, [children]);

  // If no math detected, just return plain text for better performance
  if (!children?.includes('$')) {
    return <Component className={className}>{children}</Component>;
  }

  return (
    <Component
      ref={ref as React.RefObject<HTMLSpanElement & HTMLDivElement & HTMLParagraphElement>}
      className={className}
    >
      {/* Initial content shown before useEffect runs */}
      {children}
    </Component>
  );
}

// Memoize to prevent unnecessary re-renders
export const MathText = memo(MathTextComponent);

/**
 * Process an HTML string and render LaTeX math formulas via KaTeX.
 *
 * Use this when you have HTML content (e.g. from dangerouslySetInnerHTML)
 * that contains $...$ or $$...$$ LaTeX patterns.
 *
 * @example
 * const processed = renderMathInHtml('<p>Solve $x^2 = 4$</p>');
 * <div dangerouslySetInnerHTML={{ __html: processed }} />
 */
export function renderMathInHtml(html: string): string {
  if (!html || !html.includes('$')) return html;

  let result = html;

  // Replace display math $$...$$ first
  result = result.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    try {
      return katex.renderToString(tex.trim(), {
        displayMode: true,
        throwOnError: false,
        strict: false,
      });
    } catch {
      return `<span class="text-red-500">[Math Error: ${tex}]</span>`;
    }
  });

  // Replace inline math $...$
  result = result.replace(/\$([^$\n]+?)\$/g, (_, tex) => {
    try {
      return katex.renderToString(tex.trim(), {
        displayMode: false,
        throwOnError: false,
        strict: false,
      });
    } catch {
      return `<span class="text-red-500">[Math Error: ${tex}]</span>`;
    }
  });

  return result;
}
