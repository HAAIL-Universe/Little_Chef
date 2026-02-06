Cycle: 2026-02-06T11:51:02Z
Branch: main
BASE_HEAD: f24547d9498dd942ee17569e525933e455a8762c (working tree)
Status: IN_PROCESS
Contracts read: Contracts/builder_contract.md, Contracts/blueprint.md, Contracts/manifesto.md, Contracts/physics.yaml, Contracts/ui_style.md, Contracts/phases_7_plus.md; Contracts/directive.md NOT PRESENT (allowed)
Allowed files: evidence/updatedifflog.md

## Summary
- Checkpoint prep: New Thread history UI/test/dist rebuild plus thread persistence guard are staged with the latest evidence/test_runs entries (2026-02-06T11:50:38Z run) and the diff log will record this clean bundle for authorization.
- `/fill` backend routing fix remains in the working tree (`app/services/chat_service.py` + `tests/test_chat_mode_commands.py`) and is intentionally excluded from this checkpoint.

## Files Changed (staged)
- app/services/thread_messages_repo.py
- evidence/codex.md
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- tests/test_ui_new_thread_button.py
- web/dist/main.js
- web/src/main.ts

## git status -sb
```
## main...origin/main [ahead 10]
 M app/services/chat_service.py
M  app/services/thread_messages_repo.py
M  evidence/codex.md
M  evidence/test_runs.md
M  evidence/test_runs_latest.md
M  evidence/updatedifflog.md
 M tests/test_chat_mode_commands.py
A  tests/test_ui_new_thread_button.py
M  web/dist/main.js
M  web/src/main.ts
```

## Minimal Diff Hunks
```
diff --git a/app/services/thread_messages_repo.py b/app/services/thread_messages_repo.py
index f51041b..4e63a03 100644
--- a/app/services/thread_messages_repo.py
+++ b/app/services/thread_messages_repo.py
@@ -11,6 +11,20 @@ class ThreadMessagesRepo:
             return None
         try:
             with connect() as conn, conn.cursor() as cur:
+                # Ensure a threads row exists for this thread/user
+                try:
+                    cur.execute(
+                        """
+                        INSERT INTO threads (thread_id, user_id)
+                        VALUES (%s, %s)
+                        ON CONFLICT (thread_id) DO NOTHING
+                        """,
+                        (thread_id, user_id),
+                    )
+                except Exception:
+                    # best-effort; continue even if this fails
+                    pass
                 cur.execute(
                     """
                     SELECT COALESCE(MAX(split_part(message_id, '-', 2)::int), 0) + 1
@@ -33,4 +47,3 @@ class ThreadMessagesRepo:
         except Exception:
             # Non-fatal: skip persistence if DB unavailable
             return None
```

```
diff --git a/web/src/main.ts b/web/src/main.ts
index 59bf157..e7123b1 100644
--- a/web/src/main.ts
+++ b/web/src/main.ts
@@ -29,6 +29,10 @@ const duetState = {
 };
 let lastServerMode = "ASK";

+function currentModeLower() {
+  return (lastServerMode || "ASK").toLowerCase();
+}
+
 let historyOverlay: HTMLDivElement | null = null;
@@ -430,6 +443,18 @@ function setupHistoryDrawerUi() {
  const stage = document.querySelector(".duet-stage");
  if (!shell || !stage) return;

  const historyPanel = document.getElementById("duet-history");
  const historyHeader = historyPanel?.querySelector(".history-header");
  if (historyHeader && !historyHeader.querySelector("#duet-new-thread")) {
    const newThreadBtn = document.createElement("button");
    newThreadBtn.id = "duet-new-thread";
    newThreadBtn.type = "button";
    newThreadBtn.className = "pill-btn";
    newThreadBtn.textContent = "New Thread";
    newThreadBtn.addEventListener("click", () => startNewThread());
    historyHeader.appendChild(newThreadBtn);
  }

```

```
diff --git a/tests/test_ui_new_thread_button.py b/tests/test_ui_new_thread_button.py
new file mode 100644
index 0000000..4b16ba6
--- /dev/null
+++ b/tests/test_ui_new_thread_button.py
@@ -0,0 +1,12 @@
+from pathlib import Path
+
+
def test_new_thread_button_and_thread_reset_hooks_present():
    src = Path("web/src/main.ts").read_text()
    assert "New Thread" in src
    assert "startNewThread" in src
    assert "crypto.randomUUID" in src
    assert "duetState.history = []" in src
```

## Verification
- `python -m compileall app`: PASS
- `python -c "import app.main; print('import ok')"`: PASS
- `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`: PASS (53 passed, 1 warning: python_multipart; recorded at 2026-02-06T11:50:38Z–11:50:46Z in `evidence/test_runs.md`/`test_runs_latest.md`)

## Notes
- `/fill` backend mode change is still staged/unstaged outside this checkpoint (`app/services/chat_service.py`, `tests/test_chat_mode_commands.py`) and will be addressed in the next cycle after this checkpoint is authorized.

## Next Steps
- Await Julius’ `AUTHORIZED` before committing this checkpoint bundle.
+  const historyPanel = document.getElementById("duet-history");
+  const historyHeader = historyPanel?.querySelector(".history-header");
+  if (historyHeader && !historyHeader.querySelector("#duet-new-thread")) {
+    const newThreadBtn = document.createElement("button");
+    newThreadBtn.id = "duet-new-thread";
+    newThreadBtn.type = "button";
+    newThreadBtn.className = "pill-btn";
+    newThreadBtn.textContent = "New Thread";
+    newThreadBtn.addEventListener("click", () => startNewThread());
+    historyHeader.appendChild(newThreadBtn);
+  }
