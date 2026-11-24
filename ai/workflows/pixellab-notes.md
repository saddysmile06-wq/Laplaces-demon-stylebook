# PixelLab: как мы получили позы (промпты, размеры, грабли)

Инструмент: `create_image_pro_flash` (MCP PixelLab). Сохранить стиль и палитру помогает **style-референс**: предыдущий кадр или кроп сцены. Для всех кадров: `no_background=true`, `max_colors=20`, `seed=7`.

## Расход

| Токен | Что сделано | Генераций |
|---|---|---|
| 1-й (триал, 40) | 6 поз 128×128 (подъём … села) | 36 (+ 4 осталось) |
| 2-й (триал, 40) | 3 HD-кадра (поза 2, 3, 4) + «шаг вперёд» + «шаг назад» на холсте 160×208 | 30 (+ 10 осталось) |

Цена кадра зависит от длинной стороны холста: до 96 px — 5, 100–208 px — 6, 212–256 — 9. Отклонённые фильтром запросы не списываются.

## Первый заход: 6 поз 128×128

**Референс (style):** кроп лежачей сцены (`07_PixelLab/raw/ref_f00_x4down.png`, 94×72). Цепочка якорей (style-референс каждого кадра): поза 1 ← кроп сцены; поза 2 ← поза 1; поза 3 ← поза 2; поза 4 ← поза 3; поза 5 ← поза 2; поза 6 ← поза 1.

Общая часть промпта (для кадров 2–6 после первого):

> Same fantasy demon girl character as in the style image, identical face, long dark purple hair with side-swept bangs, two small curved horns, long pointed ears, thin arrowhead tail, same dark violet casual top and shorts with a strap. [ПОЗА] Same pixel density, same cool purple palette, hard pixels, no gradients, transparent background.

Позы:

| № | Фрагмент про позу |
|---|---|
| 1 | «she has just started to get up from lying on her side — sitting up on the floor, torso lifted, propping herself on one straightened arm, the other hand on her knee, legs folded to the side, sleepy calm expression. Side three-quarter view» |
| 2 | «she stands up straight, calm and relaxed, arms hanging down at her sides, head slightly tilted, tail swaying behind her. Front three-quarter view» |
| 3 | «standing and stretching after a nap, both arms raised straight up over her head with hands together, yawning with eyes closed. Front view» |
| 4 | «just finished stretching, she is lowering her arms, both arms halfway down at shoulder height, elbows bent, relaxed, eyes half open and sleepy» |
| 5 | «she is starting to sit down on the floor, knees bent, lowering herself into a crouch, one hand reaching down to touch the floor, the other arm relaxed. Side three-quarter view» |
| 6 | «she has just sat down on the floor, sitting upright with legs folded to one side, both hands resting on her lap, back straight, calm sleepy expression, tail curled on the floor beside her. Side three-quarter view» |

## Второй заход: HD-кадры 160×208 и шаги

Зачем: в позах 2–4 фигура стоя целиком помещалась в 128 px, голова была ~26 px, лицо получалось мутным; рядом сидячие кадры имели детальное лицо. На холсте 160×208 голова ~40 px, лицо чёткое.

Дополнительная фраза: «Keep the same high level of detail in the head and face as in the style image.» Style-референс для первого HD-кадра — поза 6 (самое детальное лицо); дальше — сам HD-кадр.

| Кадр | Фрагмент про позу | Якорь |
|---|---|---|
| Поза 2 «встала» | «standing up straight, calm and sleepy, arms hanging down at her sides, head slightly tilted. Front view, entire figure visible with margin, feet on one ground line near the bottom» | поза 6 |
| Поза 3 «потягивается» | «standing and stretching after a nap, both arms raised straight up over her head with hands together, yawning with eyes closed. Front view, entire figure visible including raised hands, with margin above and below» | HD поза 2 |
| Поза 4 «опускает руки» | «just finished stretching, she is lowering her arms, both arms halfway down at shoulder height with elbows bent, hands relaxed, eyes half open and sleepy» | HD поза 2 |
| Шаг вперёд | «walking toward the viewer, taking one step forward, one foot placed ahead of the other, body leaning slightly forward, arms swinging gently at her sides, calm sleepy expression» | HD поза 2 |
| Шаг назад | «taking a small step backward, one foot placed behind the other, knees slightly bent, body lowering a little, arms hanging loosely at her sides, calm sleepy expression» | HD поза 2 |

Второй шаг вперёд — это **зеркальная копия** кадра «шаг вперёд» (без генерации).

## Что фильтр блокирует (и чем заменять)

PixelLab отклоняет запросы без объяснения, и срабатывает нестабильно: описание позы 1 с «dark violet bikini top … barefoot» прошло, а позы 2 с теми же словами — нет. Блокировались запросы со словами про тело, кожу и «подробное лицо»: «bikini», «barefoot», «highly detailed face … nose and lips», «back slightly arched, chest forward», «on tiptoe», «open hands». Рабочие замены: «casual top and shorts», «feet», «same high level of detail in the head», «arms hanging down». Если запрос отклонён, переформулировать нейтральнее; списание не происходит.

## После генерации (локально, `scripts/`)

1. `finalize_poses.py` — общая 20-цветная палитра по всем кадрам (median cut, без дизеринга) → `final/poseN.png`.
2. `clean_poses.py` — удаляет мелкие отлетевшие острова (значки зевка), одиночные «колючки» на силуэте и светлые «пылинки» в волосах (пиксель светлее всех соседей), проверяет, что поза осталась одним островком (хвост цел).
3. `build_scene.py` — вписывает позы в лежачую сцену (базой служат кадры `mascot-gen/out/anim/final_v2/frames`):
   - масштабы по позам: лёжа 3,5; HD-стоя 2,35–2,7; присела 3,65;
   - фон «отдаляется» при шагах (зум ×1,0 → 0,9 → 0,82 → 0,78) и возвращается на шаге назад;
   - пол: плиты в перспективе, блики свечей, контактная тень, отражение ступней;
   - между позами смазанный кадр, искры при потягивании; цикл 240 кадров по 50 мс, бесшовный.
