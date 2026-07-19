"""Registry central de codecs versionados e gravação JSON atômica."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


Loader = Callable[[Mapping[str, Any]], Any]
Dumper = Callable[[Any], Mapping[str, Any]]


@dataclass(frozen=True, slots=True)
class SerializationCodec:
    kind: str
    extensions: tuple[str, ...]
    current_version: int
    load: Loader
    dump: Dumper


class SerializationRegistry:
    def __init__(self) -> None:
        self._by_kind: dict[str, SerializationCodec] = {}
        self._by_extension: dict[str, SerializationCodec] = {}

    def register(self, codec: SerializationCodec) -> None:
        if codec.kind in self._by_kind:
            raise ValueError(f"Codec já registrado: {codec.kind}")
        for extension in codec.extensions:
            normalized = extension.lower() if extension.startswith(".") else f".{extension.lower()}"
            if normalized in self._by_extension:
                raise ValueError(f"Extensão já registrada: {normalized}")
            self._by_extension[normalized] = codec
        self._by_kind[codec.kind] = codec

    def codec_for(self, kind_or_path: str | Path) -> SerializationCodec:
        key = str(kind_or_path)
        if key in self._by_kind:
            return self._by_kind[key]
        extension = Path(key).suffix.lower()
        try:
            return self._by_extension[extension]
        except KeyError as exc:
            raise KeyError(f"Formato não registrado: {kind_or_path}") from exc

    def read(self, path: str | Path) -> Any:
        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{source.name}: raiz JSON deve ser objeto")
        return self.codec_for(source).load(payload)

    def write(self, path: str | Path, value: Any) -> None:
        target = Path(path)
        codec = self.codec_for(target)
        payload = dict(codec.dump(value))
        payload.setdefault("format_version", codec.current_version)
        atomic_write_json(target, payload)


def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(json.dumps(dict(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)
