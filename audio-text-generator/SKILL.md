---
name: audio-text-generator
description: "Convert paragraph content into teacher-style audio narration text for the AI Mentor education platform. Use when the user asks to generate audio text, write text for audio, or convert paragraph/explain content into audio-ready format. Triggers on: 'audio text', 'текст для аудио', 'аудио мәтін', 'convert to audio', 'generate audio narration', or when working with the paragraph content audio_text field in AI Mentor."
---

# Audio Text Generator

Convert textbook paragraph content into teacher-style audio narration for school students (grades 5-11). The output is plain text optimized for text-to-speech, written as if a teacher is explaining the topic in class.

## Autonomous Mode (запуск без параметров)

If invoked without specific paragraph IDs or user instructions, the skill operates autonomously:

### 1. Find Next Task

```bash
# Authenticate
TOKEN=$(curl -s -X POST http://localhost:8020/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['access_token'])")

# Get textbook paragraphs (replace TEXTBOOK_ID with target)
curl -s "http://localhost:8020/api/v1/admin/global/textbooks/{TEXTBOOK_ID}/paragraphs" \
  -H "Authorization: Bearer $TOKEN"
```

- Read `state.json` for `next_paragraph_id` and progress.
- If `state.json` is empty or missing — ask the user which textbook/chapter to start with.
- Filter paragraphs where `audio_text` is null or empty.
- Sort by `chapter_id` → `order`, process 1-5 paragraphs per batch.

### 2. Process Each Paragraph

Follow the standard Workflow (Steps 1-5 below) for each paragraph.

### 3. Quality Gate (Self-Check)

After generating audio text, apply the Quality Checklist (13 points from [references/prompt-guide.md](references/prompt-guide.md)):

```
Score the text: count how many of 13 checklist items pass.
- If score >= 11/13 → PASS, save via API.
- If score 10/13 → PASS with warning, save and log the failed items.
- If score < 10/13 → FAIL, regenerate with improved prompt addressing failed items.
- Max 2 regeneration attempts per paragraph. If still failing, save with flag in state.json pending_review.
```

### 4. Update State

After each paragraph, update `state.json`:
```json
{
  "textbook_id": 25,
  "next_paragraph_id": 124,
  "total_paragraphs": 47,
  "total_processed": 12,
  "pending_review": [],
  "quality_scores": {"avg": 12.3, "min": 10, "max": 13},
  "self_improvements": 0,
  "last_run": "2026-03-07T10:00:00Z"
}
```

### 5. Self-Improvement (Reflect)

After processing the batch:
- Analyze all OCR errors encountered — add new patterns to `references/prompt-guide.md` OCR table.
- Check for new textbook directives that were removed — add to the REMOVE list.
- If a new subject type was processed — add Subject-Specific Adaptation section.
- Log improvements: update `state.json` → `self_improvements` counter.

### 6. Repeat or Exit

- If more paragraphs remain → continue to next batch.
- If all done → print summary report and exit:
  ```
  === Audio Text Generation Report ===
  Textbook: {title} (ID: {id})
  Processed: {n}/{total} paragraphs
  Quality: avg {score}/13
  Pending review: {list or "none"}
  Self-improvements made: {n}
  ```

---

## Workflow (Manual & Autonomous)

### Step 1: Fetch Source Content

Determine what source text to use, in priority order:

1. **Kazakh explain_text** (`paragraph-contents/{id}/kz`) — if available and non-empty
2. **Russian explain_text** (`paragraph-contents/{id}/ru`) — if Kazakh is empty
3. **Original paragraph content** (`paragraphs/{id}` → `content` field) — fallback

Fetch via API:
```bash
TOKEN=$(curl -s -X POST http://localhost:8020/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@aimentor.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['access_token'])")

# Get paragraph info (title, number, content)
curl -s http://localhost:8020/api/v1/admin/global/paragraphs/{PARAGRAPH_ID} \
  -H "Authorization: Bearer $TOKEN"

# Get explain text (try kz first, then ru)
curl -s http://localhost:8020/api/v1/admin/global/paragraph-contents/{PARAGRAPH_ID}/kz \
  -H "Authorization: Bearer $TOKEN"
```

### Step 2: Identify Subject and Grade

Check the textbook to determine the subject type — this affects narration style:
- **History (Тарих)**: chronological, cause-effect, enumerate peoples/events
- **Math (Алгебра)**: formulas read verbally, step-by-step, warn about mistakes
- **Informatics**: analogies, simple definitions first
- **Other**: general explanatory style

### Step 3: Generate Audio Text

Read [references/prompt-guide.md](references/prompt-guide.md) for the full system prompt, subject-specific adaptations, examples, and OCR error corrections.

Core structure of generated text:
1. **Greeting**: "Сәлеметсіздер ме, балалар!"
2. **Topic intro**: what we learn today (1-2 sentences)
3. **Body**: simplified content with transitions and numbered lists
4. **Summary**: "Қорытындылайық, балалар..." — repeat main idea
5. **Farewell**: "Рахмет, балалар!" or "Келесі сабақта кездескенше!"

Critical rules:
- REMOVE: HTML tags, "Еске түсір!", "Анықта!", "Біліміңді шыңда", image refs, page numbers
- KEEP: all facts, dates, names, cause-effect chains
- FIX: OCR errors in Kazakh (к→қ, н→ң, у→ұ, Latin→Cyrillic)
- STYLE: short sentences (15-20 words), explain terms inline, number lists
- LENGTH: 2000-5000 characters for a typical paragraph

### Step 4: Save via API

Save the generated text to the `audio_text` field:
```bash
curl -s -X PUT http://localhost:8020/api/v1/admin/global/paragraphs/{PARAGRAPH_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"audio_text": "...generated text..."}'
```

The `audio_text` field is language-independent (stored on the paragraph, not per-language content).

### Step 5: Verify

Confirm the save was successful (HTTP 200) and report the character count.

---

## Batch Processing

When the user asks to process multiple paragraphs:
1. Fetch the list of paragraphs for a textbook/chapter
2. Process each paragraph sequentially
3. Report progress: "Paragraph {number}/{total}: {title} — saved ({length} chars)"
4. Skip paragraphs that already have audio_text (unless user says to overwrite)

---

## Reflection & Self-Improvement (always after processing)

After saving audio_text for each paragraph or batch:

### Quality Gate
1. Apply Quality Checklist (13 items from prompt-guide.md) to the generated text.
2. Score: count passing items out of 13.
3. If score < 10/13 — regenerate with an improved prompt that addresses the failed items.
4. If regeneration fails twice — add paragraph ID to `state.json` → `pending_review`.

### Pattern Discovery
After processing, analyze the source content and generated text:
- **New OCR errors** found during generation → append to OCR Errors Table in `references/prompt-guide.md`.
- **New directives** removed (e.g. "Ойлан!", "Талда!", "Зерттеп көр!") → add to REMOVE list in prompt-guide.md system prompt.
- **New subject processed** → add Subject-Specific Adaptations section in prompt-guide.md.
- **Structural edge cases** (very short paragraphs, image-only, heavy formulas, tables, timelines) → document handling approach in prompt-guide.md.

### How to Update
1. Read the relevant file (`references/prompt-guide.md` or this `SKILL.md`).
2. Edit with the new knowledge — append to existing sections, don't overwrite.
3. Keep entries concise (1-2 lines each).
4. Increment `state.json` → `self_improvements`.
5. Log: "Improved prompt for [subject]: added handling for [pattern]".

### Example Updates
```
# After processing a Biology textbook:
Edit references/prompt-guide.md → "Subject-Specific Adaptations" section:
### Biology (Биология)
- Explain Latin terms with Kazakh equivalents
- Use "Елестетіп көріңдер..." for microscopic processes
- Connect to everyday health/nature examples

# After discovering new OCR error:
Edit references/prompt-guide.md → "Common OCR Errors" table:
| ы → i | кыскымымен → қысымымен | Latin i mixed with Cyrillic |

# After finding new directive to remove:
Edit references/prompt-guide.md → system prompt REMOVE list:
- "Ойлан!", "Талда!" нұсқаулары
```

---

## Headless Execution

Run the skill autonomously from command line:
```bash
# Single run (processes one batch, updates state, exits)
claude -p "audio-text-generator" --output-format json > run_$(date +%Y%m%d_%H%M).json

# Continuous until done
while true; do
  result=$(claude -p "audio-text-generator" --output-format json)
  echo "$result" >> audio_text_log.json
  # Check if all_done
  if echo "$result" | grep -q '"all_done": true'; then break; fi
done
```

The skill will:
1. Read `state.json` → find `next_paragraph_id`.
2. Process 1-5 paragraphs.
3. Apply Quality Gate.
4. Update `state.json` with progress.
5. Self-improve if new patterns found.
6. Exit ready for next invocation.

---

## References

- **[references/prompt-guide.md](references/prompt-guide.md)**: Full system prompt template, subject-specific adaptations, before/after examples, OCR error table, quality checklist
- **state.json**: Processing progress, quality metrics, pending reviews
