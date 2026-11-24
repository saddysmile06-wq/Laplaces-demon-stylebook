# ИИ-инструкции: как подключить нейросеть к маскоту

Одна правда (`canon/`), несколько способов донести её до модели.

| Где работаешь | Что дать модели |
|---|---|
| **Claude Code / Codex** в этом репо | ничего: `AGENTS.md` и `CLAUDE.md` в корне подхватятся сами. Установка проекта: раздел «Установка» в `AGENTS.md` |
| **ChatGPT** (Project или свой GPT) | вставь `ai/generated/chatgpt-instructions.md` в Instructions проекта, прикрепи 3 референса: `assets/references/ref_casual_sprite.png`, `ref_mecha.png`, `assets/scenes/splash-mascot.webp` |
| **ChatGPT, разовая картинка** | собери промпт в `demo/index.html` → «Конструктор промптов», прикрепи референс формы |
| **PixelLab** | `ai/workflows/pixellab-notes.md` (настройки, цепочка якорей, запрещённые слова) |
| **Анимация по раскадровке** | `ai/templates/animation-brief.tmpl.md` + `ai/workflows/animate-from-storyboard.md` |

## Как это устроено
- `ai/templates/system-prompt.tmpl.md` — шаблон, пишется вручную.
- `python tools/build.py` подставляет в него данные из `canon/` и кладёт результат в `ai/generated/chatgpt-instructions.md`. Руками этот файл не править: следующий билд перезапишет.
- Поменял канон → запусти билд → вставь свежий файл в ChatGPT-проект. Так инструкция не расходится с каноном.
- Лимит Instructions в ChatGPT около 8000 символов; билд предупредит, если файл длиннее.

## Папки
- `templates/` — шаблоны (системный промпт, бриф анимации).
- `workflows/` — пошаговые рецепты.
- `prompts/` — готовые и устаревшие промпты (`legacy-chatgpt-prompts.md` собран из `canon/poses.json`, `example-animation-brief.md` — пример брифа от прошлой работы, там цвет волос неверный, см. `stylebook/03-do-dont.md`).
- `qa-checklist.md` — чем проверять результат.
