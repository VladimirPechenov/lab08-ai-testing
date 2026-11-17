# Сверка требований ЛР8

| Требование опубликованного шаблона | Доказательство |
|---|---|
| 10+ unit-тестов FSM/BT/perception | tests/unit/test_ai.py: 17 проверок FSM и зонального восприятия |
| Бот-плеер с метриками | player_bot.py, experiment.py; CSV на 300 запусков, JSON, график |
| Solvability на 100 seeds | tests/test_solvability.py, 100 parametrized seed 0..99; полная связность и реальное движение бота |
| Performance с порогами | tests/test_performance.py: p95 генерации <50 мс, тика NPC <1 мс; обоснование README |
| CI: lint, тесты, отчёт о времени | .github/workflows/ci.yml: Python 3.11/3.12, JUnit, durations, результаты эксперимента |
| Минимум 2 бага | docs/bugs.md; исходные падения results/regressions-before.txt, 58ae472; исправление 36412ca |
| Отчёт 4–6 страниц, разделы 1–7, приложение | docs/report.pdf: 5 страниц; Markdown, рисунок и график |
| Видео на YouTube/Диске, ссылка в README, видео не в git | 70 секунд на Google Диске; .gitignore исключает MP4 |
| История step-1, step-2… | поэтапная история поверх исходного шаблона |
| Тег v1.0 и Release | GitHub Releases |

Стек Python разрешён README; Unity не обязателен. В исходном шаблоне нет самих методических указаний,
кафедрального титульного листа и ФИО преподавателя. Эти сведения не выдуманы.
Данные примеров преподавателя не скопированы: все метрики измерены на реальных запусках.
