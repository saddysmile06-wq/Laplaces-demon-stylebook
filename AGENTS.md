# laplace-mascot: инструкция для ИИ-агентов

Репозиторий с каноном, стайлбуком, арт-ассетами и пайплайном маскота проекта «Демон Лапласа» (демоница Лаплас, пиксель-арт). Этот файл читают Claude Code, Codex и любые другие агенты. Для ChatGPT в браузере есть готовые инструкции: `ai/generated/chatgpt-instructions.md`.

Язык общения: русский, коротко. Названия файлов и ключи JSON: латиница, `kebab-case`.

## Установка (если тебя просят «установи / подними проект»)

Делай это сам, по шагам, не спрашивая лишнего. Нужны Python 3.9+, git, git-lfs.

1. Проверь инструменты: `python --version` (на macOS/Linux `python3`), `git --version`, `git lfs version`. Нет git-lfs: Windows `winget install GitHub.GitLFS`, macOS `brew install git-lfs`, Linux `sudo apt install git-lfs`. Нет Python: https://www.python.org/downloads/.
2. Если проекта ещё нет на диске: `git lfs install`, затем `git clone <URL> laplace-mascot`, `cd laplace-mascot`. **Не качай ZIP**: в нём вместо картинок заглушки LFS.
3. Одна команда делает всё остальное: `python tools/setup.py --serve` (macOS/Linux: `python3 ...`). Она проверит окружение, сама выполнит `git lfs pull`, создаст `.venv`, поставит Pillow, прогонит `validate`, `build`, `export` и поднимет сервер.
4. Сервер блокирует терминал: запусти его в фоне и не жди завершения. Ссылка на демо: **http://localhost:8790/demo/**. Без сервера демо тоже открывается файлом `demo/index.html`.
5. Только диагностика: `python tools/setup.py --check`. Строки `[FAIL]` содержат причину и что сделать.
6. Итог напиши человеку коротко: что поставлено, ссылка на демо, что не получилось. Установка ничего не меняет в git: не коммить после неё.

Типичные сбои: картинки не грузятся в демо или Pillow ругается на файл — это заглушки LFS, выполни `git lfs pull`; `venv` не создаётся на Debian/Ubuntu — `sudo apt install python3-venv`; порт 8790 занят — освободи его или открой `demo/index.html` напрямую.

## Порядок чтения (до любой правки или генерации)

1. `canon/character.json`: внешность, три формы, правила. **Источник правды.**
2. `canon/palette.json`: цвета.
3. `stylebook/03-do-dont.md`: что можно и нельзя.
4. Нужный воркфлоу из `ai/workflows/`.
5. Референсы из `assets/references/` и `assets/scenes/splash-mascot.webp` (посмотри картинку, а не только читай текст).

## Незыблемое

- Внешность берётся **из арта и `canon/`**, не из брифов и раскадровок. Они дают позы, камеру и окружение. Если бриф спорит с артом, прав арт; заметь расхождение в `stylebook/03-do-dont.md`.
- Лицо, волосы, **ровно два рога**, уши, хвост со стрелкой одинаковы во всех формах и кадрах. Лишние конечности только в форме `demon`, крылья только в `winged`.
- Пиксель-арт: крупные квадратные пиксели, плоские блоки, **без** градиентов, сглаживания, мягкого свечения. Масштаб только целым и nearest-neighbor.
- Цвета только из `canon/palette.json` (до 20 на набор кадров). Новый цвет = правка палитры, а не «на глаз».
- Casual: уютные позы, не сексуализировать. Без текста, водяных знаков, оружия.
- `assets/from-regina/` (записи с `"approved": true`) — арты, **утверждённые автором**; можно брать как образец. Подпапка `references/` там и `assets/references/` — только референсы, не канон. Крылья и «фансервис»-позы утверждённых артов — отдельная форма `winged`, не базовая casual; розовые волосы из чужих референсов не переносить.
- Tech-id проекта и название «Лаплас» / «Димон» не переименовывать.
- **Коммиты и push: здесь делает агент сам, по правилам `ai/workflows/autocommit.md`** (исключение из правила корня `Obsidian-Data`, по решению автора). Только через `python tools/autocommit.py`. Push запрещён, пока автор не поставит `first_push_confirmed` в `tools/autocommit.json`.
- Оригиналы не удалять и не перезаписывать: новую версию клади рядом (`-v4`), старую убирай в `archive/` только по просьбе.

## Структура

| Путь | Что |
|---|---|
| `canon/` | правда: `character.json`, `palette.json`, `poses.json`. Правится вручную |
| `stylebook/` | объяснения для людей (формы, палитра, анимации, можно/нельзя) |
| `assets/<раздел>/` | готовые арты; в каждом `index.json` с подписями (**обязательно**) |
| `assets/clips/<id>/` | анимации-клипы: `source/*.aseprite`, `export/` (лист, json, webp, gif), `clip.json`. Покадровый `frames/` в .gitignore |
| `ai/` | инструкции и промпты для нейросетей; `ai/generated/` создаётся билдом, руками не править |
| `pipeline/` | скрипты (часть со старыми абсолютными путями) |
| `archive/` | старые версии, сырьё, проверочные кадры |
| `demo/` | `index.html`, галерея, палитра, конструктор промптов; **генерируется** |
| `tools/` | `build.py`, `validate.py`, `sync_to_plugin.py` |

## Команды

```powershell
python tools/validate.py          # проверка: файлы есть, JSON валиден, палитра корректна
python tools/build.py             # пересобрать demo/index.html и ai/generated/*
python tools/export.py            # восстановить покадровые PNG клипов из спрайт-листа (Aseprite не нужен)
python tools/sync_to_plugin.py --plugin "C:\Obsidian-Data\MyLibrary\.obsidian\plugins\laplace-demon"   # скопировать ассеты в плагин
```

Окружение (Python 3.9+, `.venv`, Pillow, Git LFS) ставится одной командой `python tools/setup.py`, см. раздел «Установка» выше. Команды ниже запускай python из `.venv` (`.venv/Scripts/python` на Windows, `.venv/bin/python` на macOS/Linux) или любым Python с Pillow.

## Что делать в типовых задачах

**Добавить ассет**
1. Положи файл в подходящий `assets/<раздел>/` (kebab-case, версия суффиксом `-v2`).
2. Допиши запись в `assets/<раздел>/index.json`: `file`, `title`, `caption` (что это и зачем, 1–2 предложения). Для файла, который использует плагин, добавь `"plugin": "<путь внутри плагина>"`.
3. `python tools/validate.py`, затем `python tools/build.py`.
4. Запиши строку в `CHANGELOG.md`.

**Сгенерировать картинку / позу / эмоцию**
1. Прочитай `ai/workflows/generate-image.md`. Собери промпт: STYLE + CORE + outfit/framing формы + RULES + поза. Проще всего открыть `demo/index.html`, вкладка «Конструктор промптов».
2. Прикрепи референс формы.
3. Проверь результат по `ai/qa-checklist.md`. Сырьё в `archive/`, принятое в `assets/`.

**Добавить кадры / новый клип** (кадров может быть сколько угодно)
1. Один клип = одна папка `assets/clips/<id>/` (kebab-case) и один `.aseprite` в `source/`. Длинное режем на клипы по ~100–300 кадров.
2. В git кладём только `source/*.aseprite`, `export/` (спрайт-лист + json + webp/gif) и `clip.json` (скопируй из `oracle-v3`). **Покадровые PNG не коммитим**, они в `.gitignore`.
3. Лист и json экспортирует художник из Aseprite; остальным ничего не нужно: `python tools/export.py <id>` режет кадры из листа.
4. `validate.py` сверяет число кадров в `clip.json` и `sheet.json`; затем `build.py`.
5. Не складывай несколько клипов в один `.aseprite`: каждая правка копирует файл целиком в LFS.

**Сделать анимацию**
1. Если хватает одного кадра: скриптом (`stylebook/04-animation-recipes.md`), без ИИ.
2. Новые позы: `ai/workflows/pixellab-notes.md` (там же слова, которые блокирует фильтр).
3. По раскадровке: `ai/workflows/animate-from-storyboard.md` и шаблон брифа `ai/templates/animation-brief.tmpl.md`.

**Поменять канон** (рога, цвета, форму, новую форму)
Это крупное решение: сначала обсуди с человеком, правь `canon/*`, запусти `python tools/build.py`, опиши в `CHANGELOG.md`. Для новой формы предложи ADR, но не оформляй сам.

## Готово, когда

- `python tools/validate.py` без ошибок;
- `python tools/build.py` отработал, `demo/index.html` открывается двойным кликом;
- в `CHANGELOG.md` есть запись;
- работа закоммичена (`python tools/autocommit.py commit -m "..."`), push по правилам автокоммита;
- в ответе человеку: что добавлено/изменено, что **не** проверено, какие расхождения нашёл.
