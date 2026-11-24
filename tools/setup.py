#!/usr/bin/env python3
"""Установка проекта одной командой (Windows, macOS, Linux). Только стандартная библиотека.

  python tools/setup.py            # проверить окружение, довести до рабочего состояния, собрать демо
  python tools/setup.py --open     # то же + открыть демо в браузере
  python tools/setup.py --serve    # то же + поднять http://localhost:8790/demo/ (блокирует терминал, Ctrl+C остановит)
  python tools/setup.py --check    # только диагностика, ничего не менять

Что делает: проверяет Python и git, подтягивает Git LFS (картинки), создаёт .venv и ставит Pillow,
запускает validate → build → export, печатает итог. Код выхода 0 = всё готово.
"""
import argparse
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
PORT = 8790
LFS_PROBES = ["assets/scenes/splash-mascot.webp", "assets/references/ref_casual_sprite.png"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

problems: list = []


def say(ok: bool, text: str) -> None:
    print(("[ok]   " if ok else "[FAIL] ") + text)
    if not ok:
        problems.append(text)


def run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True, **kw)


def is_lfs_pointer(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(40).startswith(b"version https://git-lfs")
    except OSError:
        return False


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def lfs_install_hint() -> str:
    if os.name == "nt":
        return "winget install GitHub.GitLFS   (затем перезапусти терминал)"
    if sys.platform == "darwin":
        return "brew install git-lfs"
    return "sudo apt install git-lfs   (или dnf/pacman install git-lfs)"


def step_python() -> None:
    v = sys.version_info
    say(v >= (3, 9), f"Python {v.major}.{v.minor}.{v.micro} (нужен 3.9+)")


def step_lfs(check_only: bool) -> None:
    pointers = [p for p in LFS_PROBES if (ROOT / p).exists() and is_lfs_pointer(ROOT / p)]
    in_git = (ROOT / ".git").exists()
    if not pointers:
        say(True, "картинки на месте (не заглушки LFS)")
        return
    if not in_git:
        say(False, "картинки — заглушки Git LFS, а папка не git-репозиторий (скачан ZIP?). Клонируй: git lfs install && git clone <URL>")
        return
    if shutil.which("git") is None:
        say(False, "git не найден. Установи Git: https://git-scm.com/downloads")
        return
    if run(["git", "lfs", "version"]).returncode != 0:
        say(False, f"Git LFS не установлен. Установи: {lfs_install_hint()}")
        return
    if check_only:
        say(False, "картинки — заглушки LFS. Запусти без --check: скрипт сам выполнит git lfs pull")
        return
    print("...  скачиваю картинки из Git LFS (может занять минуту)")
    run(["git", "lfs", "install", "--local"])
    r = run(["git", "lfs", "pull"])
    still = [p for p in LFS_PROBES if (ROOT / p).exists() and is_lfs_pointer(ROOT / p)]
    say(r.returncode == 0 and not still, "git lfs pull" + ("" if r.returncode == 0 and not still else f": {r.stderr.strip()[:300] or 'файлы всё ещё заглушки'}"))


def step_venv(check_only: bool) -> Path:
    py = venv_python()
    if not py.exists():
        if check_only:
            print("[warn] .venv ещё не создан (создастся при обычном запуске)")
            return Path(sys.executable)
        print("...  создаю .venv")
        r = run([sys.executable, "-m", "venv", str(VENV)])
        if r.returncode != 0:
            say(False, f"не удалось создать .venv: {r.stderr.strip()[:300]} (на Debian/Ubuntu: sudo apt install python3-venv)")
            return Path(sys.executable)
    have = run([str(py), "-c", "import PIL"]).returncode == 0
    if not have and not check_only:
        print("...  ставлю зависимости (Pillow)")
        r = run([str(py), "-m", "pip", "install", "-q", "-r", "requirements.txt"])
        have = r.returncode == 0
        if not have:
            say(False, f"pip install не удался: {r.stderr.strip()[:300]}")
            return py
    say(have, "Pillow установлен в .venv")
    return py


def step_tools(py: Path) -> None:
    for name, args in [("validate", ["tools/validate.py"]), ("build", ["tools/build.py"]), ("export (кадры клипов)", ["tools/export.py"])]:
        r = run([str(py), *args])
        tail = (r.stdout.strip().splitlines() or [""])[-1]
        say(r.returncode == 0, f"{name}: {tail}" if r.returncode == 0 else f"{name}: {(r.stdout + r.stderr).strip()[-400:]}")


def serve() -> None:
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **k)  # noqa: E731
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as srv:
        print(f"\nДемо: http://localhost:{PORT}/demo/   (Ctrl+C — остановить)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="только диагностика")
    ap.add_argument("--open", action="store_true", help="открыть демо в браузере")
    ap.add_argument("--serve", action="store_true", help="поднять локальный сервер демо")
    a = ap.parse_args()
    print(f"Проект: {ROOT}\n")
    step_python()
    if shutil.which("git"):
        say(True, "git найден")
    else:
        print("[warn] git не найден: нужен только чтобы клонировать и обновлять репозиторий")
    step_lfs(a.check)
    if problems:
        print("\nСначала исправь пункты [FAIL] выше и запусти снова.")
        return 1
    py = step_venv(a.check)
    if not a.check and not problems:
        step_tools(py)
    demo = ROOT / "demo" / "index.html"
    say(demo.exists(), f"демо: {demo}")
    if problems:
        print("\nГотово с ошибками, см. [FAIL] выше.")
        return 1
    print("\nГОТОВО. Открыть демо: двойной клик по demo/index.html, или")
    print(f"  python tools/setup.py --serve   →  http://localhost:{PORT}/demo/")
    if a.serve:
        if a.open:
            threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}/demo/")).start()
        serve()
    elif a.open:
        webbrowser.open(demo.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
