# Changelog

## 2026-11-24: хук Stop
- `.claude/settings.json`: Claude Code в конце ответа запускает `autocommit.py tick`; закрытый push не считается ошибкой.

## 2026-11-24: автокоммит
- `tools/autocommit.py` + `tools/autocommit.json`, правила в `ai/workflows/autocommit.md`: агент коммитит законченные куски и по таймеру, пушит пачками без force; push закрыт ключом `first_push_confirmed`.

## 2026-11-24: форма winged и установка одним кликом
- Новая форма `winged` в `canon/character.json` (крылатая pin-up, утверждённые арты Регины) + 3 позы в `poses.json`; крылья разрешены только в ней.
- `tools/setup.py`: проверка окружения, `git lfs pull`, `.venv` + Pillow, validate/build/export, `--serve`/`--open`/`--check`. `start.bat` и `start.sh` — запуск двойным кликом.
- В `README.md` готовый запрос для ИИ-агента, в `AGENTS.md` раздел «Установка» (шаги, типичные сбои).

## 2026-11-24: арты от Регины
- `assets/from-regina/`: 49 картинок из переписки 22–24.11 (фан-арты, наброски, эмблема-череп, референсы). Автор утвердил арты (флаг `approved`), референсы остались референсами.

## 2026-11-24: пути в pipeline
- Убраны абсолютные пути: `export-aseprite.lua` берёт `root` параметром, `bust_build.py` берёт `PIXEL_ART_STUDIO`, черновики `pipe*.py` ушли в `archive/`.

## 2026-11-24: клипы
- Новый формат хранения анимаций `assets/clips/<id>/` (+ `clip.json`), `tools/export.py` режет кадры из листа без Aseprite, покадровые PNG в `.gitignore`.
- Oracle v3 перенесён как первый клип; его 110 кадров восстановлены из листа и совпали с оригиналами пиксель в пиксель.

## 2026-11-24: первая сборка репозитория
- Объединены: `Code/Demoness-Artbook`, `mascot-gen` (скрипты, ref), `Code/imagemakers/pixellab-out`, `demoness-redraw`, финал Oracle v3 и раскадровка v2 из `Storyboards/demoness-oracle`.
- Добавлены `canon/palette.json` (извлечена из кадров), стайлбук, ИИ-инструкции (`AGENTS.md`, `ai/`), `tools/`, демо.
- Не перенесено: покадровые наборы 240 кадров (`mascot-gen/out/anim/*/frames`), 64 кадра `demoness-redraw/out2`, слои Oracle v3 (12 МБ), production-v1 и v2. Они остались на старых местах.
