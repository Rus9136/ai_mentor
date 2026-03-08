# Audio Text Generation — Prompt Guide & Examples

## Table of Contents
1. [System Prompt Template](#system-prompt-template)
2. [Subject-Specific Adaptations](#subject-specific-adaptations)
3. [Example: History (Kazakh)](#example-history-kazakh)
4. [Example: Math/Algebra](#example-mathalgebra)
5. [Common OCR Errors in Kazakh](#common-ocr-errors-in-kazakh)
6. [Quality Checklist](#quality-checklist)
7. [Self-Reflection Prompt](#self-reflection-prompt)

---

## System Prompt Template

Use the following system prompt when generating audio text. Adapt the subject-specific section based on the textbook type.

```
Sen — тәжірибелі мұғалімсің. Сенің міндетің — параграфтың мазмұнын оқушыларға аудио сабақ ретінде түсіндіру.

МІНДЕТТІ ЕРЕЖЕЛЕР:

1. ҚҰРЫЛЫМ:
   - Сәлемдесу: "Сәлеметсіздер ме, балалар!"
   - Тақырыпқа кіріспе: бүгін не оқитынымызды қысқаша айту
   - Негізгі мазмұн: параграф мәтінін қарапайым тілмен, түсіндірме стильде баяндау
   - Қорытынды: "Қорытындылайық, балалар..." — негізгі ойды қайталау
   - Қоштасу: "Рахмет, балалар!" немесе "Келесі сабақта кездескенше!"

2. ТІЛ ЖӘНЕ СТИЛЬ:
   - Қарапайым, түсінікті тіл (6-7 сынып деңгейі)
   - Күрделі терминдерді бірден түсіндіру: "Ляо мемлекеті — бұл қидандар құрған ел"
   - Қысқа сөйлемдер (15-20 сөзден аспасын)
   - Ауызекі-ғылыми стиль: мұғалім тікелей сөйлеп тұрғандай

3. АУДИО АДАПТАЦИЯ:
   - Визуалды сілтемелер ЖОҚК: "суретте көріп тұрсыздар" — ҚОЛДАНБА
   - "Анықта!", "Еске түсір!" сияқты оқулық нұсқауларын АЛЫП ТАСТАУ
   - Тізімдерді нөмірлеу: "Біріншіден... Екіншіден... Үшіншіден..."
   - Өтпе сөздерді қолдану: "Ал енді...", "Бұл неге маңызды?", "Енді қарастырайық..."

4. НЕ АЛЫП ТАСТАУ КЕРЕК:
   - HTML тегтері (<p>, <h3>, <ul>, <img> т.б.)
   - "Бұл сабақта:" блогы (бірақ мазмұнын кіріспеде қолдануға болады)
   - "Тірек сөздер" блогы (бірақ терминдерді мәтін ішінде түсіндіру)
   - "Біліміңді шыңда" сұрақтары
   - "Еске түсір!", "Анықта!", "Есте сақта!" нұсқаулары
   - "Ойлан!", "Талда!", "Зерттеп көр!" нұсқаулары
   - Суреттерге сілтемелер
   - Бет нөмірлері

5. НЕ САҚТАУ КЕРЕК:
   - Барлық фактілер, даталар, атаулар
   - Себеп-салдарлық байланыстар
   - Хронологиялық реттілік
   - Географиялық мәліметтер
```

---

## Subject-Specific Adaptations

### History (Тарих)
- Emphasize chronological flow and cause-effect chains
- Number events or groups when listing many items
- Use phrases: "Сол кезде...", "Осыдан кейін...", "Нәтижесінде..."
- Explain each tribe/state/figure briefly when first mentioned
- Connect historical events to modern Kazakhstan where relevant

### Math/Algebra (Алгебра/Математика)
- Read formulas verbally: "x квадрат плюс 2x минус 3 тең нөл"
- Explain step-by-step solutions as if writing on a board
- Use phrases: "Енді келесі қадамға көшейік", "Мұнда не болып жатқанын қарайық"
- Warn about common mistakes: "Көп оқушы мұнда қателеседі..."
- Keep formula explanations conceptual, not just procedural

### Informatics (Информатика)
- Explain technical terms in simple words first
- Use everyday analogies for abstract concepts
- Use phrases: "Мысалы, күнделікті өмірде...", "Мұны қарапайым тілмен айтсақ..."

---

## Example: History (Kazakh)

### Input (original content, HTML):
```html
<h3>Бул сабақта:</h3>
<ul><li>Ұлы Дала аумағына шығыстан ығысып келіп қоныстанған түркі тайпаларының тарихын оқимыз</li></ul>
<h3>Тірек сөздер</h3>
<ul><li>қидан</li><li>Ляо мемлекеті</li></ul>
<p>Еске түсір! X ғасырдан бұрын батысқа қоныс аударған қандай түркі тайпаларын білесің?</p>
<p>924 жылы басталған кидандардын Орталык Азия далаларына жорыктары үлкен қасіретке айналды...</p>
<p>Анықта! Қидандар дегендер кімдер?</p>
<p>...мәтін жалғасы...</p>
<h3>Біліміңді шыңда:</h3>
<div><strong>1.</strong> Картада көрсетілген түркі тайпаларын анықта.</div>
```

### Output (audio text):
```
Сәлеметсіздер ме, балалар! Бүгінгі сабағымызда біз X-XIII ғасырлардағы Ұлы Даланың саяси картасының қалай өзгергенін талқылаймыз. Бұл — қазақ халқының қалыптасуын түсіну үшін өте маңызды тақырып.

Ендеше, бастайық.

Бәрі 924 жылы басталды. Сол кезде шығыстан — қидандар деп аталатын тайпалар Орталық Азия далаларына жорық жасады. Қидандар — бұлар түркі емес, тұңғыс-маньчжур тілінде, яғни көне монғол тілінде сөйлейтін халық...

[...structured numbered content...]

Қорытындылайық, балалар. [...негізгі ой қайталанады...]

Келесі сабақта осы тақырыпты тереңірек талқылаймыз. Рахмет, балалар!
```

Key transformations applied:
- "Бұл сабақта" list -> woven into introduction
- "Тірек сөздер" -> terms explained inline when first encountered
- "Еске түсір!" and "Анықта!" -> removed entirely
- "Біліміңді шыңда" questions -> removed entirely
- Multiple tribes listed -> numbered (Біріншіден... Екіншіден...)
- Image references -> removed
- OCR errors fixed (кндандардын -> қидандардың)

---

## Example: Math/Algebra

### Input:
```
Квадрат теңдеу ax² + bx + c = 0 түрінде жазылады, мұнда a ≠ 0.
Дискриминант формуласы: D = b² - 4ac
Егер D > 0 болса, теңдеудің екі түбірі бар...
```

### Output:
```
Сәлеметсіздер ме, балалар! Бүгін біз квадрат теңдеулерді шешуді үйренеміз. Бұл — алгебрадағы ең маңызды тақырыптардың бірі.

Квадрат теңдеу деген не? Бұл — "а икс квадрат плюс бэ икс плюс цэ тең нөлге" деген түрде жазылатын теңдеу. Мұнда ең басты шарт — "а" коэффициенті нөлге тең болмауы керек.

Оны шешу үшін бізге дискриминант деген формула керек. Дискриминант — "Д тең бэ квадрат минус төрт а цэ". Бұл формуланы жаттап алыңдар, себебі ол бізге теңдеудің жауаптары қанша екенін айтады.

Егер дискриминант нөлден үлкен болса — теңдеудің екі жауабы бар...

Қорытындылайық, балалар...
```

---

## Common OCR Errors in Kazakh

Textbook content is often loaded from OCR (Mathpix), which introduces systematic errors in Kazakh text. Fix these when generating audio text:

| OCR Error | Correct | Note |
|-----------|---------|------|
| к → қ | кидан → қидан | Before/after vowels |
| н → ң | онтүстік → оңтүстік | Before г, к |
| е → ё | жонылып → жойылып | Rare |
| и → і | билігін → білігін | Common |
| у → ұ, ү | курылымы → құрылымы | Context-dependent |
| о → ө | козенінін → өзенінің | Context-dependent |
| Missing spaces | батыскажылжып → батысқа жылжып | |
| Double letters | mатарлар → татарлар | OCR artifact |
| Latin mixed | mемлекет → мемлекет | m(lat) vs м(cyr) |

Always proofread the generated text for these patterns.

---

## Quality Checklist

Before saving audio text, verify:

1. [ ] Starts with "Сәлеметсіздер ме, балалар!" (or similar greeting)
2. [ ] Has introduction stating the topic
3. [ ] No HTML tags remain
4. [ ] No "Еске түсір!", "Анықта!", "Есте сақта!" directives
5. [ ] No "Біліміңді шыңда" questions
6. [ ] No image references or page numbers
7. [ ] All key terms explained inline
8. [ ] Lists are numbered for audio clarity
9. [ ] Transitions between sections are smooth
10. [ ] Ends with summary + farewell
11. [ ] OCR errors corrected
12. [ ] All facts and dates from original preserved
13. [ ] Length is reasonable (2000-5000 chars for typical paragraph)

**Scoring:**
- 13/13 = excellent
- 11-12/13 = good, save
- 10/13 = acceptable, save with warning
- <10/13 = regenerate (max 2 attempts, then flag for review)

---

## Self-Reflection Prompt (Quality Gate + Self-Improvement)

After generating audio text, use this prompt to evaluate and improve:

```
Ты — критик audio_text_generator. Проверь сгенерированный текст по чеклисту из 13 пунктов.

ВХОД:
- original_content: {исходный контент параграфа}
- generated_audio_text: {сгенерированный аудио-текст}
- subject: {предмет: тарих/алгебра/информатика/другое}

ПРОВЕРКА (каждый пункт: pass/fail + причина если fail):
1. Приветствие "Сәлеметсіздер ме, балалар!" или аналог?
2. Кіріспе — тақырып айтылды ма?
3. HTML тегтер жоқ па?
4. "Еске түсір!", "Анықта!", "Есте сақта!" нұсқаулары жоқ па?
5. "Біліміңді шыңда" сұрақтары жоқ па?
6. Суреттерге сілтемелер, бет нөмірлері жоқ па?
7. Терминдер мәтін ішінде түсіндірілді ме?
8. Тізімдер нөмірленді ме?
9. Бөлімдер арасында өтпе сөздер бар ма?
10. Қорытынды + қоштасу бар ма?
11. OCR қателері түзетілді ме?
12. Барлық фактілер, даталар сақталды ма?
13. Ұзындығы 2000-5000 символ аралығында ма?

ФОРМАТ ЖАУАБЫ (JSON):
{
  "score": "X/13",
  "passed": [1, 2, 3, ...],
  "failed": [
    {"item": 7, "reason": "Термин 'қаған' түсіндірілмеген", "fix": "Қаған — бұл түрк мемлекетінің билеушісі деп қосу"}
  ],
  "new_ocr_patterns": [
    {"error": "г → ғ", "example": "гылыми → ғылыми", "note": "Before ы, а vowels"}
  ],
  "new_directives_found": ["Ойлан!", "Талда!"],
  "verdict": "PASS" | "REGENERATE" | "REVIEW",
  "improvement_suggestions": ["..."]
}
```

### How the Self-Reflection Loop Works

1. **Generate** audio text using the System Prompt Template.
2. **Evaluate** using the Self-Reflection Prompt above.
3. **If PASS** → save via API, update state.json.
4. **If REGENERATE** → fix the failed items, regenerate, re-evaluate (max 2 retries).
5. **If REVIEW** → save paragraph ID to `state.json` → `pending_review`.
6. **If new_ocr_patterns found** → append to OCR Errors Table above.
7. **If new_directives_found** → append to REMOVE list in System Prompt Template.
8. **Log** all improvements for the session report.
