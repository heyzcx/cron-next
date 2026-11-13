import subprocess
import sys

PY = [sys.executable, "cron_next.py"]


def run(*args):
    proc = subprocess.run(PY + list(args), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip().splitlines()


def test_weekdays():
    lines = run("30 9 * * 1-5", "--from", "2026-11-13 10:00", "-n", "3")
    assert lines[0].startswith("2026-11-16 09:30"), lines
    assert lines[1].startswith("2026-11-17 09:30"), lines
    assert lines[2].startswith("2026-11-18 09:30"), lines


def test_monthly_and_names():
    lines = run("0 0 1 jan *", "--from", "2026-11-13 10:00", "-n", "2")
    assert lines[0].startswith("2027-01-01 00:00"), lines
    assert lines[1].startswith("2028-01-01 00:00"), lines


def test_step_and_range():
    lines = run("*/15 8-9 * * *", "--from", "2026-11-13 08:00", "-n", "3")
    assert lines[0].startswith("2026-11-13 08:15"), lines
    assert lines[1].startswith("2026-11-13 08:30"), lines
    assert lines[2].startswith("2026-11-13 08:45"), lines


def test_dom_or_dow():
    # 1st of month OR Friday: 2026-11-13 is a Friday, so it matches first.
    lines = run("0 12 1 * 5", "--from", "2026-11-12 00:00", "-n", "2")
    assert lines[0].startswith("2026-11-13 12:00"), lines
    assert lines[1].startswith("2026-11-20 12:00"), lines


def test_bad_expression():
    proc = subprocess.run(PY + ["0 0 * *"], capture_output=True, text=True)
    assert proc.returncode == 2
    assert "error" in proc.stderr


if __name__ == "__main__":
    for name, fn in sorted(dict(globals()).items()):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
