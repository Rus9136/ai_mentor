const { Document, Packer, Paragraph, TextRun, AlignmentType, UnderlineType } = require('docx');
const fs = require('fs');

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Times New Roman", size: 28 } // 14pt default
      }
    },
    paragraphStyles: [
      {
        id: "Title",
        name: "Title",
        basedOn: "Normal",
        run: { size: 28, bold: true, italics: true, font: "Times New Roman" },
        paragraph: { spacing: { after: 120 }, alignment: AlignmentType.RIGHT }
      },
      {
        id: "Header",
        name: "Header",
        basedOn: "Normal",
        run: { size: 28, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER }
      },
      {
        id: "SubHeader",
        name: "SubHeader",
        basedOn: "Normal",
        run: { size: 28, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.LEFT }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      // Үлгі (шаблон)
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "Үлгі", italics: true, size: 28 })]
      }),

      // Закон ссылкасы
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 240 },
        children: [new TextRun({ text: "«Авторлық құқық және", italics: true, size: 28 })]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "сабақтас құқықтар туралы»", italics: true, size: 28 })]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "ҚР 1996 жылғы 10 маусымдағы", italics: true, size: 28 })]
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 480 },
        children: [new TextRun({ text: "Заңының 9-1 Бабы", italics: true, size: 28 })]
      }),

      // Реферат заголовок
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 120 },
        children: [new TextRun({ text: "Реферат", bold: true, size: 28 })]
      }),

      // Тип объекта
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [new TextRun({ text: "ЭЕМ арналған бағдарлама", bold: true, size: 28 })]
      }),

      // Название
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 360 },
        children: [new TextRun({ text: "«AI Mentor — 7-11 сынып оқушыларына арналған адаптивті білім беру платформасы»", bold: true, size: 28 })]
      }),

      // Автор
      new Paragraph({
        spacing: { before: 240 },
        children: [
          new TextRun({ text: "Автор(-лардың) Тегі, Аты, Әкесінің аты", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 }),
          new TextRun({ text: ": ", bold: true, size: 28 }),
          new TextRun({ text: "Абдуназаров Рыскелдi Дауренұлы", size: 28 })
        ]
      }),

      // Дата создания
      new Paragraph({
        spacing: { before: 240 },
        children: [
          new TextRun({ text: "Объектінің құрылған күні", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 }),
          new TextRun({ text: ": ", bold: true, size: 28 }),
          new TextRun({ text: "2025 жылғы 29 қазан", size: 28 })
        ]
      }),

      // Область применения
      new Paragraph({
        spacing: { before: 360 },
        children: [
          new TextRun({ text: "Қолдану саласы", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 })
        ]
      }),
      new Paragraph({
        spacing: { before: 120, after: 120 },
        children: [new TextRun({
          text: "AI Mentor — Қазақстан Республикасының жалпы білім беретін мектептерінің 7-11 сынып оқушыларына арналған адаптивті білім беру SaaS-платформасы (Software as a Service). Платформа орыс және қазақ тілдерінде жұмыс істейді. Қолдану моделі — әр мектеп деректерінің оқшаулануымен көп иеленушілі (multi-tenant) SaaS. Жүйе веб-қосымшалар және мобильді веб-интерфейс арқылы қол жетімді.",
          size: 28
        })]
      }),

      // Назначение
      new Paragraph({
        spacing: { before: 360 },
        children: [
          new TextRun({ text: "Мақсаты", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 })
        ]
      }),
      new Paragraph({
        spacing: { before: 120, after: 120 },
        children: [new TextRun({
          text: "Бағдарламаның негізгі мақсаты — әр оқушының білім деңгейі мен үлгеріміне қарай оқу процесін бейімдейтін автоматтандырылған білім беру платформасын құру. Негізгі міндеттер:",
          size: 28
        })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 360 },
        children: [new TextRun({ text: "— Адаптивті оқыту: оқушыларды шеберлік деңгейі бойынша A/B/C топтарына автоматты түрде бөлу (A: ≥85% — үздік меңгеру, B: 60-84% — жақсы меңгеру, C: <60% — қосымша көмек қажет);", size: 28 })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 360 },
        children: [new TextRun({ text: "— Жекелендірілген түсіндірмелер: RAG жүйесі оқушының шеберлік деңгейіне бейімделген түсіндірмелер жасайды;", size: 28 })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 360 },
        children: [new TextRun({ text: "— Білім мазмұнын басқару: барлық мектептер үшін жаһандық мазмұн және әр мектеп үшін жеке мазмұн;", size: 28 })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 360 },
        children: [new TextRun({ text: "— Үлгерімді бақылау: мұғалімдер сынып үлгерімін, трендтерді, проблемалы тақырыптарды қадағалай алады;", size: 28 })]
      }),
      new Paragraph({
        spacing: { after: 60 },
        indent: { left: 360 },
        children: [new TextRun({ text: "— Мемлекеттік стандартпен интеграция: мазмұнды МЖМБС (ГОСО) оқу мақсаттарымен байланыстыру;", size: 28 })]
      }),
      new Paragraph({
        spacing: { after: 120 },
        indent: { left: 360 },
        children: [new TextRun({ text: "— Офлайн режим: мобильді қосымша интернетсіз жұмыс істейді, кейін синхрондалады.", size: 28 })]
      }),

      // Функциональные возможности
      new Paragraph({
        spacing: { before: 360 },
        children: [
          new TextRun({ text: "Функционалдық мүмкіндігі", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 })
        ]
      }),
      new Paragraph({
        spacing: { before: 120 },
        children: [new TextRun({ text: "Оқушыларға арналған функциялар:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Google OAuth арқылы тіркелу және авторизация;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Пәндер, тараулар, параграфтар бойынша навигация;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Мәтін оқу, аудио тыңдау, слайдтар мен бейнелерді көру, карточкалар;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Кірістірілген сұрақтарға жауап беру;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Түсіну деңгейін өзін-өзі бағалау;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Әртүрлі тест түрлерін тапсыру (диагностикалық, формативті, жиынтық, практика);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— 4 сұрақ түрі: жалғыз таңдау, көп таңдау, дұрыс/бұрыс, қысқа жауап;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— RAG негізіндегі жекелендірілген түсіндірмелер;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Тараулар мен тесттер бойынша үлгерімді көру.", size: 28 })]
      }),

      new Paragraph({
        spacing: { before: 180 },
        children: [new TextRun({ text: "Мұғалімдерге арналған функциялар:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Жалпы статистика бар басқару тақтасы;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Сыныптар тізімін, оқушылар құрамын басқару;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Оқушыларды A/B/C топтарына бөлу аналитикасы;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Әр оқушының үлгерімін егжей-тегжейлі көру;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Проблемалы тақырыптар аналитикасы;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Шеберлік трендтерін қадағалау;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Үй тапсырмаларын құру және жіберу.", size: 28 })]
      }),

      new Paragraph({
        spacing: { before: 180 },
        children: [new TextRun({ text: "Әкімшілерге арналған функциялар:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Пайдаланушыларды басқару (оқушылар, мұғалімдер, әкімшілер);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Сыныптар құру, оқушыларды бөлу, мұғалімдерді тағайындау;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Жаһандық мазмұнды көру, жеке мазмұн құру;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Оқулықтар мен тесттерді fork ету (көшіріп өңдеу);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Rich Content қосу: мәтін, аудио, слайдтар, бейне, карточкалар;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Параграфтарды МЖМБС оқу мақсаттарымен байланыстыру.", size: 28 })]
      }),

      // Технические характеристики
      new Paragraph({
        spacing: { before: 360 },
        children: [
          new TextRun({ text: "Негізгі техникалық сипаттамалары", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 })
        ]
      }),
      new Paragraph({
        spacing: { before: 120 },
        children: [new TextRun({ text: "Жүйе архитектурасы:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Көп деңгейлі ұйымдастырылған микросервистік архитектура;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Backend API (FastAPI), 3 веб-қосымша (Next.js);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— PostgreSQL деректер қоры pgvector кеңейтімімен;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— 37+ кесте, 27 кестеде Row Level Security (RLS);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— JWT токендері + Google OAuth аутентификациясы;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— RBAC (5 рөл: SUPER_ADMIN, ADMIN, TEACHER, STUDENT, PARENT);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Docker контейнерлеу, Nginx reverse proxy.", size: 28 })]
      }),

      new Paragraph({
        spacing: { before: 180 },
        children: [new TextRun({ text: "AI интеграциялары:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— OpenAI API (text-embedding-3-small) — embeddings үшін;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Jina AI — баламалы embeddings сервисі;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Cerebras LLM — RAG түсіндірмелерін генерациялау.", size: 28 })]
      }),

      new Paragraph({
        spacing: { before: 180 },
        children: [new TextRun({ text: "Қолдау көрсетілетін платформалар:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Web: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Мобильді Web: Chrome Mobile, Safari iOS (iOS 12+, Android 5+).", size: 28 })]
      }),

      // Язык программирования
      new Paragraph({
        spacing: { before: 360 },
        children: [
          new TextRun({ text: "Бағдарламалау тілі", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 })
        ]
      }),
      new Paragraph({
        spacing: { before: 120 },
        children: [new TextRun({ text: "Backend:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Python 3.11+ (негізгі тіл);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— SQL (PostgreSQL 16+ сұраныстар тілі);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Негізгі фреймворктер: FastAPI 0.115+, SQLAlchemy 2.0+, Pydantic 2.9+, Alembic 1.13+, LangChain 0.3+.", size: 28 })]
      }),

      new Paragraph({
        spacing: { before: 180 },
        children: [new TextRun({ text: "Frontend:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— TypeScript 5.7+ (типтелген JavaScript);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— JavaScript/JSX (ES2023);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— CSS (Tailwind 3.4+);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— HTML5;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Негізгі фреймворктер: Next.js 15+, React 19+, TanStack Query 5+, shadcn/ui, Zustand 5+.", size: 28 })]
      }),

      // ЭВМ
      new Paragraph({
        spacing: { before: 360 },
        children: [
          new TextRun({ text: "ЭЕМ жүзеге асырушы", bold: true, underline: { type: UnderlineType.SINGLE }, size: 28 })
        ]
      }),
      new Paragraph({
        spacing: { before: 120, after: 120 },
        children: [new TextRun({ text: "Бағдарлама келесі құрылғылар мен платформаларда жұмыс істейді:", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Клиенттік жақ: Интернетке қосылған кез келген компьютер, планшет немесе смартфон (Chrome, Firefox, Safari, Edge браузерлері);", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Минималды талаптар: RAM 512 MB, CPU Dual-core 1 GHz+, 100 MB бос орын;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Серверлік жақ: Docker контейнерлері Kubernetes немесе Docker Compose ортасында;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Серверлік талаптар: RAM 8+ GB, CPU 4+ cores, 50+ GB SSD;", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Желілік талаптар: 3G+ интернет қосылымы (офлайн режимде клиент жақта жұмыс істей алады).", size: 28 })]
      }),

      new Paragraph({
        spacing: { before: 240 },
        children: [new TextRun({ text: "Production URL мекенжайлары:", bold: true, size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Оқушылар қосымшасы: https://ai-mentor.kz", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Мұғалімдер қосымшасы: https://teacher.ai-mentor.kz", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— Әкімші панелі: https://admin.ai-mentor.kz", size: 28 })]
      }),
      new Paragraph({
        indent: { left: 360 },
        children: [new TextRun({ text: "— API құжаттамасы: https://api.ai-mentor.kz/docs", size: 28 })]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/rus/projects/ai_mentor/copyright_ref_kz_filled.docx", buffer);
  console.log("Файл сәтті құрылды: copyright_ref_kz_filled.docx");
});
