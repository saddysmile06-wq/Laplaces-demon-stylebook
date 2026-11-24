# Воркфлоу: сгенерировать картинку (поза, эмоция, сцена)

Для браузерного ChatGPT или любого генератора картинок.

1. **Выбери форму** (casual / mecha / demon) и тип: эмоция, поза или сцена. Готовые поза/эмоция уже есть в `canon/poses.json` (id вида `emo_happy`, `pose_walk_contact`, `mecha_read`). Нужной нет — допиши свою запись.
2. **Собери промпт.** Формула: `STYLE + CORE + outfit и framing формы + RULES + поза`. Блоки берутся из `canon/character.json` дословно. Быстрее всего: `demo/index.html` → «Конструктор промптов» → скопировать.
3. **Референс.** Прикрепи изображение формы: casual → `assets/references/ref_casual_sprite.png`, mecha → `ref_mecha.png`, demon → `assets/originals/archivist-among-books.png`. Для сцен ещё `assets/scenes/splash-mascot.webp`.
4. **Фон.** Браузерный ChatGPT не гарантирует прозрачность. Проси «solid dark background» и вырезай потом.
5. **Постобработка.** `pipeline/mascot-gen/postprocess.py`: приводит к чистой пиксельной сетке и палитре (проверь пути в начале файла).
6. **Проверка.** `ai/qa-checklist.md`. Сырьё идёт в `archive/`, принятое в `assets/<раздел>/` + запись в `index.json`.

## Если модель «уплывает»
- Лицо другое: прикрепи крупное лицо `assets/references/ref_face.png` и напиши «keep face identical to the second reference».
- Размытые пиксели: добавь «hard-edged pixels, no anti-aliasing, no blur».
- Лишние рога или руки: повтори «TWO horns, no extra limbs» в конце промпта.
- Пиксель разного размера в наборе: генерируй серию в одном чате, каждый следующий кадр с предыдущим как style-референсом.
