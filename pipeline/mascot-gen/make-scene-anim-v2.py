#!/usr/bin/env python3
"""Сцена v2: хвост-лента (make-tail-ribbon.py) + моргание (make-blink.py) + дыхание (make-breath.py) + свечи (make-scene-anim.py).

  python make-scene-anim-v2.py   -> out/anim/final_v2/{scene.gif, scene.webp, frames/*.png}
240 кадров по 50 мс = 12 с, бесшовный цикл. Внутри цикла:
  хвост — 6 взмахов (по 2 с), свечи — той же скорости, что в 4-секундном варианте;
  дыхание — 2 спокойных вдоха + 1 вздох с резким выдохом (последняя треть цикла);
  моргание — одно в начале цикла и одно в момент резкого выдоха.
"""
import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ribbon = load("ribbon", "make-tail-ribbon.py")
blink = load("blink", "make-blink.py")
breath = load("breath", "make-breath.py")
scene = load("scene", "make-scene-anim.py")

N = 240
BASE_N = 80  # длина цикла, под который написаны кривые свечей
BLINKS = [30, 205]  # кадры начала морганий (длятся 17 кадров)

scene.N = N
scene.FRAME_MS = 50
scene.PATCH = 60  # полосы вокруг свечей (побочный продукт) не должны превышать 16383 px по ширине в webp
scene.OUT = HERE / "out" / "anim" / "final_v2"
# свечи: частоты k считались на 80 кадров, масштабируем под 240, чтобы мерцание шло с той же скоростью
scene.wave = lambda t, k, phase: math.sin(2 * math.pi * k * (N // BASE_N) * t / N + phase)


def frames():
    out = []
    tails = ribbon.tail_frames(N, cycles=2 * (N // BASE_N))
    for t, f in enumerate(tails):
        p_blink = max(blink.blink_p(t, b) for b in BLINKS)
        f = blink.apply_blink(f, p_blink)
        out.append(breath.apply_breath(f, breath.breath_p(t, N)))
    return out


scene.load_tail = frames
scene.main()
