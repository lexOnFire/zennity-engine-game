# Custom Rules for Zennity Engine

## Automatically Commit and Push to Git/GitHub
Always stage, commit, and push all modifications to the active GitHub branch at the end of each successful task execution.
- Only stage files relevant to the implementation (avoid staging large ZIP files, local system backups, or temporary CLI outputs like `exit`).
- Write clear, descriptive commit messages describing the changes (following Conventional Commits style when possible, e.g., `feat(...)` or `fix(...)`).
- Use the `git push` command to send the changes to the active branch.
