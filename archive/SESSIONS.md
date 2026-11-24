# Чаты, где мы работали с картинками демоницы

Список собран поиском по транскриптам сессий (слова «демонеска», «mascot», «pixellab», `scene-mecha`, `final_v3`, `demoness-redraw` и другие) и по заголовкам. Содержимое каждой сессии целиком я не перечитывал: «что делали» ниже восстановлено по найденным фрагментам и по файлам, которые в ней появились. Даты — последняя активность сессии, время в UTC (локально +3 ч).

## Основные: арт создавался здесь

| Сессия | Дата | Что делали с артом |
|---|---|---|
| [Переименование проекта на Демон Лапласа](claude://claude.ai/epitaxy/local_386957ab-2580-481e-8773-c1ddac6e6788) `local_386957ab` | 7 нояб, 09:08 | Название «Демон Лапласа»; поиск референсов «chibi demon pixel art mascot» для маскота |
| [Загрузочный экран с маскотом](claude://claude.ai/epitaxy/local_f09aa1d2-3fe9-4a01-bfc9-654953b9da41) `local_f09aa1d2` | 7 нояб, 12:58 | Идея «демонеска ходит по комнате, перекладывает книги, зажигает свечи»; референсы (`sprite`, `mecha`, `room`), три формы, промпты; сборка сплэш-экрана, mecha-сцена; обсуждение способов анимации (PixelLab, ключевые позы + Aseprite) |
| [Шумы света в Demoness](claude://claude.ai/epitaxy/local_27f5eb1b-ad64-417a-8b7f-b61de36375f6) `local_27f5eb1b` | 7 нояб, 21:04 | Оживление лежачей сцены: хвост, моргание, дыхание, подъём, мерцание свечей (v1 → v3); эксперименты с `demoness.aseprite` через Aseprite MCP |
| [Claude с графическим движком](claude://claude.ai/epitaxy/local_183efe30-1d28-48e7-9d70-3ce709c4846a) `local_183efe30` | 7 нояб, 21:29 | Инструменты для пиксель-арта (Aseprite MCP, PixelLab), `demoness-redraw`, полоса «думает» (`make-thinking-strip.py`), итоги `final_v3` |
| ↳ ответвление [btw: а чего mcp не подключен?](claude://claude.ai/epitaxy/local_89c8b51c-b660-4df5-a11c-1d06096e92fb) `local_89c8b51c` | 7 нояб, 20:18 | Fork предыдущей: те же материалы, диагностика MCP |
| [Анимация генерации ответа](claude://claude.ai/epitaxy/local_e595121f-92d1-42be-8ae6-a1bee3dfcaff) `local_e595121f` | 7 нояб, 20:05 | «Думающая» демоница над полем ввода (`thinking-strip.webp`, компонент `thinking-mascot`) |
| [Поведение загрузочного экрана плагина](claude://claude.ai/epitaxy/local_7d51ce3e-84cc-46dd-aa30-472dda073e90) `local_7d51ce3e` | 7 нояб, 20:52 | Варианты сплэша (`scene-reclining.webp` / `scene-mecha.webp`), `mascot.webp` |
| [Pixellab brief review](claude://claude.ai/epitaxy/local_02ee3eb0-be0a-4081-8ecc-90aac3269264) `local_02ee3eb0` | 7–8 нояб | Эта сессия: PixelLab-позы, HD-перерисовка, шаги, пол, фон «отдаляется», сам артбук |
| [Pixellab brief review](claude://claude.ai/epitaxy/local_64903c6a-71e5-4f63-b10a-9e35bcf24452) `local_64903c6a` | 7 нояб, 22:12 | Сессия с тем же заголовком и первой репликой («прочитай pixellab-brief.md и начни»); содержимое не сверял |

## Рядом: демоница упоминается в интерфейсе, но арт не создавался

| Сессия | Где всплывает |
|---|---|
| [Prompt Laplace Demon план реализации](claude://claude.ai/epitaxy/local_756a1e52-72c3-4279-8677-e3b3582f4715) | Описание «thinking-mascot» и полосы кадров в плане реализации |
| [Интерфейс чатов с папками и сортировкой](claude://claude.ai/epitaxy/local_ae5960fb-ee14-4fd7-9e38-210799f80929) | Код `ThinkingMascot` в списке чатов |
| [Claude Agents Mode реализация](claude://claude.ai/epitaxy/local_6df1aa5c-916e-4bea-97df-bac5061c6b9e) и [ADR-025: режим агентов](claude://claude.ai/epitaxy/local_c3a19225-bfb2-4310-bdca-eea7048430d2) | Договорённость не трогать `tools/mascot-gen`; «демонеска в левой панели» при потоковом ответе |
| [Контракты структуры заметок](claude://claude.ai/epitaxy/local_a2315d97-d7f9-4b9c-9479-e30d8efe68db), [ADR-023 Focus-First Graph](claude://claude.ai/epitaxy/local_ad7daf5a-0bfe-4eec-9aeb-86dbd2cba38f) | Только упоминание `tools/mascot-gen` как «чужих» файлов в git-статусе |
| [OpenMontage для анимаций брендинга](claude://claude.ai/epitaxy/local_c96d4f0e-0601-432b-9c00-2b12da3fdc4f) | Исследование инструмента для анимации брендинга; к демонице отношения почти нет |

## Как найти ещё

В поиске по сессиям использовались слова: `демонес`, `mascot`, `pixellab`, `laplase-branding`, `Многорукая`, `final_v3`, `demoness-redraw`, `scene-mecha`. Если арт делался в сессии, где этих слов нет (например, только картинки без текста), поиск её не найдёт, дайте название — добавлю.
