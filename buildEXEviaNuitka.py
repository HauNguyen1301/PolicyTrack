"""buildEXEviaNuitka.py
Simple helper to compile the PolicyTrack application into a single EXE using Nuitka.

Requirements:
1. Python 3.8+ (same major/minor as the project runtime).
2. Nuitka and its commercial dependency `ordered-set`. Install with:
   pip install nuitka ordered-set zstandard

Usage (PowerShell):
    python buildEXEviaNuitka.py --onefile

Options:
    --onefile      Build a single-file executable (slower start-up, easy distribution).
    --standalone   Build a standalone folder (default if --onefile not supplied).
    --clean        Remove previous build/dist directories before compiling.
    --output NAME  Specify output exe name (default: PolicyTrack.exe / PolicyTrack). 

This script simply wraps the Nuitka CLI, adding sensible defaults such as
including tkinter and data files.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent
ENTRY_SCRIPT = PROJECT_ROOT / "main.py"
DEFAULT_EXE_NAME = "PolicyTrack v0.1.2"


def run(cmd: List[str]):
    """Run a shell command, forwarding output. Exit on failure."""
    print("Executing:", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


def main():
    """Compile the app into a single-file EXE using Nuitka with sensible defaults."""

    parser = argparse.ArgumentParser(description="Build PolicyTrack with Nuitka")
    parser.add_argument("--output", default=DEFAULT_EXE_NAME, help="Executable base name (default: PolicyTrack)")
    parser.add_argument("--noconsole", action="store_true", help="Hide the console window (GUI app)")
    args = parser.parse_args()

    output_name = args.output

    # Always clean previous output to avoid confusion
    for d in (PROJECT_ROOT / "build", PROJECT_ROOT / "dist"):
        if d.exists():
            print(f"Removing {d} …")
            shutil.rmtree(d, ignore_errors=True)

    nuitka_opts = [
        "-m",
        "nuitka",
        str(ENTRY_SCRIPT),
        "--onefile",
        "--enable-plugin=tk-inter",
        "--include-module=tkinter.ttk",
        "--include-module=tkinter.messagebox",
        "--include-module=tkinter.font",
        "--include-module=bcrypt",
        "--include-module=bcrypt._bcrypt",
        "--include-module=libsql_client",
        "--include-module=dotenv",
        "--include-data-files=utils/*=utils/",
        "--include-data-files=ui/*=ui/",
        f"--output-filename={output_name}",
        "--nofollow-import-to=tests,__pycache__",
        "--no-pyi-file",
        "--python-flag=no_site",
    ]

    if args.noconsole:
        nuitka_opts.append("--windows-disable-console")

    cmd = [sys.executable] + nuitka_opts
    run(cmd)

    # Move the generated exe into our own dist folder for easy pickup
    exe_name = f"{output_name}.exe"
    exe_src = PROJECT_ROOT / exe_name
    dist_dir = PROJECT_ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    if exe_src.exists():
        shutil.move(str(exe_src), dist_dir / exe_name)
        print(f"Moved {exe_name} -> dist/{exe_name}")

    # Clean up any build artifacts to leave only the dist folder with the final exe
    for path in PROJECT_ROOT.iterdir():
        if not path.is_dir():
            # Remove stray files that Nuitka may leave such as the original exe
            if path.suffix == ".exe" and path.name == exe_name:
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
            continue

        # Delete known build artifact directories
        if path.name in {"build"} or path.name.endswith(".build") or path.name.endswith(".dist") or path.name == "__nuitka-cache__":
            print(f"Cleaning build artifact: {path}")
            shutil.rmtree(path, ignore_errors=True)

    print("\n✅ Build completed! Find your executable in the 'dist' directory.")


if __name__ == "__main__":
    main()
