from pathlib import Path


def test_smoke_script_write_host_has_no_token_words():
    text = Path("scripts/smoke.ps1").read_text(encoding="utf-8").splitlines()
    write_lines = [line for line in text if "Write-Host" in line or "Write-Output" in line]
    banned = ("Authorization", "BearerToken", "Bearer ")
    for line in write_lines:
        for word in banned:
            assert word not in line, f"Write line leaks token-related word: {word}"
