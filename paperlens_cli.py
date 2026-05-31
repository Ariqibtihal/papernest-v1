"""
PaperLens unified CLI.

Entry point dipanggil sebagai `paperlens` setelah `uv sync`. Dipasang
via `[project.scripts]` di pyproject.toml.

Subcommand:
  setup        Install dependencies (Python + Node) dan siapkan .env.
  dev          Jalankan backend + frontend dev server bersamaan.
  start        Build frontend lalu jalankan FastAPI (production mode).
  build        Build frontend production saja (tidak start server).
  test         Jalankan pytest.
  doctor       Cek environment (uv, node, .env, db) dan laporkan masalah.
  db           Subcommand database (alembic upgrade/downgrade/revision).

Tujuan: setelah `git clone` dan satu kali `paperlens setup`, user bisa
ketik `paperlens dev` untuk langsung jalan — sama seperti `9router`.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# ────────────────────────────────────────────────────────────
# Stdout / stderr: pastikan bisa print karakter Unicode (─ ✓ ✗) di Windows
# console (default cp1252). Tanpa ini, redirect ke pipe atau encoding non-UTF8
# akan UnicodeEncodeError. reconfigure() di Python 3.7+ aman dipanggil.
# ────────────────────────────────────────────────────────────
for _stream in (sys.stdout, sys.stderr):
    with contextlib.suppress(AttributeError, OSError):
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# ────────────────────────────────────────────────────────────
# Path & helper
# ────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

IS_WINDOWS = os.name == "nt"

# Warna ANSI sederhana (di-disable kalau bukan TTY)
_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def info(msg: str) -> None:
    print(f"{_c('36', '▶')} {msg}")


def ok(msg: str) -> None:
    print(f"{_c('32', '✓')} {msg}")


def warn(msg: str) -> None:
    print(f"{_c('33', '!')} {msg}")


def fail(msg: str) -> None:
    print(f"{_c('31', '✗')} {msg}", file=sys.stderr)


def have(cmd: str) -> bool:
    """Return True jika `cmd` ada di PATH."""
    return shutil.which(cmd) is not None


def run(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> int:
    """Jalankan command sinkronus dengan output streamed."""
    display = " ".join(cmd)
    info(f"$ {display}")
    proc = subprocess.run(cmd, cwd=cwd, env=env, check=False)
    if check and proc.returncode != 0:
        fail(f"Command failed (exit {proc.returncode}): {display}")
        sys.exit(proc.returncode)
    return proc.returncode


def run_async(
    cmd: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[bytes]:
    """Spawn process tanpa block. Output di-pipe ke parent."""
    info(f"$ {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd, env=env)


# ────────────────────────────────────────────────────────────
# Bootstrap helpers
# ────────────────────────────────────────────────────────────


def ensure_uv() -> None:
    """Pastikan `uv` tersedia. Saran cara install kalau belum."""
    if have("uv"):
        return
    fail("`uv` tidak terinstall.")
    print()
    print("Install uv terlebih dahulu:")
    if IS_WINDOWS:
        print(
            '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"'
        )
    else:
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
    print()
    print("Atau lihat https://docs.astral.sh/uv/getting-started/installation/")
    sys.exit(127)


def ensure_node() -> None:
    """Pastikan Node + npm tersedia (untuk frontend)."""
    if have("node") and have("npm"):
        return
    fail("Node.js / npm tidak terinstall.")
    print()
    print("Install Node.js LTS dari https://nodejs.org/")
    sys.exit(127)


def ensure_env() -> None:
    """Auto-buat `.env` dari template kalau belum ada."""
    if ENV_FILE.exists():
        return
    if not ENV_EXAMPLE.exists():
        warn(".env.example tidak ditemukan, lewati auto-create .env")
        return
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    ok(".env dibuat dari .env.example — edit untuk isi CONTACT_EMAIL, dst.")


def frontend_installed() -> bool:
    """True kalau node_modules sudah ada (heuristik cepat)."""
    return (FRONTEND_DIR / "node_modules").is_dir()


def frontend_built() -> bool:
    return (FRONTEND_DIR / "dist" / "index.html").is_file()


# ────────────────────────────────────────────────────────────
# Subcommand: setup
# ────────────────────────────────────────────────────────────


def cmd_setup(args: argparse.Namespace) -> int:
    """Install dependency Python + Node + buat .env kalau belum ada."""
    info("PaperLens setup — first time bootstrap")

    ensure_uv()
    ensure_env()

    info("Installing Python dependencies via uv (extra: dev)…")
    run(["uv", "sync", "--extra", "dev"], cwd=ROOT)

    if args.skip_frontend:
        warn("Skip frontend setup karena --skip-frontend.")
    else:
        ensure_node()
        info("Installing frontend dependencies via npm…")
        run(["npm", "install"], cwd=FRONTEND_DIR)

    print()
    ok("Setup selesai.")
    print()
    print("Langkah berikutnya:")
    print("  paperlens dev      # mode pengembangan (backend + frontend hot-reload)")
    print("  paperlens start    # build frontend + jalankan production server")
    print("  paperlens doctor   # cek environment")
    return 0


# ────────────────────────────────────────────────────────────
# Subcommand: dev
# ────────────────────────────────────────────────────────────


def cmd_dev(args: argparse.Namespace) -> int:
    """Jalankan FastAPI backend + Vite frontend secara paralel."""
    ensure_uv()
    ensure_env()

    if not args.no_frontend:
        ensure_node()
        if not frontend_installed():
            warn("frontend/node_modules belum ada — menjalankan `npm install`…")
            run(["npm", "install"], cwd=FRONTEND_DIR)

    backend_cmd = [
        "uv",
        "run",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]

    procs: list[subprocess.Popen[bytes]] = []
    info(f"Starting backend on http://{args.host}:{args.port}")
    procs.append(run_async(backend_cmd, cwd=ROOT))

    if not args.no_frontend:
        # `npm run dev` di Windows hanya jalan via shell `npm.cmd` ketika
        # dipanggil dari Python; gunakan shell=True via list dengan npm path.
        npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
        info("Starting frontend (Vite) on http://localhost:5173")
        procs.append(run_async([npm_cmd, "run", "dev"], cwd=FRONTEND_DIR))

    print()
    ok("Servers running. Tekan Ctrl+C untuk berhenti.")
    print()

    return _wait_for_procs(procs)


def _wait_for_procs(procs: list[subprocess.Popen[bytes]]) -> int:
    """Block sampai user Ctrl+C atau salah satu proses mati."""
    try:
        while True:
            time.sleep(0.5)
            for p in procs:
                rc = p.poll()
                if rc is not None:
                    fail(f"Process exited unexpectedly (code {rc}). Stopping all.")
                    _terminate_all(procs)
                    return rc or 1
    except KeyboardInterrupt:
        print()
        info("Ctrl+C diterima, menghentikan semua proses…")
        _terminate_all(procs)
        return 0


def _terminate_all(procs: list[subprocess.Popen[bytes]]) -> None:
    for p in procs:
        if p.poll() is not None:
            continue
        try:
            if IS_WINDOWS:
                p.terminate()
            else:
                p.send_signal(signal.SIGINT)
        except Exception:
            pass
    # Beri grace period 3 detik
    deadline = time.time() + 3
    for p in procs:
        remaining = max(0, deadline - time.time())
        try:
            p.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            p.kill()


# ────────────────────────────────────────────────────────────
# Subcommand: build
# ────────────────────────────────────────────────────────────


def cmd_build(args: argparse.Namespace) -> int:
    """Build frontend production (output ke frontend/dist)."""
    ensure_node()
    if not frontend_installed():
        info("frontend/node_modules belum ada — install dulu…")
        run(["npm", "install"], cwd=FRONTEND_DIR)

    npm_cmd = "npm.cmd" if IS_WINDOWS else "npm"
    info("Building frontend (Vite production)…")
    run([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)
    ok(f"Build siap di {FRONTEND_DIR / 'dist'}")
    return 0


# ────────────────────────────────────────────────────────────
# Subcommand: start (production)
# ────────────────────────────────────────────────────────────


def cmd_start(args: argparse.Namespace) -> int:
    """Production: pastikan frontend ter-build, lalu jalankan FastAPI."""
    ensure_uv()
    ensure_env()

    if not args.skip_build:
        if not frontend_built():
            info("frontend/dist belum ada — building dulu…")
            cmd_build(args)
        else:
            info("frontend/dist ditemukan, skip build (pakai --rebuild kalau mau force).")

    if args.rebuild:
        cmd_build(args)

    backend_cmd = [
        "uv",
        "run",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.workers > 1:
        backend_cmd += ["--workers", str(args.workers)]

    info(f"Starting production server on http://{args.host}:{args.port}")
    rc = run(backend_cmd, cwd=ROOT, check=False)
    return rc


# ────────────────────────────────────────────────────────────
# Subcommand: test
# ────────────────────────────────────────────────────────────


def cmd_test(args: argparse.Namespace) -> int:
    ensure_uv()
    cmd = ["uv", "run", "pytest"]
    cmd += args.pytest_args
    return run(cmd, cwd=ROOT, check=False)


# ────────────────────────────────────────────────────────────
# Subcommand: db (alembic wrapper)
# ────────────────────────────────────────────────────────────


def cmd_db(args: argparse.Namespace) -> int:
    ensure_uv()
    cmd = ["uv", "run", "alembic", args.action]
    if args.action == "upgrade" and not args.target:
        cmd.append("head")
    elif args.target:
        cmd.append(args.target)
    if args.action == "revision":
        cmd += ["--autogenerate", "-m", args.message or "manual revision"]
    return run(cmd, cwd=ROOT, check=False)


# ────────────────────────────────────────────────────────────
# Subcommand: doctor
# ────────────────────────────────────────────────────────────


def cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnostik environment — cek semua prerequisite."""
    print()
    print(_c("1;36", "PaperLens doctor"))
    print("─" * 40)

    checks: list[tuple[str, bool, str]] = []

    checks.append(
        (
            "uv installed",
            have("uv"),
            "Install: https://docs.astral.sh/uv/getting-started/installation/",
        )
    )
    checks.append(("Node.js installed", have("node"), "Install Node LTS dari https://nodejs.org/"))
    checks.append(("npm installed", have("npm"), "Biasanya bundled dengan Node"))
    checks.append((".env file exists", ENV_FILE.exists(), "Jalankan: paperlens setup"))

    venv_dir = ROOT / ".venv"
    venv_exists = venv_dir.is_dir()
    checks.append(
        (
            "Project virtualenv exists (.venv)",
            venv_exists,
            "Jalankan: paperlens setup (atau uv sync --extra dev)",
        )
    )

    # Cek dep penting di venv (loguru sering jadi sinyal pertama deps belum ter-sync).
    venv_python = venv_dir / "Scripts" / "python.exe" if IS_WINDOWS else venv_dir / "bin" / "python"
    deps_ok = False
    if venv_exists and venv_python.is_file():
        rc = subprocess.run(
            [str(venv_python), "-c", "import loguru, uvicorn, fastapi"],
            capture_output=True,
        ).returncode
        deps_ok = rc == 0
    checks.append(
        (
            "Python deps in venv (loguru, uvicorn, fastapi)",
            deps_ok,
            "Jalankan: uv sync --extra dev",
        )
    )

    # Deteksi `uvicorn` global di PATH yang bisa nyamar — penyebab umum
    # ModuleNotFoundError saat user menjalankan `uvicorn app.main:app` langsung
    # tanpa `uv run` / activate venv.
    uvicorn_path = shutil.which("uvicorn")
    if uvicorn_path:
        uv_p = Path(uvicorn_path).resolve()
        venv_uv = (
            venv_dir / "Scripts" / "uvicorn.exe" if IS_WINDOWS else venv_dir / "bin" / "uvicorn"
        )
        is_venv_uvicorn = venv_uv.is_file() and uv_p == venv_uv.resolve()
        if not is_venv_uvicorn:
            warn(
                f"uvicorn di PATH bukan dari .venv project: {uv_p}\n"
                f"    └─ Jangan jalankan `uvicorn ...` langsung — pakai "
                f"`paperlens dev` atau `uv run uvicorn ...` agar dependencies project ter-load."
            )

    checks.append(
        (
            "Frontend deps installed",
            frontend_installed(),
            "Jalankan: cd frontend && npm install",
        )
    )
    checks.append(
        (
            "Frontend built (production only)",
            frontend_built(),
            "Jalankan: paperlens build",
        )
    )

    all_ok = True
    for label, passed, hint in checks:
        if passed:
            print(f"  {_c('32', '✓')} {label}")
        else:
            all_ok = False
            print(f"  {_c('31', '✗')} {label}")
            print(f"    {_c('90', '└─')} {hint}")

    print()
    if all_ok:
        ok("Semua siap. `paperlens dev` atau `paperlens start`.")
        return 0
    warn("Ada item yang belum siap (lihat di atas).")
    return 1


# ────────────────────────────────────────────────────────────
# Argparse wiring
# ────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paperlens",
        description=(
            "PaperLens unified CLI — setup, dev, build, start, dan test "
            "untuk research paper aggregator."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Quickstart setelah git clone:\n"
            "  paperlens setup       # install Python + Node deps, buat .env\n"
            "  paperlens dev         # jalankan dev server (backend + frontend)\n"
            "  paperlens start       # production mode (build + serve)\n"
            "\n"
            "Belum punya `paperlens` di PATH? Pakai `uv run paperlens <cmd>` "
            "atau script bootstrap `./paperlens.bat` (Windows) / `./paperlens` (Unix)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=False)

    # setup
    p_setup = sub.add_parser("setup", help="Install dependencies dan siapkan .env (first time)")
    p_setup.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Lewati npm install (kalau frontend dihandle terpisah)",
    )
    p_setup.set_defaults(func=cmd_setup)

    # dev
    p_dev = sub.add_parser("dev", help="Jalankan backend + frontend dev server")
    p_dev.add_argument("--host", default="0.0.0.0", help="Backend host (default: 0.0.0.0)")
    p_dev.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    p_dev.add_argument(
        "--no-frontend",
        action="store_true",
        help="Jalankan backend saja (tanpa Vite dev server)",
    )
    p_dev.set_defaults(func=cmd_dev)

    # build
    p_build = sub.add_parser("build", help="Build frontend production")
    p_build.set_defaults(func=cmd_build)

    # start
    p_start = sub.add_parser("start", help="Production: build (kalau perlu) + jalankan FastAPI")
    p_start.add_argument("--host", default="0.0.0.0")
    p_start.add_argument("--port", type=int, default=8000)
    p_start.add_argument("--workers", type=int, default=1, help="Jumlah uvicorn workers")
    p_start.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip build walau frontend/dist belum ada",
    )
    p_start.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild frontend",
    )
    p_start.set_defaults(func=cmd_start)

    # test
    p_test = sub.add_parser("test", help="Jalankan pytest (forward args ke pytest)")
    p_test.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Argumen lanjutan ke pytest")
    p_test.set_defaults(func=cmd_test)

    # db
    p_db = sub.add_parser("db", help="Database: alembic wrapper")
    p_db.add_argument("action", choices=["upgrade", "downgrade", "current", "history", "revision"])
    p_db.add_argument("target", nargs="?", default=None, help="Target (mis. head, -1, base)")
    p_db.add_argument("-m", "--message", help="Pesan revisi (untuk action=revision)")
    p_db.set_defaults(func=cmd_db)

    # doctor
    p_doctor = sub.add_parser("doctor", help="Cek environment")
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Default behaviour: tanpa subcommand → tampilkan help singkat + doctor.
    if not args.command:
        parser.print_help()
        print()
        return cmd_doctor(args)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
