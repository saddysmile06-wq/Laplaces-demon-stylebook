# laplace-mascot

Канон, стайлбук, арты и анимации маскота проекта «Демон Лапласа»: демоница Лаплас («Димон»), пиксель-арт. Единое место для людей и нейросетей.

## Установка одним кликом

**Нужно один раз на машине:** [Python 3.9+](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads) и [Git LFS](https://git-lfs.com) (`winget install GitHub.GitLFS` / `brew install git-lfs` / `sudo apt install git-lfs`).

**Вариант 1: через ИИ-агента (Claude Code, Codex, любой с доступом к терминалу).** Вставь в чат агента:

> Установи проект: `git lfs install`, затем `git clone https://github.com/saddysmile06-wq/Laplaces-demon-stylebook.git laplace-mascot`. Зайди в папку, прочитай `AGENTS.md` (раздел «Установка») и выполни его: `python tools/setup.py --serve`. Скажи, что получилось и дай ссылку на демо.

Агент сделает остальное сам: подтянет картинки из LFS, создаст `.venv`, поставит Pillow, соберёт демо и поднимет `http://localhost:8790/demo/`.

**Вариант 2: руками.**

```powershell
git lfs install
git clone https://github.com/saddysmile06-wq/Laplaces-demon-stylebook.git laplace-mascot
cd laplace-mascot
start.bat                  # Windows: двойной клик по файлу start.bat
# ./start.sh               # macOS / Linux
```

Любой способ запускает `python tools/setup.py`: проверка окружения → LFS → `.venv` → validate → build → export → демо. Только диагностика без изменений: `python tools/setup.py --check`.

> Не скачивай репозиторий ZIP-архивом: GitHub кладёт туда заглушки вместо картинок. Клонируй через `git clone`.

## Что где

| Путь | Что |
|---|---|
| [`canon/`](canon) | правда: `character.json`, `palette.json`, `poses.json` |
| [`stylebook/`](stylebook) | как выглядит и анимируется Лаплас, что можно и нельзя |
| [`assets/`](assets) | готовые арты по разделам, у каждого `index.json` с подписями |
| [`assets/clips/`](assets/clips) | анимации-клипы: `.aseprite` + спрайт-лист + превью; кадры восстанавливает `tools/export.py` |
| [`ai/`](ai) | инструкции для нейросетей: ChatGPT, Claude Code, PixelLab |
| [`pipeline/`](pipeline) | скрипты, которыми всё собрано |
| [`archive/`](archive) | старые версии и сырьё |
| [`demo/`](demo) | `index.html`, собирается автоматически |
| [`tools/`](tools) | `setup.py` (установка), `build.py`, `validate.py`, `export.py`, `sync_to_plugin.py` |

## Работа с нейросетью

- **Claude Code / Codex**: откройте репозиторий, `AGENTS.md` подхватится сам.
- **ChatGPT**: вставьте `ai/generated/chatgpt-instructions.md` в Instructions проекта и приложите референсы. Подробнее в [`ai/README.md`](ai/README.md).

## Как вносить изменения

1. Новая ветка, один PR на одну тему.
   Много кадров: новый клип в `assets/clips/<id>/`, покадровые PNG не коммитим (см. `AGENTS.md`).
2. Новый арт: файл в `assets/<раздел>/` + запись в `index.json` (`file`, `title`, `caption`).
3. `python tools/validate.py` и `python tools/build.py`, закоммитить результат.
4. Запись в `CHANGELOG.md`.
5. Канон (`canon/*`) меняем только осознанно, через обсуждение.

Имена файлов: латиница, `kebab-case`, версии суффиксом (`scene-v3.webp`).

Автокоммит: этот репозиторий живёт по отдельным правилам, агент сам коммитит и периодически пушит (`ai/workflows/autocommit.md`, `python tools/autocommit.py status`). Выключатель: файл `.autocommit-off`.

## Плагин

Плагин `laplace-demon` хранит свои копии в `public/`. Обновить их из этого репо:

```powershell
python tools/sync_to_plugin.py --plugin "<путь к плагину laplace-demon>" --dry-run
```

## Известные недочёты

- Многие скрипты в `pipeline/` читают тяжёлые покадровые наборы, которых в репозитории нет; запускаются только у автора (таблица в `pipeline/README.md`).
- Палитра извлечена из кадров автоматически; художнику стоит подтвердить.
- Расхождения по цвету волос в старом брифе: см. `stylebook/03-do-dont.md`.
