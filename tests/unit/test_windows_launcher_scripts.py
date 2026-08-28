from __future__ import annotations

from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]


def test_shortcut_installer_persists_paths_only_and_uses_hidden_window() -> None:
    source = (REPOSITORY / "tools" / "windows" / "Install-PAIM-DesktopShortcut.ps1").read_text(
        encoding="utf-8"
    )
    assert "repository_path" in source
    assert "configuration_path" in source
    assert "-WindowStyle Hidden" in source
    assert ".lnk" in source
    for prohibited in ("credential_env", "TOKEN", "Password", "credential_value"):
        assert prohibited not in source


def test_start_wrapper_uses_locked_launcher_without_secret_or_broad_kill() -> None:
    source = (REPOSITORY / "tools" / "windows" / "Start-PAIM.ps1").read_text(encoding="utf-8")
    assert "run --locked paim-launcher --config" in source
    assert "PresentationFramework" in source
    for prohibited in ("TOKEN", "Password", "taskkill", "Stop-Process", "Get-Process"):
        assert prohibited not in source
