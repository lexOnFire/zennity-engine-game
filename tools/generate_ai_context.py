from pathlib import Path
import platform
import subprocess
import sys
from collections.abc import Sequence

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".ai"
OUT.mkdir(exist_ok=True)


def run(cmd: Sequence[str]) -> str:
    try:
        return subprocess.check_output(
            list(cmd),
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception as e:
        return str(e)


def save(name: str, content: str) -> None:
    (OUT / name).write_text(content, encoding="utf-8")


def main() -> None:
    print("Generating AI Context...")

    save("git_branch.txt", run(["git", "branch"]))
    save("git_status.txt", run(["git", "status"]))
    save("git_log.txt", run(["git", "log", "--oneline", "-20"]))
    save("tree.txt", run(["git", "ls-files"]))
    save("pytest.txt", run([sys.executable, "-m", "pytest", "--tb=short", "-q"]))

    summary = f"""
# Zennity AI Context

OS: {platform.system()}

Python:

{run([sys.executable, "--version"])}

Current Branch:

{run(["git", "branch", "--show-current"])}

Status:

{run(["git", "status", "--short"])}

"""

    save("context.md", summary)

    print("Done.")


if __name__ == "__main__":
    main()
