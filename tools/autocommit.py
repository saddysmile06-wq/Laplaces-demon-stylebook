#!/usr/bin/env python3
"""Безопасный автокоммит и лёгкий push. Правила: ai/workflows/autocommit.md, настройки: tools/autocommit.json.

  python tools/autocommit.py status                 # что произойдёт сейчас, ничего не меняет
  python tools/autocommit.py commit -m "art(clips): добавил idle" [--agent "Claude"]
  python tools/autocommit.py push                   # push, если пришло время (или --now)
  python tools/autocommit.py tick [-m "..."]        # одним вызовом: commit по таймеру + push по таймеру

Никогда не делает force-push, reset, rebase чужих коммитов, не меняет ветку и не обходит проверки.
Код выхода 0 = всё в порядке или делать нечего; 1 = остановился по правилу (причина в тексте).
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "tools" / "autocommit.json").read_text(encoding="utf-8"))
SECRETS = re.compile(r"(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{32,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{12,})", re.I)
TYPES = "art anim canon style ai tools docs chore fix"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def git(*a, check=False):
    r = subprocess.run(["git", *a], cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(a)}: {r.stderr.strip()[:400]}")
    return r


def out(*a) -> str:
    return git(*a).stdout.strip()


def stop(msg: str) -> int:
    print("СТОП:", msg)
    return 1


def preflight(for_push=False):
    """Возвращает текст причины остановки или None."""
    if not CFG["enabled"] or (ROOT / ".autocommit-off").exists():
        return "автокоммит выключен (enabled=false или файл .autocommit-off)"
    if not (ROOT / ".git").exists():
        return "это не git-репозиторий"
    if out("symbolic-ref", "--short", "HEAD") != CFG["branch"]:
        return f"текущая ветка не «{CFG['branch']}»: автокоммит работает только там"
    gd = ROOT / ".git"
    if any((gd / n).exists() for n in ("MERGE_HEAD", "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD")):
        return "идёт merge/rebase/cherry-pick: разберись вручную"
    if for_push:
        if not CFG["first_push_confirmed"]:
            return "push запрещён: first_push_confirmed=false в tools/autocommit.json (автор ещё не разрешил публиковать)"
        if git("remote", "get-url", CFG["remote"]).returncode != 0:
            return f"нет remote «{CFG['remote']}»: добавь git remote add {CFG['remote']} <URL>"
    return None


def changed_files():
    return [l[3:].strip('"') for l in out("status", "--porcelain", "-uall").splitlines() if l.strip()]


def minutes_since(ts: str) -> float:
    return (time.time() - int(ts)) / 60 if ts else 1e9


def last_commit_age() -> float:
    return minutes_since(out("log", "-1", "--format=%ct"))


def ahead_behind():
    r = git("rev-list", "--left-right", "--count", f"HEAD...{CFG['remote']}/{CFG['branch']}")
    if r.returncode != 0:
        return len(out("rev-list", "HEAD").splitlines()), 0, True  # upstream ещё нет
    a, b = r.stdout.split()
    return int(a), int(b), False


def last_push_age(no_upstream: bool) -> float:
    if no_upstream:
        return 1e9
    return minutes_since(out("log", "-1", "--format=%ct", f"{CFG['remote']}/{CFG['branch']}"))


def do_commit(msg: str, agent: str) -> int:
    why = preflight()
    if why:
        return stop(why)
    files = changed_files()
    if not files:
        print("нечего коммитить")
        return 0
    bad = [f for f in files if any(b in f.replace("\\", "/") for b in CFG["blocked_paths"])]
    if bad:
        return stop("в изменениях запрещённые пути (добавь в .gitignore или убери): " + ", ".join(bad[:5]))
    big = [f for f in files if (ROOT / f).is_file() and (ROOT / f).stat().st_size > CFG["max_file_mb"] * 1048576]
    if big:
        return stop(f"файлы больше {CFG['max_file_mb']} МБ, спроси автора: " + ", ".join(big[:5]))
    m = re.match(rf"^({TYPES.replace(' ', '|')})(\([\w\-./]+\))?: .{{5,}}", msg)
    if not m:
        return stop(f"сообщение должно быть «тип(область): описание», типы: {TYPES}")
    has_commits = bool(out("rev-list", "-n1", "HEAD"))
    if has_commits and any(f.startswith("canon/") for f in files) and not msg.startswith("canon"):
        return stop("в изменениях есть canon/: коммить их отдельным коммитом canon(...): ... (и только если автор это просил)")
    # производные файлы и проверка
    for tool in ("validate.py", "build.py"):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / tool)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            return stop(f"{tool} упал:\n{(r.stdout + r.stderr)[-500:]}")
    git("add", "-A", check=True)
    diff = git("diff", "--cached", "-U0", "--no-color").stdout
    hit = SECRETS.search("\n".join(l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")))
    if hit:
        git("reset", "-q")
        return stop(f"похоже на секрет в изменениях («{hit.group(0)[:20]}…»): ничего не закоммичено, проверь файлы")
    trailer = f"\n\nCo-Authored-By: {agent} <noreply@anthropic.com>" if agent else ""
    git("commit", "-q", "-m", msg + trailer, check=True)
    print("коммит:", out("log", "-1", "--format=%h %s"), f"({len(files)} файлов)")
    return 0


def do_push(now: bool) -> int:
    why = preflight(for_push=True)
    if why:
        return stop(why)
    a, b, no_up = ahead_behind() if git("rev-parse", f"{CFG['remote']}/{CFG['branch']}").returncode == 0 else (len(out("rev-list", "HEAD").splitlines()), 0, True)
    if a == 0 and not no_up:
        print("пушить нечего")
        return 0
    due = now or a >= CFG["push_min_commits"] or last_push_age(no_up) >= CFG["push_every_min"]
    if not due:
        print(f"рано: {a} коммит(ов) не отправлено, лимиты: {CFG['push_min_commits']} коммитов или {CFG['push_every_min']} мин")
        return 0
    if changed_files():
        print("предупреждение: есть незакоммиченные изменения, они в push не попадут")
    if not no_up:
        r = git("pull", "--rebase", "--autostash", CFG["remote"], CFG["branch"])
        if r.returncode != 0:
            git("rebase", "--abort")
            return stop("pull --rebase не удался (конфликт?). Ничего не отправлено, разберись вручную:\n" + r.stderr.strip()[-300:])
    r = git("push", CFG["remote"], f"HEAD:{CFG['branch']}", *([] if not no_up else ["--set-upstream"]))
    if r.returncode != 0:
        return stop("push не прошёл (без force): " + (r.stderr or r.stdout).strip()[-400:])
    print(f"push: отправлено {a} коммит(ов) в {CFG['remote']}/{CFG['branch']}")
    return 0


def status() -> int:
    why = preflight()
    print("ветка:", out("symbolic-ref", "--short", "HEAD"), "| изменено файлов:", len(changed_files()))
    print("последний коммит:", f"{last_commit_age():.0f} мин назад" if out("rev-list", "-n1", "HEAD") else "коммитов нет")
    print("коммит по таймеру:", "ДА" if changed_files() and last_commit_age() >= CFG["commit_every_min"] else "нет")
    p = preflight(for_push=True)
    print("push:", f"запрещён ({p})" if p else "разрешён")
    if why:
        print("СТОП:", why)
    return 0


def auto_message(files) -> str:
    tops = sorted({f.replace("\\", "/").split("/")[0] for f in files})
    kind = {"assets": "art", "canon": "canon", "stylebook": "style", "ai": "ai", "tools": "tools", "pipeline": "tools"}.get(tops[0], "chore")
    return f"{kind}({'+'.join(tops[:3])}): автокоммит, {len(files)} файлов"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "commit", "push", "tick"])
    ap.add_argument("-m", "--message")
    ap.add_argument("--agent", default="Claude")
    ap.add_argument("--now", action="store_true", help="push без ожидания таймеров")
    a = ap.parse_args()
    if a.cmd == "status":
        return status()
    if a.cmd == "commit":
        if not a.message:
            return stop("нужен -m \"тип(область): описание\"")
        return do_commit(a.message, a.agent)
    if a.cmd == "push":
        return do_push(a.now)
    # tick
    files = changed_files()
    rc = 0
    if files and (a.message or last_commit_age() >= CFG["commit_every_min"]):
        rc = do_commit(a.message or auto_message(files), a.agent)
    elif files:
        print(f"коммит рано: последний {last_commit_age():.0f} мин назад, интервал {CFG['commit_every_min']}")
    if rc:
        return rc
    closed = preflight(for_push=True)
    if closed and ("first_push" in closed or "нет remote" in closed):
        print("push пропущен:", closed)  # это не ошибка: автор ещё не открыл push
        return 0
    return do_push(a.now)


if __name__ == "__main__":
    sys.exit(main())
