# Лабораторная работа № 8. Тестирование игрового ИИ автоботом

**Студент:** Печенов В. В. · **Группа:** ИВТ-465 · **Стек:** Python / pytest · **Дата:** 17.11.2026

**[Отчёт PDF, 5 страниц](docs/report.pdf)** · **[Отчёт Markdown](docs/report.md)** ·
**[Видео, 70 секунд](https://drive.google.com/file/d/1MSn17qVu5pExD4rUUXrRrG-ADP_5Pi_t/view)** ·
**[Release v1.0](https://github.com/VladimirPechenov/lab08-ai-testing/releases/tag/v1.0)**

## Выполнение требований

- [x] 17 unit-проверок FSM и восприятия: все переходы, таймаут, повторный поиск, свет/темнота, тревога, приоритет зрения над шумом.
- [x] Автобот: жадная, epsilon-жадная и случайная политики; 300 запусков с метриками.
- [x] 100 отдельных solvability-тестов seed=0..99: 100% пола доступно, легальность пути, оптимальная длина, повторяемость генерации.
- [x] Performance-тесты с явными порогами: p95 генерации <50 мс, тика NPC <1 мс.
- [x] CI: lint + pytest + эксперимент, Python 3.11/3.12, JUnit, durations и артефакты.
- [x] [Два реально найденных бага](docs/bugs.md), падающие регрессии до исправления сохранены в истории.
- [x] Отчёт на 5 страниц, скриншот и график; видео вынесено на Google Диск, MP4 исключены из git.
- [x] Последовательные коммиты step-1 и далее, тег v1.0, GitHub Release.

Требования взяты из [шаблона преподавателя](https://github.com/kolesnikov-vstu-gameai/lab08-ai-testing).
Отдельных методических указаний, официального титульного листа и ФИО преподавателя нет в предоставленном источнике.
Отчёт следует опубликованным разделам и объёму 4–6 страниц. Соответствие неизвестным материалам не заявляется.
[Подробная сверка](docs/requirements.md).

## Результаты

Локально: **127 passed, 0 skipped**. BSP 64×48, seed=0..99 без отбора, лимит 2000 перемещений.

| Политика | Достигли цели | Средние ходы | Непрогресс / уровень | Покрытие пола |
|---|---:|---:|---:|---:|
| Жадная, epsilon=0 | 100/100 | 101.21 | 0.00 | 9.21% |
| epsilon=0.1 | 100/100 | 115.05 | 6.92 | 9.51% |
| Случайная, epsilon=1 | 0/100 | 2000.00 | 999.81 | 15.98% |

![Сравнение политик](results/comparison.png)

`steps` считает реальные перемещения. `stuck_events` — отсутствие допустимого хода либо ход без уменьшения
BFS-дистанции; это показатель непрогресса, а не автоматически геометрический баг. Покрытие — уникальные
посещённые клетки / весь пол. Средние включают неуспешные запуски. Полный протокол: [CSV](results/bot_metrics.csv),
[сводка](results/summary.json), [среда](results/environment.json), [измерения времени](results/performance.json).

Локальный p95 генерации: **0.1546 мс**, тика FSM: **0.000500 мс**. Порог генерации 50 мс относится к загрузке
уровня. При 60 FPS кадр занимает 16.67 мс, поэтому 1 мс — целевой бюджет простого NPC. Проверяется p95
(nearest-rank) после прогрева, 100 генераций и 1000 тиков Search→Chase, таймер `perf_counter_ns`.
Время исключает BFS и рендер. CI сохраняет свои измерения: числа зависят от машины и нагрузки.

Ограничения: один генератор и размер карты; FSM-тик не заменяет нагрузочный тест полного игрового кадра;
бот знает всю карту расстояний; восприятие из ЛР3 работает на уровне зон, света и фактов.

## Запуск

Из корня репозитория, Python 3.11 или 3.12:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest --durations=10 --junitxml=results/junit.xml
.\.venv\Scripts\python.exe -m bot.experiment
```

В Linux/macOS: `python3 -m venv .venv`, затем `.venv/bin/python` вместо Windows-пути.
`make check` выполняет lint и тесты. Ключевые тесты не пропускаются через `importorskip`.

Для PDF, графика, скриншота и видео:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements-artifacts.txt
.\.venv\Scripts\python.exe -X utf8 tools/build_artifacts.py
```

По умолчанию используется Arial из `C:/Windows/Fonts`. На другой ОС задайте `LAB_FONT_DIR` с файлом `arial.ttf`.
Видео — программная визуализация реального пути бота, 10 seed × 6 секунд + 10 секунд результатов, без звука.
Для точного локального окружения: `pip install -r requirements-lock.txt`, затем `pip install -e .`.

## Структура и источники

- `src/aiunder/`: BSP, BFS из ЛР7; новый минимальный FSM; замеры времени.
- `src/rules/`: собственная база правил ЛР3, проверяемая без изменения логики.
- `src/bot/`: исправленный бот из шаблона и воспроизводимый эксперимент.
- `tests/unit/`, `tests/test_solvability.py`, `tests/test_performance.py`: поведение, 100 карт, бюджеты.
- `results/regressions-before.txt`: два падения исходного бота, коммит `58ae472`; исправление `36412ca`.
- `docs/report.pdf`, `docs/report.md`, `docs/bugs.md`: материалы сдачи.
- `unity/`: примеры преподавателя для альтернативного стека; Python-решение их не использует.

Происхождение: [шаблон ЛР8](https://github.com/kolesnikov-vstu-gameai/lab08-ai-testing),
[собственная ЛР3](https://github.com/VladimirPechenov/lab03-rules-logic),
[собственная ЛР7](https://github.com/VladimirPechenov/lab07-pcg-levels).

## Проверка сдачи

GitHub Actions: [проверки репозитория](https://github.com/VladimirPechenov/lab08-ai-testing/actions).
Первый завершённый прогон: [CI, Python 3.11 и 3.12](https://github.com/VladimirPechenov/lab08-ai-testing/actions/runs/44107870749),
по 127 passed на каждой версии. Снимок проверки: `results/ci-verified.json`.
Доступ к видео: всем по ссылке, роль «Читатель»; проверено после сохранения настроек.
