/**
 * Run test cases against student code using Pyodide.
 * All execution happens client-side in the browser.
 */

import { runPython, ensurePyodideLoaded, type PythonResult } from './pyodide-runner';

export interface TestCaseInput {
  input: string;
  expected_output: string;
  description: string | null;
  is_hidden: boolean;
}

export interface TestCaseResult {
  index: number;
  input: string;
  expected: string;
  actual: string;
  passed: boolean;
  is_hidden: boolean;
  description: string | null;
  error: string | null;
  executionTimeMs: number;
}

export interface ChallengeRunResult {
  testResults: TestCaseResult[];
  passed: number;
  total: number;
  allPassed: boolean;
  totalTimeMs: number;
}

/**
 * Compare output: strip trailing whitespace from each line, then compare.
 */
function normalizeOutput(s: string): string {
  return s
    .split('\n')
    .map((line) => line.trimEnd())
    .join('\n')
    .trim();
}

/**
 * Run all test cases for a challenge.
 */
export async function runChallengeTests(
  code: string,
  testCases: TestCaseInput[],
  timeLimitMs: number = 5000
): Promise<ChallengeRunResult> {
  await ensurePyodideLoaded();

  const results: TestCaseResult[] = [];
  let totalTimeMs = 0;

  for (let i = 0; i < testCases.length; i++) {
    const tc = testCases[i];
    const start = performance.now();

    let result: PythonResult;
    try {
      result = await runPython(code, tc.input);
    } catch {
      results.push({
        index: i,
        input: tc.input,
        expected: tc.expected_output,
        actual: '',
        passed: false,
        is_hidden: tc.is_hidden,
        description: tc.description,
        error: 'Failed to execute',
        executionTimeMs: Math.round(performance.now() - start),
      });
      continue;
    }

    const elapsed = result.executionTimeMs;
    totalTimeMs += elapsed;

    if (result.error) {
      results.push({
        index: i,
        input: tc.input,
        expected: tc.expected_output,
        actual: result.stdout,
        passed: false,
        is_hidden: tc.is_hidden,
        description: tc.description,
        error: result.error,
        executionTimeMs: elapsed,
      });
      continue;
    }

    const actual = normalizeOutput(result.stdout);
    const expected = normalizeOutput(tc.expected_output);
    const passed = actual === expected;

    results.push({
      index: i,
      input: tc.input,
      expected: tc.expected_output,
      actual: result.stdout.trim(),
      passed,
      is_hidden: tc.is_hidden,
      description: tc.description,
      error: null,
      executionTimeMs: elapsed,
    });
  }

  const passedCount = results.filter((r) => r.passed).length;

  return {
    testResults: results,
    passed: passedCount,
    total: testCases.length,
    allPassed: passedCount === testCases.length,
    totalTimeMs,
  };
}
