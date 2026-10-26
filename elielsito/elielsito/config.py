"""Configuración de Elielsito.

Reglas:
- La configuración NO contiene secretos. Las claves se leen del entorno.
- El archivo de configuración se guarda como JSON en ``~/.elielsito/config.json``.
- Las variables de entorno tienen prioridad sobre el archivo.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".elielsito"

VALID_PROVIDERS = {"mock", "openai", "anthropic", "gemini", "ollama"}

ENV_PREFIX = "ELELSITO_"


def _env(name: str) -> str | None:
    value = os.environ.get(ENV_PREFIX + name)
    return value if value not in (None, "") else None


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


@dataclass
class ModelConfig:
    provider: str = "mock"
    name: str = "mock-1"
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1024
    timeout: int = 60

    def validate(self) -> None:
        if self.provider not in VALID_PROVIDERS:
            raise ValueError(
                f"Proveedor de modelo no válido: {self.provider!r}. "
                f"Opciones: {', '.join(sorted(VALID_PROVIDERS))}"
            )
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("temperature debe estar entre 0 y 2")
        if self.max_tokens < 1:
            raise ValueError("max_tokens debe ser mayor que 0")


@dataclass
class SafetyConfig:
    """Límites de seguridad. Valores conservadores por defecto."""

    max_steps: int = 12
    max_seconds: int = 180
    allow_shell: bool = False
    allowed_roots: list[str] = field(default_factory=list)
    require_approval: list[str] = field(default_factory=lambda: ["execute", "danger"])

    def validate(self) -> None:
        if self.max_steps < 1:
            raise ValueError("max_steps debe ser al menos 1")
        if self.max_seconds < 1:
            raise ValueError("max_seconds debe ser al menos 1")


@dataclass
class MemoryConfig:
    enabled: bool = True
    db_filename: str = "memory.db"
    max_items: int = 20000

    def validate(self) -> None:
        if self.max_items < 1:
            raise ValueError("max_items debe ser al menos 1")


@dataclass
class Config:
    app_name: str = "Elielsito"
    data_dir: str = str(DEFAULT_DATA_DIR)
    model: ModelConfig = field(default_factory=ModelConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    # ------------------------------------------------------------------ rutas
    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).expanduser()

    @property
    def config_file(self) -> Path:
        return self.data_path / "config.json"

    @property
    def memory_db(self) -> Path:
        return self.data_path / self.memory.db_filename

    @property
    def audit_file(self) -> Path:
        return self.data_path / "audit.log"

    def allowed_roots(self) -> list[Path]:
        roots = [Path(r).expanduser().resolve() for r in self.safety.allowed_roots]
        roots.append(self.data_path.resolve())
        return roots

    # ------------------------------------------------------------------ ciclo
    def ensure_dirs(self) -> None:
        self.data_path.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        self.model.validate()
        self.safety.validate()
        self.memory.validate()

    def apply_env(self) -> "Config":
        """Aplica variables de entorno sobre la configuración actual."""
        if (value := _env("DATA_DIR")) is not None:
            self.data_dir = value
        if (value := _env("MODEL_PROVIDER")) is not None:
            self.model.provider = value.strip().lower()
        if (value := _env("MODEL_NAME")) is not None:
            self.model.name = value
        if (value := _env("MODEL_BASE_URL")) is not None:
            self.model.base_url = value
        self.safety.allow_shell = _env_bool("ALLOW_SHELL", self.safety.allow_shell)
        if (value := _env("ALLOWED_ROOTS")) is not None:
            self.safety.allowed_roots = [
                part for part in value.replace(";", os.pathsep).split(os.pathsep) if part
            ]
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        model = ModelConfig(**{**asdict(ModelConfig()), **(data.get("model") or {})})
        safety = SafetyConfig(**{**asdict(SafetyConfig()), **(data.get("safety") or {})})
        memory = MemoryConfig(**{**asdict(MemoryConfig()), **(data.get("memory") or {})})
        return cls(
            app_name=data.get("app_name", "Elielsito"),
            data_dir=data.get("data_dir", str(DEFAULT_DATA_DIR)),
            model=model,
            safety=safety,
            memory=memory,
        )

    def save(self, path: Path | None = None) -> Path:
        target = path or self.config_file
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(target)  # escritura atómica: nunca deja el archivo a medias
        return target

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        if path is None:
            # Respetar ELELSITO_DATA_DIR al localizar el archivo de configuración.
            env_dir = os.environ.get(ENV_PREFIX + "DATA_DIR")
            base = Path(env_dir) if env_dir else DEFAULT_DATA_DIR
            target = base / "config.json"
        else:
            target = path
        data: dict = {}
        if target.exists():
            try:
                data = json.loads(target.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"El archivo de configuración está dañado: {target}") from exc
        config = cls.from_dict(data)
        config.apply_env()
        config.validate()
        return config
