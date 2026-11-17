"""Animated scene driven by actual inference snapshots, also used to export MP4."""

import argparse
import json
import math
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .guard_rules import value
from .scenarios import ROOT, play

W, H, FPS = 1280, 720, 12
SEGMENT = 9
COLORS = {"patrol": "#67D9BC", "investigate": "#F2C66D", "chase": "#FF7389", "search": "#9FADFF"}
LABELS = {"patrol": "Патруль", "investigate": "Проверка", "chase": "Погоня", "search": "Поиск"}
ZONES = {"hall": (48, 198, 315, 505), "corridor": (326, 198, 465, 505), "storage": (476, 198, 743, 505)}
ZONE_LABELS = {"hall": "ЗАЛ", "corridor": "КОРИДОР", "storage": "СКЛАД"}


def font(size, bold=False):
    candidates = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError("Install Arial or DejaVu Sans for Cyrillic captions")


FONTS = {s: font(s) for s in (14, 16, 18, 20, 22, 26, 32)}


def text(draw, xy, content, size=18, fill="#EAF0FA"):
    draw.text(xy, str(content), font=FONTS[size], fill=fill)


def wrap(draw, xy, content, width, size=18, fill="#EAF0FA", lines=10):
    for i, line in enumerate(textwrap.wrap(str(content), width=width)[:lines]):
        text(draw, (xy[0], xy[1] + i * (size + 7)), line, size, fill)


def facts_set(raw):
    return {tuple(f) for f in raw}


def frame(data, records, seconds):
    idx = min(int(seconds // SEGMENT), len(records) - 1)
    rec = records[idx]
    local = seconds % SEGMENT
    n = len(rec["trace"])
    # First two seconds show input. Then expose real rule activations one by one.
    shown = 0 if local < 2 else min(n, int((local - 2) / 4 * n) + 1)
    raw = rec["input"] if shown == 0 else rec["trace"][shown - 1]["facts"]
    facts = facts_set(raw)
    final = local >= 6
    if final:
        facts = facts_set(rec["facts"])
    im = Image.new("RGB", (W, H), "#0B1220")
    d = ImageDraw.Draw(im)
    text(d, (38, 22), "ЛР 03  /  ЛОГИЧЕСКАЯ МОДЕЛЬ СТЕЛС-NPC", 16, "#72D7C6")
    text(d, (38, 55), data["name"], 26)
    text(d, (38, 96), "Печенов В. В.  •  ИВТ-465  •  Python / forward chaining", 16, "#98A8BE")
    d.rounded_rectangle((28, 140, 762, 665), 18, fill="#141F30")
    d.rounded_rectangle((783, 140, 1252, 665), 18, fill="#141F30")
    text(d, (48, 156), f"СЦЕНА  •  шаг {idx + 1}/{len(records)}  •  t = {rec['time']} с", 18)
    alarm = ("alarm",) in facts
    text(d, (535, 156), "ТРЕВОГА" if alarm else "Спокойно", 18, "#FF7389" if alarm else "#67D9BC")
    for zone, box in ZONES.items():
        lit = ("light_on", zone) in facts
        d.rounded_rectangle(box, 10, fill="#293B4B" if lit else "#0C1523", outline="#3C5268", width=2)
        text(d, (box[0] + 14, box[1] + 16), ZONE_LABELS[zone], 16, "#D3DFEE")
        text(d, (box[0] + 14, box[1] + 42), "свет" if lit else "темно", 14, "#F2C66D" if lit else "#8290AE")
        if ("door_opened", zone) in facts:
            text(d, (box[0] + 14, box[3] - 34), "ДВЕРЬ ОТКРЫТА", 14, "#F2C66D")
        if ("power_failed", zone) in facts:
            text(d, (box[0] + 14, box[3] - 34), "ОТКАЗ СВЕТА", 14, "#F2C66D")
    player_zone = value(facts, "at", "player", "corridor")
    pb = ZONES.get(player_zone, ZONES["corridor"])
    px, py = (pb[0] + pb[2]) / 2 + 36, 370
    d.ellipse((px - 12, py - 12, px + 12, py + 12), fill="#E6EDF7")
    text(d, (px - 25, py + 18), "Игрок", 14)
    for j, guard in enumerate(("g1", "g2")):
        zone = value(facts, "at", guard, "hall" if j == 0 else "storage")
        box = ZONES.get(zone, ZONES["hall"])
        cx, cy = (box[0] + box[2]) / 2 - 25, 340
        state = value(facts, "state", guard, "patrol")
        color = COLORS[state]
        phase = seconds * 1.4 + j * 2
        if state == "chase" and zone == player_zone:
            cx += 30 + 8 * math.sin(phase)
            cy += 12
            d.line((cx, cy, px, py), fill=color, width=2)
        else:
            cx += (28 if state == "patrol" else 42) * math.sin(phase)
            cy += 35 * math.cos(phase * 0.7)
        if ("hears", guard, "noise") in facts:
            radius = 35 + int(seconds * 12) % 30
            d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline="#F2C66D", width=2)
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=color)
        text(d, (cx - 12, cy - 11), guard.upper(), 16, "#111B2B")
        text(d, (cx - 40, cy + 23), LABELS[state], 16, color)
    for j, guard in enumerate(("g1", "g2")):
        state = value(facts, "state", guard, "patrol")
        text(d, (49 + 345 * j, 527), f"{guard.upper()}   {LABELS[state]} / {state}", 18, COLORS[state])
        memory = value(facts, "last_seen", guard)
        target = value(facts, "target", guard)
        text(d, (49 + 345 * j, 557), f"Память: {memory or 'нет'}", 16, "#9CAEC7")
        text(d, (49 + 345 * j, 583), f"Цель: {target or ('игрок' if state == 'chase' else 'зона')} ", 16, "#9CAEC7")
    text(d, (803, 158), "ОБЪЯСНЕНИЕ РЕШЕНИЯ", 18, "#72D7C6")
    wrap(d, (803, 193), rec["caption"], 42, 18, lines=3)
    text(d, (803, 290), "Факты текущего шага", 16, "#98A8BE")
    salient = [f for f in sorted(facts) if f[0] not in ("since", "time", "responded", "light_on")]
    for i, fact in enumerate(salient[:8]):
        text(d, (803, 318 + i * 22), "(" + ", ".join(map(str, fact)) + ")", 16)
    text(d, (803, 507), "Цепочка сработавших правил", 16, "#98A8BE")
    names = rec["fired"][:shown]
    wrap(d, (803, 536), " → ".join(names) if names else "Ожидание вывода" if n else "Новых правил нет", 48, 14, lines=4)
    text(
        d,
        (803, 630),
        "ПРОВЕРКА: OK" if final and rec["ok"] else "Выполнение шага…",
        16,
        "#67D9BC" if final and rec["ok"] else "#98A8BE",
    )
    progress = min(seconds / (len(records) * SEGMENT), 1)
    d.rectangle((28, 686, 28 + int(1224 * progress), 690), fill="#72D7C6")
    text(d, (38, 617), "Цвет = состояние   •   Кольцо = шум   •   Белый = игрок", 16, "#9CAEC7")
    return im


def export(path, data, records, output):
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required for video export")
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for i in range(len(records) * SEGMENT * FPS):
            proc.stdin.write(frame(data, records, i / FPS).tobytes())
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"FFmpeg failed for {path.name}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--render", action="store_true", help="Export each scenario and combined video")
    p.add_argument("--scenario", help="Scenario filename stem")
    p.add_argument("--output", type=Path, default=ROOT / "videos")
    args = p.parse_args()
    paths = sorted((ROOT / "scenarios").glob(f"{args.scenario or '*'}.json"))
    if not paths:
        p.error("No scenarios matched")
    items = [(path, json.loads(path.read_text(encoding="utf-8-sig"))) for path in paths]
    if args.render:
        args.output.mkdir(parents=True, exist_ok=True)
        chapters, elapsed = [], 0
        for path, data in items:
            records = play(data)
            if not all(r["ok"] for r in records):
                raise RuntimeError(f"Scenario failed: {path.stem}")
            export(path, data, records, args.output / f"{path.stem}.mp4")
            image_dir = ROOT / "docs" / "img"
            image_dir.mkdir(parents=True, exist_ok=True)
            frame(data, records, 7).save(image_dir / f"{path.stem}.png")
            chapters.append(
                {"id": path.stem, "name": data["name"], "start": elapsed, "duration": len(records) * SEGMENT}
            )
            elapsed += len(records) * SEGMENT
            print(f"Rendered {path.stem}", flush=True)
        playlist = args.output / "concat.txt"
        playlist.write_text("\n".join(f"file '{path.stem}.mp4'" for path, _ in items), encoding="utf-8")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(playlist),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(args.output / "lab03_demo_full.mp4"),
            ],
            check=True,
        )
        (args.output / "chapters.json").write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        import tkinter as tk

        from PIL import ImageTk

        window = tk.Tk()
        window.title("ЛР 3 — Печенов В. В. — ИВТ-465")
        label = tk.Label(window)
        label.pack()
        status = {"index": 0, "seconds": 0.0, "paused": False}
        played = [play(data) for _, data in items]

        def move(delta):
            status["index"] = (status["index"] + delta) % len(items)
            status["seconds"] = 0.0

        def pause():
            status["paused"] = not status["paused"]

        bar = tk.Frame(window)
        bar.pack()
        for title, command in [
            ("← Предыдущий сценарий", lambda: move(-1)),
            ("Пауза / продолжить", pause),
            ("Повторить", lambda: move(0)),
            ("Следующий сценарий →", lambda: move(1)),
        ]:
            tk.Button(bar, text=title, command=command).pack(side="left", padx=8, pady=8)

        def tick():
            index = status["index"]
            picture = ImageTk.PhotoImage(frame(items[index][1], played[index], status["seconds"]))
            label.configure(image=picture)
            label.image = picture
            if not status["paused"]:
                status["seconds"] += 1 / FPS
                if status["seconds"] >= len(played[index]) * SEGMENT:
                    move(1)
            window.after(1000 // FPS, tick)

        window.bind("<space>", lambda _: pause())
        window.bind("<Right>", lambda _: move(1))
        window.bind("<Left>", lambda _: move(-1))
        tick()
        window.mainloop()


if __name__ == "__main__":
    main()
