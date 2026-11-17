"""Create a measured chart, five-page report and actual bot-path animation."""

import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

import imageio_ffmpeg
import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as PDFImage
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from aiunder import bsp
from aiunder.validator import pick_start, reachable
from bot.player_bot import run_bot

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FONTDIR = Path(os.environ.get("LAB_FONT_DIR", "C:/Windows/Fonts"))
REPO = "https://github.com/VladimirPechenov/lab08-ai-testing"


def font(size):
    return ImageFont.truetype(str(FONTDIR / "arial.ttf"), size)


def level_frame(seed, progress):
    grid = bsp.generate(seed=seed)
    start = pick_start(grid)
    _, info = reachable(grid, start)
    goal = info["finish"]
    dist, _ = reachable(grid, goal)
    bot = run_bot(grid, dist, start, goal, epsilon=0, seed=seed)
    im = Image.new("RGB", (1280, 800), "#f2f6fa")
    draw = ImageDraw.Draw(im)
    draw.text((30, 20), "ЛР 8 · Тестирование игрового ИИ автоботом", font=font(32), fill="#17304a")
    draw.text((30, 70), f"BSP 64×48 · seed {seed} · жадный бот · реальные перемещения", font=font(23), fill="#17304a")
    scale, ox, oy = 12, 30, 125
    for y, x in np.ndindex(grid.shape):
        draw.rectangle(
            (ox + x * scale, oy + y * scale, ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1),
            fill="#17304a" if grid[y, x] else "#e0e8ec",
        )
    count = max(1, round(1 + progress * (len(bot.path) - 1)))
    points = [(ox + x * scale + 6, oy + y * scale + 6) for y, x in bot.path]
    if count > 1:
        draw.line(points[:count], fill="#138d96", width=4)
    for p, color in ((points[0], "#17a05e"), (points[-1], "#e04c5c"), (points[count - 1], "#f1b530")):
        x, y = p
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
    lines = [
        f"Ход: {count - 1} / {bot.steps}",
        f"Достигнут финиш: {count == len(bot.path)}",
        "Стены: тёмные",
        "Путь: бирюзовый",
        "Бот: жёлтый",
        "Старт: зелёный",
        "Финиш: красный",
        "",
        "BFS от финиша",
        "4 соседа",
        "epsilon = 0",
        "",
        "Печенов В. В.",
        "ИВТ-465",
    ]
    for i, line in enumerate(lines):
        draw.text((840, 130 + i * 35), line, font=font(23), fill="#17304a")
    draw.text(
        (30, 745),
        "Видеовизуализация сохранённого пути бота; не запись экрана редактора.",
        font=font(22),
        fill="#17304a",
    )
    return im


def main():
    summary = json.loads((ROOT / "results/summary.json").read_text())
    perf = json.loads((ROOT / "results/performance.json").read_text())
    names = list(summary)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    for ax, key, label in zip(
        axes,
        ("successes", "steps", "coverage"),
        ("Goals reached / 100", "Mean moves (all runs)", "Mean floor coverage"),
        strict=True,
    ):
        ax.bar(names, [summary[n][key] for n in names], color=["#178f97", "#4174b2", "#db9151"])
        ax.set_title(label)
    fig.tight_layout()
    fig.savefig(ROOT / "results/comparison.png", dpi=180)
    plt.close(fig)
    level_frame(0, 1).save(ROOT / "docs/img/bot_seed0.png")
    pages = [
        (
            "Лабораторная работа № 8",
            [
                "Тестирование игрового ИИ автоботом",
                "Дисциплина: Игровой искусственный интеллект. Студент: Печенов В. В. Группа: ИВТ-465. Стек: Python, pytest, GitHub Actions. Дата: 17.11.2026.",
                "1. Цель работы",
                "Построить воспроизводимую автоматическую проверку поведения игрового ИИ, проходимости процедурных карт и временных бюджетов. Обнаружить реальные дефекты автобота и защитить исправления регрессионными тестами.",
                "2. Постановка задачи",
                "Реализовать не менее 10 unit-тестов FSM/восприятия; запустить бота с метриками; проверить 100 seed; задать performance-пороги; настроить CI; оформить журнал минимум двух багов, видео, историю этапов и Release v1.0.",
                "Источник задания - README и docs/report.md шаблона преподавателя. Отдельные методические указания, кафедральный титульный лист и ФИО преподавателя не предоставлены. Настоящий отчёт следует опубликованным разделам и объёму 4-6 страниц; соответствие неизвестному макету не заявляется.",
            ],
        ),
        (
            "3. Описание реализации",
            [
                "Компоненты и происхождение",
                "В src/aiunder перенесены BSP и BFS-валидатор из собственной ЛР 7. Пакет rules из ЛР 3 проверяет восприятие света/темноты, приоритет обнаружения над шумом и передачу тревоги второму стражу. Новая компактная GuardFSM задаёт Patrol, Alert, Chase, Attack и Search.",
                "Переходы: Patrol + see_player/hear_noise -> Alert; Alert + confirm -> Chase; Chase + in_range -> Attack; Attack + out_of_range -> Chase; lost -> Search; Search + see_player -> Chase; timeout -> Patrol. Таймер поиска сбрасывается при переходе. Обнаружение цели имеет приоритет над таймаутом.",
                "Автобот и контракт метрик",
                "BFS строит карту расстояний от финиша. Жадный ход выбирает минимум среди четырёх соседей-полов. С вероятностью epsilon ход случайный. RNG локальный, seed воспроизводим. Бот проверяет границы, стены и входные параметры; старт и финиш используют координаты (строка, столбец).",
                "steps - число выполненных перемещений; reached_goal - достижение цели, включая старт в ней; visited и path включают старт и конечную позицию. stuck_events - тупик без допустимых соседей либо шаг без уменьшения BFS-дистанции. Для случайной политики это показатель непрогресса, а не доказательство геометрического застревания.",
                "Жадный бот располагает полной картой. Он служит тестовым оракулом навигации, а не обученным агентом. Построение BFS и отрисовка не входят в время генерации или тика FSM.",
            ],
        ),
        (
            "4. Демонстрация и обнаруженные баги",
            [
                "На рисунке показан фактический путь бота на BSP seed=0: старт зелёный, цель красная, путь бирюзовый. Видео последовательно визуализирует 10 уровней seed=0..9 и показывает итоговый экран измерений.",
                "Баг 1: на сетке 1×2 при max_steps=1 бот из шаблона попадал в цель последним ходом, но возвращал reached_goal=False и не добавлял цель в visited. Проверка цели стояла только до перемещения.",
                "Баг 2: на сетке 1×1 при start=goal и max_steps=0 исходный бот сообщал неуспех и пустое visited. При ненулевом лимите считался лишний шаг. Исправлена начальная инициализация, счётчик теперь отражает перемещения.",
                "Оба теста реально падали до исправления: results/regressions-before.txt, коммит 58ae472. Исправление 36412ca. Результаты не являются искусственной инъекцией ошибок. Журнал и точные шаги воспроизведения находятся в docs/bugs.md.",
            ],
        ),
        (
            "5. Метрики и результаты",
            [
                "Протокол: BSP 64×48, min_leaf=10, depth=5, все seed=0..99 без отбора. Для каждой карты старт - первая клетка пола по строкам, финиш - самая дальняя достижимая. Дополнительно требуется доступность 100% пола: выбор достижимого финиша сам по себе не доказывает связность.",
                "100 отдельных solvability-тестов проверяют полную связность, исходный is_playable (доля >=0.6, путь >=20), воспроизводимость карты, легальность каждого хода и достижение цели ровно за BFS-длину. Unit-каталог содержит 17 проверок переходов, таймера и восприятия. Всего локально: 127 passed, 0 skipped.",
                *[
                    f"{n}: успех {summary[n]['successes']}/100; средние ходы {summary[n]['steps']:.2f}; события непрогресса {summary[n]['stuck_events']:.2f}; покрытие пола {summary[n]['coverage']:.2%}."
                    for n in names
                ],
                "Эксперимент содержит 300 запусков: epsilon=0, 0.1, 1; max_steps=2000. Средние учитывают все запуски, в том числе неуспешные. random не решил уровни в данном бюджете, что не означает абсолютную невозможность случайного прохождения. CSV и JSON сохраняются в results/.",
            ],
        ),
        (
            "5. Производительность и CI",
            [
                f"Генерация, 100 измерений после одного прогрева: p95={perf['generation']['p95_ms']:.4f} мс; максимум={perf['generation']['max_ms']:.4f} мс. Тик одного FSM, 1000 измерений Search->Chase: p95={perf['ai_tick']['p95_ms']:.6f} мс. Таймер perf_counter_ns; p95 - nearest rank ceil(0.95*n). Среда сохранена в environment.json.",
                "Пороги p95: генерация <50 мс; тик одного NPC <1 мс. При 60 FPS кадр занимает около 16.67 мс: 1 мс - целевой бюджет простого NPC. Генерация 50 мс допускается в загрузке уровня, не в каждом кадре. Это пороги регрессии, не гарантия realtime. Микрозамеры зависят от ОС и нагрузки, включают накладные расходы таймера; тест не моделирует тысячи NPC.",
                "GitHub Actions на Python 3.11/3.12 выполняет установку, ruff, полный pytest с JUnit и durations, затем 300 запусков бота. Результаты публикуются отдельными артефактами для каждой версии. Ни importorskip, ни пропуски ключевых проверок не используются.",
                "6. Выводы",
                "Проверены состояния и приоритеты ИИ, найдены и исправлены два дефекта учёта цели. Полностью связные BSP-карты решены жадным ботом на всех 100 seed. Epsilon-политика требует больше ходов, случайная не достигает цели в данном бюджете. Ограничения: один размер и генератор, доступ бота к полной карте, абстрактное восприятие зон вместо геометрических лучей, короткий FSM-тик вместо полного кадра движка.",
                "7. Список литературы",
                "1. kolesnikov-vstu-gameai/lab08-ai-testing: README, docs/report.md, исходный player_bot.py (ветка Master). 2. Собственные ЛР 3 и ЛР 7: rules/engine.py, guard_rules.py, bsp.py, validator.py. 3. Документация pytest: https://docs.pytest.org/ . 4. GitHub Actions: https://docs.github.com/actions .",
                "Приложение. Репозиторий",
                REPO,
                "Видео и Release v1.0 доступны по ссылкам в README. Исходники генерации графика, PDF и видео: tools/build_artifacts.py. Для воспроизведения сначала выполните pytest, затем python -m bot.experiment.",
            ],
        ),
    ]
    pdfmetrics.registerFont(TTFont("ArialLab", str(FONTDIR / "arial.ttf")))
    body = ParagraphStyle("body", fontName="ArialLab", fontSize=10.5, leading=15, spaceAfter=11)
    title = ParagraphStyle("title", parent=body, fontSize=18, leading=24, spaceAfter=20)
    story, markdown = [], []
    for i, (heading, paras) in enumerate(pages):
        if i:
            story.append(PageBreak())
        story.append(Paragraph(escape(heading), title))
        markdown.append("## " + heading + "\n")
        for p in paras:
            story.append(Paragraph(escape(p), body))
            markdown.append(p + "\n")
        if i == 2:
            story.append(Spacer(1, 5 * mm))
            story.append(PDFImage(str(ROOT / "docs/img/bot_seed0.png"), width=166 * mm, height=104 * mm))
        if i == 3:
            story.append(PDFImage(str(ROOT / "results/comparison.png"), width=170 * mm, height=50 * mm))

    def footer(canvas, doc):
        canvas.setFont("ArialLab", 9)
        canvas.drawString(20 * mm, 12 * mm, "Печенов В. В. · ИВТ-465 · ЛР 8")
        canvas.drawRightString(190 * mm, 12 * mm, str(doc.page))

    SimpleDocTemplate(
        str(ROOT / "docs/report.pdf"), leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    (ROOT / "docs/report.md").write_text("\n".join(markdown), encoding="utf-8")
    out = ROOT / "videos/lab08_demo.mp4"
    out.parent.mkdir(exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(out), (1280, 800), fps=10, codec="libx264", quality=7)
    writer.send(None)
    try:
        for seed in range(10):
            for t in range(60):
                writer.send(level_frame(seed, min(1, t / 49)).tobytes())
        im = Image.new("RGB", (1280, 800), "#f2f6fa")
        d = ImageDraw.Draw(im)
        lines = [
            "Результаты · 100 seed · 127 тестов",
            "Жадный бот: 100/100, 101.21 хода",
            "epsilon=0.1: 100/100, 115.05 хода",
            "Случайный: 0/100, лимит 2000 ходов",
            "Исправлены 2 реальные ошибки границы бюджета",
            "CI: lint + pytest + метрики, Python 3.11/3.12",
            "Код, журнал багов и отчёт: GitHub / VladimirPechenov / lab08-ai-testing",
        ]
        for j, line in enumerate(lines):
            d.text((45, 80 + j * 85), line, font=font(28 if j else 40), fill="#17304a")
        for _ in range(100):
            writer.send(im.tobytes())
    finally:
        writer.close()
    print("Created report, chart, screenshot and 70-second video")


if __name__ == "__main__":
    main()
