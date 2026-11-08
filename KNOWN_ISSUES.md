# KNOWN_ISSUES · red-thread-debt-audit · Волна ×5 (2026-11-09)

## Красные CI (было → после патча)

| Run | Что было | Диагноз | После |
|---|---|---|---|
| 42312132721 (11-06 23:28) | guardian-tripwire failure, **0 jobs**, имя рана = путь к файлу | общий корень кластера ×5: пин-склейка `# vXwith:` в tripwire.yml того SHA → «Invalid workflow file» (PyYAML-репро, строки 39–41) | волна ×4 переписала tripwire.yml (e6ff871): зелёный **42517070324** @ e6ff8713 (19:50); ×5-D диспатч: run ****42527372818** (workflow_dispatch → success, 21:52, sha e6ff8713)** |
