export interface LessonPlanGenerateRequest {
  paragraph_id: number;
  class_id?: number;
  language: string;
  duration_min: number;
}

export interface TaskDescriptor {
  text: string;
  score: number;
}

export interface LessonTask {
  number: number;
  teacher_activity: string;
  student_activity: string;
  descriptors: TaskDescriptor[];
  total_score: number;
}

export interface LessonStage {
  name: string;
  name_detail: string;
  duration_min: number;
  method_name: string;
  method_purpose: string;
  method_effectiveness: string;
  teacher_activity: string;
  student_activity: string;
  assessment: string;
  differentiation: string | null;
  resources: string;
  tasks: LessonTask[];
}

export interface LessonPlanHeader {
  section: string;
  topic: string;
  learning_objective: string;
  lesson_objective: string;
  monthly_value: string;
  value_decomposition: string;
}

export interface DifferentiationBlock {
  approach: string;
  for_level_a: string;
  for_level_b: string;
  for_level_c: string;
}

export interface LessonPlanData {
  header: LessonPlanHeader;
  stages: LessonStage[];
  total_score: number;
  differentiation: DifferentiationBlock | null;
  health_safety: string;
  reflection_template: string[];
}

export interface LessonPlanContext {
  paragraph_title: string;
  chapter_title: string;
  textbook_title: string;
  subject: string;
  grade_level: number;
  mastery_distribution: Record<string, number> | null;
  total_students: number | null;
  struggling_topics: string[] | null;
}

export interface LessonPlanGenerateResponse {
  lesson_plan: LessonPlanData;
  context: LessonPlanContext;
}
