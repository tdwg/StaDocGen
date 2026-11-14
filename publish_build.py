"""
Publish a StaDocGen instance build into the local clone of the standard's repo.

Usage (from the stadocgen repo root, or anywhere):
    python publish_build.py mids
    python publish_build.py mids --dry-run     # show what would happen, change nothing

Steps:
  1. Bring the target repo up to date (git pull --ff-only). Aborts if the
     target repo has uncommitted changes or the pull is not a fast-forward.
  2. Back up the target repo's current docs/ folder to a timestamped zip
     (outside the target repo, so the backup never gets committed).
  3. Replace the contents of docs/ with <ns>/app/build/.

CNAME in the target docs/ folder is never moved, deleted, or edited. A CNAME
inside the build directory is ignored.

The script does not commit or push; review and commit in the target repo.

Configuration is read from .env in the stadocgen repo root:
    MIDS_REPO=G:\\repos\\tdwg\\mids
    LTC_REPO=G:\\repos\\tdwg\\ltc
    MINEXT_REPO=G:\\repos\\tdwg\\mineralogy
    BACKUP_DIR=G:\\repos\\tdwg\\stadocgen\\backups   (optional)
See .env.example.
"""
import argparse
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PROTECTED = "CNAME"


def load_env(path: Path) -> dict:
    """Minimal .env reader (KEY=VALUE lines, # comments, optional quotes)."""
    env = {}
    if not path.is_file():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        env[key.strip()] = value
    return env


def fail(msg: str):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def git(repo: Path, *args) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed in {repo}:\n{result.stderr.strip()}")
    return result.stdout.strip()


def update_repo(repo: Path, dry_run: bool):
    print(f"[1/3] Updating {repo}")
    dirty = git(repo, "status", "--porcelain")
    if dirty:
        fail(f"{repo} has uncommitted changes; commit or stash them first:\n{dirty}")
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    print(f"      branch: {branch}")
    if dry_run:
        git(repo, "fetch")
        print("      " + (git(repo, "status", "-sb").splitlines()[0]))
        print("      (dry run: not pulling)")
        return
    out = git(repo, "pull", "--ff-only")
    print("      " + out.replace("\n", "\n      "))


def backup_docs(docs: Path, backup_dir: Path, ns: str, dry_run: bool):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / ns / f"docs-{stamp}"
    print(f"[2/3] Backing up {docs} -> {target}.zip")
    if not docs.exists():
        print("      docs/ does not exist; nothing to back up")
        return
    if dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.make_archive(str(target), "zip", root_dir=docs)


def _force_remove(func, path, _exc):
    # Windows: clear read-only flag and retry
    os.chmod(path, stat.S_IWRITE)
    func(path)


def replace_docs(build: Path, docs: Path, dry_run: bool):
    print(f"[3/3] Replacing {docs} with {build}")
    if dry_run:
        for item in sorted(docs.iterdir()) if docs.exists() else []:
            if item.name != PROTECTED:
                print(f"      would remove {item.name}")
        for item in sorted(build.iterdir()):
            if item.name != PROTECTED:
                print(f"      would copy   {item.name}")
        if (build / PROTECTED).exists():
            print(f"      would skip   build/{PROTECTED}")
        return

    docs.mkdir(exist_ok=True)
    for item in docs.iterdir():
        if item.name == PROTECTED:
            continue
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item, onerror=_force_remove)
        else:
            item.unlink()

    for item in build.iterdir():
        if item.name == PROTECTED:
            print(f"      skipping build/{PROTECTED} (target {PROTECTED} is never touched)")
            continue
        dest = docs / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)


def main():
    parser = argparse.ArgumentParser(description="Copy <ns>/app/build into the standard repo's docs/ folder.")
    parser.add_argument("ns", help="instance namespace folder, e.g. mids, ltc, minext")
    parser.add_argument("--dry-run", action="store_true", help="report actions without changing anything")
    args = parser.parse_args()

    ns = args.ns.strip("/\\").lower()
    env = {**load_env(PROJECT_ROOT / ".env"), **os.environ}

    repo_value = env.get(f"{ns.upper()}_REPO")
    if not repo_value:
        fail(f"{ns.upper()}_REPO is not set in {PROJECT_ROOT / '.env'}")
    repo = Path(repo_value).resolve()
    if not (repo / ".git").exists():
        fail(f"{repo} is not a git repository")

    build = (PROJECT_ROOT / ns / "app" / "build").resolve()
    if not (build / "index.html").is_file():
        fail(f"{build} has no index.html; run 'python freeze.py build' in {ns}/app first")

    docs = repo / "docs"
    backup_dir = Path(env.get("BACKUP_DIR") or PROJECT_ROOT / "backups").resolve()
    if repo in backup_dir.parents or backup_dir == repo:
        fail(f"BACKUP_DIR {backup_dir} must be outside the target repo")

    if args.dry_run:
        print("DRY RUN: no changes will be made\n")

    update_repo(repo, args.dry_run)
    backup_docs(docs, backup_dir, ns, args.dry_run)

    cname = docs / PROTECTED
    cname_before = cname.read_bytes() if cname.exists() else None
    replace_docs(build, docs, args.dry_run)
    cname_after = cname.read_bytes() if cname.exists() else None
    if cname_before != cname_after:
        fail(f"{cname} changed unexpectedly; restore it from the backup")
    if cname_before is None:
        print(f"WARNING: {cname} does not exist in the target repo")

    if not args.dry_run:
        print("\nDone. Changes in target repo (not committed):")
        print(git(repo, "status", "--short", "--", "docs") or "  (no changes)")


if __name__ == "__main__":
    main()
