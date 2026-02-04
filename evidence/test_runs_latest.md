Status: PASS
Start: 2026-02-04T11:35:40Z
End: 2026-02-04T11:35:43Z
Branch: main
HEAD: 1a7efbf515685c313bcb9ed2367d9f0fc0a8108d
Python: Z:\LittleChef\.venv\\Scripts\\python.exe
compileall exit: 0
import app.main exit: 0
pytest exit: 0
pytest summary: 28 passed, 1 warning in 0.66s
git status -sb:
```
## main...origin/main
 M app/api/deps.py
 M app/api/routers/auth.py
 M app/errors.py
 M scripts/run_local.ps1
?? tests/test_auth_debug_details.py
```
git diff --stat:
```
 app/api/deps.py         | 30 ++++++++++++++++++++++--------
 app/api/routers/auth.py | 28 +++++++++++++++++++++-------
 app/errors.py           |  5 +++--
 scripts/run_local.ps1   |  4 +++-
 4 files changed, 49 insertions(+), 18 deletions(-)
```

