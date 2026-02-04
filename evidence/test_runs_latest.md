Status: PASS
Start: 2026-02-04T13:25:54Z
End: 2026-02-04T13:25:58Z
Branch: main
HEAD: 11fce1d6ff16c14df37fd079dfb226dede452c77
Python: Z:\LittleChef\.venv\\Scripts\\python.exe
compileall exit: 0
import app.main exit: 0
pytest exit: 0
pytest summary: 30 passed, 1 warning in 1.14s
git status -sb:
```
## main...origin/main
 M app/api/deps.py
 M app/api/routers/auth.py
 M evidence/test_runs.md
 M evidence/test_runs_latest.md
 M scripts/run_local.ps1
 M tests/test_auth_debug_details.py
```
git diff --stat:
```
 app/api/deps.py                  |   7 +-
 app/api/routers/auth.py          |   7 +-
 evidence/test_runs.md            | 169 +++++++++++++++++++++++++++++++++++++++
 evidence/test_runs_latest.md     |  62 +++++++++++---
 scripts/run_local.ps1            |  28 ++++---
 tests/test_auth_debug_details.py |  45 ++++++++---
 6 files changed, 286 insertions(+), 32 deletions(-)
```

