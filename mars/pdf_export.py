"""
PDF export via LibreOffice headless conversion.

Generates a DOCX using export_sections_to_docx, then converts it to PDF
using soffice --headless. Requires LibreOffice installed (resolved dynamically).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from api.schemas_mars import DraftSection
from mars.docx_export import export_sections_to_docx


def _resolve_soffice() -> str:
    env_path = os.environ.get("SOFFICE_PATH")
    if env_path and Path(env_path).is_file():
        return env_path
    found = shutil.which("soffice")
    if found:
        return found
    for candidate in ["/opt/homebrew/bin/soffice", "/usr/bin/soffice", "/usr/local/bin/soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]:
        if Path(candidate).is_file():
            return candidate
    raise FileNotFoundError("LibreOffice (soffice) not found. Install it or set SOFFICE_PATH.")


def _build_soffice_env(temp_dir: Path, soffice_path: Path) -> dict[str, str]:
    runtime_dir = temp_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.chmod(0o700)

    env = os.environ.copy()
    env["HOME"] = str(temp_dir)
    env["TMPDIR"] = str(temp_dir)
    env["XDG_RUNTIME_DIR"] = str(runtime_dir)
    env["SOFFICE_PATH"] = str(soffice_path)
    env["SAL_USE_VCLPLUGIN"] = "svp"
    env["NO_AT_BRIDGE"] = "1"
    env["OOO_DISABLE_RECOVERY"] = "1"
    env["DISPLAY"] = ""
    return env


def export_sections_to_pdf(
    sections: List[DraftSection],
    output_path: Path,
    locale: str = "en",
    client_branding: dict | None = None,
) -> Path:
    """
    Render sections to a PDF file at output_path.

    Generates a DOCX via export_sections_to_docx, then converts it to PDF
    using LibreOffice headless mode. Returns output_path.
    """
    soffice_path = Path(_resolve_soffice())
    if not soffice_path.exists():
        raise FileNotFoundError(
            f"LibreOffice not found at {soffice_path}. "
            "Install via: brew install --cask libreoffice"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = tempfile.mkdtemp()
    try:
        temp_docx = Path(temp_dir) / "export.docx"
        profile_dir = Path(temp_dir) / "lo-profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        export_sections_to_docx(sections, temp_docx, locale, client_branding)

        try:
            env = _build_soffice_env(Path(temp_dir), soffice_path)
            subprocess.run(
                [
                    str(soffice_path),
                    "--headless",
                    "--invisible",
                    "--nologo",
                    "--nodefault",
                    "--nolockcheck",
                    "--nofirststartwizard",
                    "--norestore",
                    f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    temp_dir,
                    str(temp_docx),
                ],
                timeout=60,
                check=True,
                capture_output=True,
                env=env,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "LibreOffice PDF conversion timed out after 60 seconds"
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else ""
            stdout = exc.stdout.decode(errors="replace") if exc.stdout else ""
            raise RuntimeError(
                f"LibreOffice conversion failed (exit {exc.returncode}): {stderr or stdout}"
            ) from exc

        temp_pdf = Path(temp_dir) / "export.pdf"
        if not temp_pdf.exists():
            raise RuntimeError(
                f"Expected PDF not found at {temp_pdf} after soffice conversion"
            )

        shutil.move(str(temp_pdf), str(output_path))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return output_path
