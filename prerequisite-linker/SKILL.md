---
name: prerequisite-linker
description: >
  Create and manage prerequisite links (knowledge graph) between textbook paragraphs
  within a subject for the AI Mentor education platform. Builds the foundation for
  individualized learning trajectories based on Kazakhstan's spiral curriculum model.
  Use when: (1) user says 'создай связи', 'link prerequisites', 'prerequisites for [subject]',
  'связи параграфов', 'граф зависимостей'; (2) user provides a subject name and wants
  prerequisite coverage; (3) user asks to check or report prerequisite links for a subject.
  Supports subjects: Алгебра, Қазақстан тарихы, Информатика, Ағылшын тілі, and any other
  subject in the AI Mentor database.
---

# Prerequisite Linker

Build the knowledge graph of paragraph dependencies across textbooks within a subject.

## Purpose

In Kazakhstan's spiral curriculum, the same topics are taught each year with increasing depth.
This skill creates directed prerequisite links between paragraphs so the system can:

1. **Warn students** before starting a paragraph if prerequisites are weak
2. **Suggest review** of foundational topics when a student struggles
3. **Build individual learning trajectories** — if a student doesn't understand topic X,
   the system follows the prerequisite chain to find the right level to restart from

## Input

The user provides a **subject name** (e.g., "Алгебра", "Информатика", "История").
Optionally: specific textbook IDs or grade range to focus on.

## Workflow

### Phase 1: Report current state

1. Find the subject_id by searching textbooks matching the subject name:
   ```sql
   SELECT DISTINCT t.subject_id, t.title FROM textbooks t
   WHERE t.title ILIKE '%{SUBJECT_NAME}%' AND t.school_id IS NULL;
   ```
2. Load all textbooks for this subject (sorted by grade_level)
3. Load all paragraphs grouped by textbook/grade
4. Query existing prerequisite links for the subject
5. Present a summary report:
   - List of textbooks with paragraph counts
   - Count of existing links (required/recommended)
   - Table of existing links if any
6. Read `references/linking-log.md` to check if this subject was previously processed
7. Show the report to the user and confirm before proceeding

### Phase 2: Analyze and create links

1. Read `references/spiral-curriculum.md` for subject-specific patterns and linking rules
2. Group paragraphs into **thematic clusters** by matching keywords in titles across grades
3. For each cluster, determine the learning progression (lower grade → higher grade)
4. For ambiguous titles or OCR-damaged text, read paragraph content:
   ```sql
   SELECT p.id, p.title, LEFT(p.content, 500) FROM paragraphs p WHERE p.id = {ID};
   ```
5. Determine `strength`:
   - `required` — topic B is impossible without topic A (formulas, definitions used directly)
   - `recommended` — topic B benefits from A but is understandable standalone
6. Create links via batch SQL INSERT:
   ```sql
   INSERT INTO paragraph_prerequisites (paragraph_id, prerequisite_paragraph_id, strength)
   VALUES (target_id, prereq_id, 'required')
   ON CONFLICT (paragraph_id, prerequisite_paragraph_id) DO NOTHING;
   ```
7. After each batch, verify with a SELECT to confirm creation
8. Present created links to user in a readable table

### Phase 3: Update memory

After completing work, update `references/linking-log.md`:

1. Add or update subject entry with: textbook list, link count, discovered patterns
2. Document specific chains created with paragraph IDs
3. Add notes and lessons learned (OCR issues, naming conventions, etc.)
4. If new patterns discovered — add to "Общие паттерны" section

## DB connection

```bash
docker exec ai_mentor_postgres_prod psql -U ai_mentor_user -d ai_mentor_db -c "SQL"
```

Full SQL templates: `references/db-queries.md`

## Rules

- **Same subject_id only** — both paragraphs must belong to textbooks with matching subject_id
- **No self-links** — paragraph_id != prerequisite_paragraph_id
- **No cycles** — backend validates with BFS (max depth 10), but avoid obvious cycles
- **Skip review paragraphs** — "Проверь себя!", "Өзіңді тексер!", "Қайталау" are not link targets
- **Use ON CONFLICT DO NOTHING** — safe against duplicate inserts
- **Read content when unsure** — don't guess from ambiguous titles alone
- **Batch inserts** — group related links into single INSERT for efficiency
- **Verify after insert** — confirm with COUNT or SELECT
- OCR damage is common in titles (ЗАГЛАВНЫЕ, letter errors) — fuzzy match needed

## References

| File | When to read |
|------|-------------|
| `references/spiral-curriculum.md` | Phase 2: for subject-specific patterns and strength rules |
| `references/db-queries.md` | Any phase: SQL query templates |
| `references/linking-log.md` | Phase 1: check previous work. Phase 3: update with results |
