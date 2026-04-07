'use client';

import React, { useRef, useLayoutEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

/**
 * Format up to 10 subscriber digits as (XXX) XXX-XX-XX
 */
function formatSubscriber(d: string): string {
  if (!d) return '';
  let r = '(';
  r += d.slice(0, 3);
  if (d.length >= 3) r += ') ';
  if (d.length > 3) r += d.slice(3, 6);
  if (d.length >= 6) r += '-';
  if (d.length > 6) r += d.slice(6, 8);
  if (d.length >= 8) r += '-';
  if (d.length > 8) r += d.slice(8, 10);
  return r;
}

/** Get indices of digit characters in the formatted string */
function getDigitPositions(formatted: string): number[] {
  const positions: number[] = [];
  for (let i = 0; i < formatted.length; i++) {
    if (/\d/.test(formatted[i])) positions.push(i);
  }
  return positions;
}

/** Count digits that appear before `pos` in the string */
function countDigitsBefore(str: string, pos: number): number {
  let count = 0;
  for (let i = 0; i < pos && i < str.length; i++) {
    if (/\d/.test(str[i])) count++;
  }
  return count;
}

/** Find cursor position in formatted string after the n-th digit (1-based) */
function cursorAfterNthDigit(formatted: string, n: number): number {
  if (n <= 0) return formatted.indexOf('(') >= 0 ? 1 : 0; // after "("
  const positions = getDigitPositions(formatted);
  if (n > positions.length) return formatted.length;
  return positions[n - 1] + 1;
}

interface PhoneInputProps {
  digits: string;
  onDigitsChange: (digits: string) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  id?: string;
  autoComplete?: string;
  className?: string;
}

export function PhoneInput({
  digits,
  onDigitsChange,
  placeholder = '(707) 123-45-67',
  className,
  disabled,
  ...inputProps
}: PhoneInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const cursorPosRef = useRef<number | null>(null);

  // Restore cursor position after React re-renders the formatted value
  useLayoutEffect(() => {
    if (cursorPosRef.current !== null && inputRef.current) {
      inputRef.current.setSelectionRange(
        cursorPosRef.current,
        cursorPosRef.current
      );
      cursorPosRef.current = null;
    }
  });

  const formatted = formatSubscriber(digits);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const el = e.target;
      const rawValue = el.value;
      const cursorPos = el.selectionStart ?? rawValue.length;

      // How many digits sit before the cursor in the (already modified) raw value
      const digitsBefore = countDigitsBefore(rawValue, cursorPos);

      // Extract only digit characters, cap at 10
      const newDigits = rawValue.replace(/\D/g, '').slice(0, 10);

      // Compute where the cursor should land in the newly formatted string
      const newFormatted = formatSubscriber(newDigits);
      cursorPosRef.current = cursorAfterNthDigit(newFormatted, digitsBefore);

      onDigitsChange(newDigits);
    },
    [onDigitsChange]
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();
      const text = e.clipboardData.getData('text');
      let pastedDigits = text.replace(/\D/g, '');
      // Strip country code prefix (87..., +77..., 77...)
      if (pastedDigits.startsWith('87') && pastedDigits.length >= 11)
        pastedDigits = pastedDigits.slice(1);
      if (pastedDigits.startsWith('7') && pastedDigits.length >= 11)
        pastedDigits = pastedDigits.slice(1);
      pastedDigits = pastedDigits.slice(0, 10);
      if (pastedDigits) {
        const newFormatted = formatSubscriber(pastedDigits);
        cursorPosRef.current = newFormatted.length;
        onDigitsChange(pastedDigits);
      }
    },
    [onDigitsChange]
  );

  return (
    <div className="flex">
      <span
        className={cn(
          'inline-flex items-center rounded-l-md border border-r-0 border-input bg-muted px-3 text-sm text-muted-foreground select-none',
          disabled && 'cursor-not-allowed opacity-50'
        )}
      >
        +7
      </span>
      <input
        ref={inputRef}
        type="tel"
        inputMode="tel"
        className={cn(
          'flex h-10 w-full rounded-md rounded-l-none border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        value={formatted}
        onChange={handleChange}
        onPaste={handlePaste}
        placeholder={placeholder}
        disabled={disabled}
        {...inputProps}
      />
    </div>
  );
}
