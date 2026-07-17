from pathlib import Path
import subprocess
import platform

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / ".ai"
OUT.mkdir(exist_ok=True)


def run(cmd):
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception as e:
        return str(e)


def save(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


print("Generating AI Context...")

save("git_branch.txt", run("git branch"))
save("git_status.txt", run("git status"))
save("git_log.txt", run("git log --oneline -20"))
save("tree.txt", run("git ls-files"))
save("pytest.txt", run("python -m pytest --tb=short -q"))

summary = f"""
# Zennity AI Context

OS: {platform.system()}

Python:

{run("python --version")}

Current Branch:

{run("git branch --show-current")}

Status:

{run("git status --short")}

"""

save("context.md", summary)

print("Done.")