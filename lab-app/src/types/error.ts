export interface APIError {
  code: string;
  message: string;
  detail: string;
  field?: string;
  meta?: Record<string, unknown>;
}
