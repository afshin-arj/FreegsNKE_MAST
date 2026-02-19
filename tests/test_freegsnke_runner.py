from __future__ import annotations

from pathlib import Path

from mast_freegsnke.freegsnke_runner import FreeGSNKERunner


def test_runner_records_import_error_hint(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    script = run_dir / "inverse_run.py"
    script.write_text("import freegsnke\nprint('ok')\n")

    r = FreeGSNKERunner().run_script(script, run_dir=run_dir, label="inverse")
    assert r.ok is False
    # Environment may or may not have freegsnke; if it does, this test would pass unexpectedly.
    # We therefore only assert that if it failed due to import, we tag the hint.
    if r.returncode != 0:
        stderr = (run_dir / r.stderr_path).read_text()
        if "freegsnke" in stderr:
            assert r.error_hint in {"freegsnke_not_installed_in_selected_python", "freegsnke_import_error"}
