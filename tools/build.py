#!/usr/bin/env python3
"""Сборка производных файлов из canon/ и assets/:

  demo/index.html                       галерея + формы + палитра + конструктор промптов (данные вшиты, без сервера)
  ai/generated/chatgpt-instructions.md  инструкция для ChatGPT-проекта из ai/templates/system-prompt.tmpl.md

  python tools/build.py
"""
import json

from common import CANON, ROOT, load_clips, load_collections, read_json

CHATGPT_LIMIT = 8000


def forms_text(ch: dict) -> str:
    out = []
    for fid, f in ch["forms"].items():
        out.append(f"## {fid}: {f['label']}\n- Референс: {f['ref']}" + (f" (запасной: {f['ref_fallback']})" if f.get("ref_fallback") else "") +
                   f"\n- Кадр: {f['framing']}\n- Одежда: {f['outfit']}\n- Использование: {f['use']}")
    return "\n\n".join(out)


def palette_text(pal: dict) -> str:
    return "\n".join(f"- {c['hex']} {c['id']}: {c['role']}" for c in pal["colors"])


def build_instructions(ch: dict, pal: dict) -> str:
    tmpl = (ROOT / "ai" / "templates" / "system-prompt.tmpl.md").read_text(encoding="utf-8")
    text = (tmpl.replace("{{CORE}}", ch["core"]).replace("{{STYLE}}", ch["style"]).replace("{{RULES}}", ch["rules"])
            .replace("{{FORMS}}", forms_text(ch)).replace("{{PALETTE}}", palette_text(pal)).replace("{{MAX_COLORS}}", str(pal.get("max_colors", 20))))
    header = "<!-- Файл сгенерирован: python tools/build.py. Не править руками, меняй canon/ или ai/templates/system-prompt.tmpl.md -->\n\n"
    return header + text


def main() -> None:
    ch, pal, poses = read_json(CANON / "character.json"), read_json(CANON / "palette.json"), read_json(CANON / "poses.json")
    colls = [{"slug": s, "title": d["title"], "intro": d["intro"], "items": d["items"]} for s, d in load_collections()]
    clips = load_clips()
    if clips:
        colls.insert(0, {"slug": "clips", "title": "Анимации-клипы", "intro": "Готовые анимации: исходник .aseprite, спрайт-лист и превью. Покадровые PNG не хранятся, их восстанавливает tools/export.py.",
                         "items": [{"file": f"{c['id']}/{c['preview']}", "title": c["title"],
                                    "caption": f"{c['caption']} [{c['frames']} кадр., {c['size'][0]}×{c['size'][1]}, форма {c['form']}, {c['status']}]"} for c in clips]})

    gen = ROOT / "ai" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    instr = build_instructions(ch, pal)
    (gen / "chatgpt-instructions.md").write_text(instr, encoding="utf-8")
    if len(instr) > CHATGPT_LIMIT:
        print(f"! chatgpt-instructions.md: {len(instr)} символов, лимит ChatGPT ~{CHATGPT_LIMIT}. Сократи шаблон или канон.")
    else:
        print(f"chatgpt-instructions.md: {len(instr)} символов (лимит ~{CHATGPT_LIMIT})")

    data = {"character": ch, "palette": pal, "poses": poses["items"], "collections": colls}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (ROOT / "tools" / "demo.tmpl.html").read_text(encoding="utf-8").replace("/*DATA*/", blob)
    (ROOT / "demo").mkdir(exist_ok=True)
    (ROOT / "demo" / "index.html").write_text(html, encoding="utf-8")
    n = sum(len(c["items"]) for c in colls)
    print(f"demo/index.html: {len(colls)} разделов, {n} карточек")


if __name__ == "__main__":
    main()
