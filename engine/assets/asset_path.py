from __future__ import annotations

from pathlib import Path


class AssetPathResolver:
    """Canonical project asset paths with case-insensitive legacy lookup."""

    CANONICAL_ROOT = "Assets"

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()

    @property
    def canonical_root(self) -> Path:
        return self.project_root / self.CANONICAL_ROOT

    def physical_roots(self) -> tuple[Path, ...]:
        roots = [self.canonical_root]
        if self.project_root.is_dir():
            roots.extend(
                child
                for child in self.project_root.iterdir()
                if child.is_dir()
                and child.name.casefold() == self.CANONICAL_ROOT.casefold()
                and child != self.canonical_root
            )
        return tuple(roots)

    def canonicalize(self, path: str | Path) -> str:
        candidate = Path(str(path).replace("\\", "/"))
        if candidate.is_absolute():
            for root in self.physical_roots():
                try:
                    relative = candidate.resolve().relative_to(root.resolve())
                    return self._canonical_relative(relative)
                except ValueError:
                    continue
            raise ValueError(f"asset path is outside project asset roots: {candidate}")
        parts = candidate.parts
        if parts and parts[0].casefold() == self.CANONICAL_ROOT.casefold():
            candidate = Path(*parts[1:])
        return self._canonical_relative(candidate)

    def lookup_key(self, path: str | Path) -> str:
        return self.canonicalize(path).casefold()

    def resolve(self, path: str | Path, *, must_exist: bool = False) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            resolved = candidate.resolve()
            if must_exist and not resolved.exists():
                raise FileNotFoundError(path)
            return resolved
        canonical = self.canonicalize(candidate)
        relative = Path(*Path(canonical).parts[1:])
        for root in self.physical_roots():
            resolved = self._resolve_casefold(root, relative)
            if resolved is not None:
                return resolved.resolve()
        fallback = (self.canonical_root / relative).resolve()
        if must_exist:
            raise FileNotFoundError(path)
        return fallback

    def _canonical_relative(self, relative: Path) -> str:
        clean = relative.as_posix().lstrip("/")
        return self.CANONICAL_ROOT if not clean or clean == "." else f"{self.CANONICAL_ROOT}/{clean}"

    @staticmethod
    def _resolve_casefold(root: Path, relative: Path) -> Path | None:
        current = root
        if not current.exists():
            return None
        for part in relative.parts:
            exact = current / part
            if exact.exists():
                current = exact
                continue
            if not current.is_dir():
                return None
            match = next((child for child in current.iterdir() if child.name.casefold() == part.casefold()), None)
            if match is None:
                return None
            current = match
        return current if current.exists() else None
