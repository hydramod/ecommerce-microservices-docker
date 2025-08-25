#!/usr/bin/env python3
"""
gen_service_reqs.py — generate requirements.txt for each service using pipreqs
(Uses the pipreqs console script; avoids `python -m pipreqs` which fails on Windows.)
"""
import argparse, os, shutil, subprocess, sys
from pathlib import Path

SERVICES = ["auth", "catalog", "order", "cart", "payment", "shipping", "notifications"]

def venv_bin(name: str) -> Path:
    base = Path(sys.executable).parent
    return base / (name + (".exe" if os.name == "nt" else ""))

def ensure_pipreqs() -> str:
    # Prefer the pipreqs binary in this interpreter's venv/bin or venv/Scripts
    exe_path = venv_bin("pipreqs")
    if exe_path.exists():
        return str(exe_path)
    # Otherwise, try PATH
    found = shutil.which("pipreqs")
    if found:
        return found
    # Install into current interpreter's environment
    print("pipreqs not found. Installing into current environment...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pipreqs"], check=True)
    # Try again
    if exe_path.exists():
        return str(exe_path)
    found = shutil.which("pipreqs")
    if found:
        return found
    print("Error: pipreqs installation succeeded but executable not found.", file=sys.stderr)
    sys.exit(1)

def run_pipreqs(pipreqs_exe: str, service_dir: Path) -> Path | None:
    if not (service_dir / "app").exists():
        return None
    req_path = service_dir / "requirements.txt"
    cmd = [
        pipreqs_exe,
        str(service_dir),
        "--force",
        "--encoding", "utf-8",
        "--savepath", str(req_path),
    ]
    print(">>>", " ".join(cmd))
    subprocess.run(cmd, check=True)

    # Post-process: de-dup, sort, strip blanks and pkg-resources noise
    lines = [ln.strip() for ln in req_path.read_text(encoding="utf-8").splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("#") and not ln.startswith("pkg-resources==")]
    req_path.write_text("\n".join(sorted(set(lines))) + "\n", encoding="utf-8")
    return req_path

def combine_requirements(paths: list[Path], target: Path):
    seen, out = set(), []
    for p in paths:
        if not p or not p.exists():
            continue
        for ln in p.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln or ln in seen:
                continue
            seen.add(ln); out.append(ln)
    target.write_text("\n".join(sorted(out)) + "\n", encoding="utf-8")
    print(f"Combined requirements written to {target}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--services", nargs="*", default=SERVICES, help="Subset of services")
    ap.add_argument("--combine", action="store_true", help="Also create a combined requirements.txt at repo root")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    pipreqs_exe = ensure_pipreqs()

    generated: list[Path] = []
    for s in args.services:
        svc_dir = repo_root / "services" / s
        if svc_dir.exists():
            p = run_pipreqs(pipreqs_exe, svc_dir)
            if p: generated.append(p)

    if args.combine and generated:
        combine_requirements(generated, repo_root / "requirements.txt")

    print("Done.")

if __name__ == "__main__":
    main()
