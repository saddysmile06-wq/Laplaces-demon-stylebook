#!/usr/bin/env python3
"""Генерация артов маскота через OpenAI Images (gpt-image-1, редактирование по референсу).

Ключ: переменная окружения OPENAI_API_KEY, а если её нет, то ключ OpenAI из настроек плагина (data.json,
settings.aiProvider.apiKey, только если адрес api.openai.com). В чат и в новые файлы ключ не копируется.
  python generate.py --dry-run                 показать, что и сколько примерно стоит
  python generate.py --only emo_happy          одна запись
  python generate.py --kind emotion            все эмоции
  python generate.py --quality low --yes       всё, что ещё не сгенерировано
Результат: out/raw/<id>.png (повторный запуск пропускает готовое; --force перегенерирует).
Дальше: python postprocess.py
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "out" / "raw"
API = "https://api.openai.com/v1/images/edits"
# Ориентировочная цена за картинку, $ (проверь актуальные тарифы OpenAI): только для оценки и предохранителя
PRICE = {"low": 0.02, "medium": 0.07, "high": 0.19}


def plugin_key() -> str:
    """Ключ OpenAI из настроек плагина (data.json в корне плагина); пусто, если провайдер не OpenAI."""
    try:
        ai = json.loads((HERE.parent.parent / "data.json").read_text(encoding="utf8"))["settings"]["aiProvider"]
    except Exception:
        return ""
    return ai.get("apiKey", "") if "api.openai.com" in ai.get("baseUrl", "") else ""


def multipart(fields: dict, files: list) -> tuple:
    boundary = uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, p in files:
        ctype = mimetypes.guess_type(p.name)[0] or "image/png"
        head = f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{p.name}"\r\nContent-Type: {ctype}\r\n\r\n'
        out.append(head.encode() + p.read_bytes() + b"\r\n")
    out.append(f"--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def form_of(bible: dict, item: dict) -> dict:
    return bible["forms"][item.get("form", "casual")]


def build_prompt(bible: dict, item: dict) -> str:
    if item["kind"] == "scene":
        return f'{bible["style"]} {item["prompt"]}'
    f = form_of(bible, item)
    return f'{bible["style"]} {bible["core"]} {f["outfit"]} {f["framing"]} {bible["rules"]} {item["prompt"]}'


def ref_for(bible: dict, item: dict) -> Path:
    """Референс: у сцены room.png (или scene_mecha.png для меха), у персонажа файл его формы (запасной, если своего ещё нет)."""
    ref = HERE / "ref"
    if item["kind"] == "scene":
        return ref / ("scene_mecha.png" if item.get("form") == "mecha" else "room.png")
    f = form_of(bible, item)
    main = ref / f["ref"]
    return main if main.exists() else ref / f.get("ref_fallback", "sprite.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gpt-image-1.5", help="модель изображений; список доступных ключу: --list-models")
    ap.add_argument("--list-models", action="store_true", help="показать модели картинок, доступные ключу, и выйти")
    ap.add_argument("--only", action="append", help="id записи (можно несколько раз)")
    ap.add_argument("--kind", choices=["emotion", "pose", "scene"])
    ap.add_argument("--quality", choices=list(PRICE), default="medium")
    ap.add_argument("--size", default="1024x1024", help="1024x1024 | 1536x1024 | 1024x1536 (сцена всегда 1536x1024)")
    ap.add_argument("--max-usd", type=float, default=1.0, help="предохранитель: оценка выше — без --yes не запускать")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.list_models:
        key = os.environ.get("OPENAI_API_KEY") or plugin_key()
        if not key:
            sys.exit("нет ключа")
        req = urllib.request.Request("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                ids = sorted(m["id"] for m in json.load(r)["data"])
        except urllib.error.HTTPError as e:
            sys.exit(f"HTTP {e.code}: {e.read().decode('utf8', 'replace')[:300]}")
        print("модели картинок:", [i for i in ids if "image" in i or "dall" in i] or "нет доступных")
        return

    bible = json.loads((HERE / "character.json").read_text(encoding="utf8"))
    items = json.loads((HERE / "poses.json").read_text(encoding="utf8"))["items"]
    items = [i for i in items if (not args.only or i["id"] in args.only) and (not args.kind or i["kind"] == args.kind)]
    RAW.mkdir(parents=True, exist_ok=True)
    todo = [i for i in items if args.force or not (RAW / f'{i["id"]}.png').exists()]
    est = len(todo) * PRICE[args.quality]
    print(f"к генерации: {len(todo)} из {len(items)} (качество {args.quality}), оценка ~ ${est:.2f}")
    for i in todo:
        print(f'  - {i["id"]} ({i.get("form", "casual")}, {i["kind"]})')
    if args.dry_run or not todo:
        return
    if est > args.max_usd and not args.yes:
        sys.exit(f"оценка ${est:.2f} больше --max-usd {args.max_usd}: добавь --yes или сузь выбор (--only / --kind)")
    key = os.environ.get("OPENAI_API_KEY") or plugin_key()
    if not key:
        sys.exit("нет ключа: задай OPENAI_API_KEY или укажи ключ OpenAI в настройках плагина")

    for it in todo:
        scene = it["kind"] == "scene"
        refs = [ref_for(bible, it)]
        fields = {
            "model": args.model,
            "prompt": build_prompt(bible, it),
            "size": "1536x1024" if scene else args.size,
            "quality": args.quality,
            "n": "1",
            "output_format": "png",
        }
        if not scene:
            fields["background"] = "transparent"
        body, ctype = multipart(fields, [("image[]", p) for p in refs])
        req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": ctype})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.load(r)
            (RAW / f'{it["id"]}.png').write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
            print(f'ok   {it["id"]}')
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf8", "replace")
            try:
                msg = json.loads(msg)["error"]["message"]
            except Exception:
                pass
            print(f'FAIL {it["id"]}: HTTP {e.code} {msg}')
        except Exception as e:  # сеть и т.п.: идём дальше, готовое не пропадает
            print(f'FAIL {it["id"]}: {e}')


if __name__ == "__main__":
    main()
