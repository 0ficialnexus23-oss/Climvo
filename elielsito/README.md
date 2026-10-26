# Elielsito AI

Asistente personal de inteligencia artificial: modular, extensible, con memoria
persistente, herramientas controladas y aprendizaje verificable.

> **Estado actual: Etapa 2 (núcleo + configuración + memoria + modelos + herramientas).**
> La voz, la navegación web autónoma y el control del ordenador llegan en etapas
> posteriores. Ver `docs/ARQUITECTURA.md`.

## Qué es (y qué no es)

**Es** un sistema real que:
- conversa en español con una identidad persistente;
- usa un modelo de IA **intercambiable** (API o local) sin tocar el resto del código;
- guarda memoria útil entre sesiones (SQLite, con búsqueda y categorías);
- ejecuta **herramientas** con permisos, validación y registro de auditoría;
- se detiene ante operaciones sensibles y pide autorización.

**No es** (todavía): voz, navegación web, control del ordenador, habilidades
modulares ni automejora. Todo eso está diseñado pero **aún no implementado**.

## Requisitos

- Python 3.11 o superior.
- Opcional: una clave de API de un proveedor de modelos, **o** un servidor local
  compatible con OpenAI (Ollama, LM Studio, llama.cpp).

Sin clave ni servidor local, funciona en **modo `mock`**: permite probar toda la
arquitectura sin gastar nada y sin internet.

## Instalación

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -e ".[dev]"
cp .env.example .env      # completa tus claves (nunca se versionan)
```

## Uso

```bash
elielsito doctor                 # revisa el entorno y la configuración
elielsito chat                   # conversación interactiva
elielsito chat -m "Hola"         # un solo mensaje
elielsito memory list            # ver la memoria
elielsito memory search "clave"  # buscar en la memoria
elielsito tools                  # herramientas registradas
```

## Modelo local gratis con Ollama (recomendado)

Ollama ejecuta el modelo **en tu equipo**: sin claves, sin cuotas y sin enviar
tus conversaciones a internet. Guía completa en [`docs/OLLAMA.md`](docs/OLLAMA.md).

```bash
# 1) instala Ollama desde https://ollama.com/download
# 2) descarga un modelo acorde a tu RAM
ollama pull qwen2.5:7b
# 3) configura Elielsito (detecta tu RAM y elige el modelo)
python scripts/configurar_ollama.py
# 4) comprueba y conversa
elielsito doctor
elielsito chat -m "Hola Elielsito"
```

| RAM | Modelo |
|---|---|
| ≤ 8 GB | `qwen2.5:3b` |
| 8–15 GB | `qwen2.5:7b` |
| 16–31 GB | `qwen2.5:14b` |
| ≥ 32 GB | `qwen2.5:32b` |

## Interfaz web

Además de la terminal, Elielsito tiene una interfaz web local con chat,
herramientas, memoria, auditoría y estado del sistema.

```bash
pip install -e ".[web]"
elielsito web                 # http://127.0.0.1:8765
```

- Escucha **solo en tu equipo** (`127.0.0.1`) por defecto.
- No usa CDN ni fuentes externas: funciona sin internet.
- Reutiliza el mismo motor que la CLI (agente, memoria, herramientas).

Detalles y API en [`docs/WEB.md`](docs/WEB.md).

## Configuración

La configuración vive en `~/.elielsito/config.json`. Los **secretos van en `.env`**
o en variables de entorno, nunca en el archivo de configuración.

| Variable | Para qué |
|---|---|
| `ELELSITO_DATA_DIR` | Carpeta de datos (memoria, auditoría) |
| `ELELSITO_MODEL_PROVIDER` | `mock`, `openai`, `anthropic`, `gemini`, `ollama` |
| `ELELSITO_MODEL_NAME` | Nombre del modelo |
| `ELELSITO_MODEL_BASE_URL` | URL base (para servidores compatibles con OpenAI) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | Claves de proveedor |
| `ELELSITO_ALLOW_SHELL` | `1` para permitir herramientas de ejecución |

## Pruebas

```bash
python -m pytest -q
```

## Seguridad

- Permisos mínimos; cada herramienta declara su nivel (`read`, `write`, `network`, `execute`).
- Las operaciones `execute` y `danger` requieren autorización explícita.
- Las herramientas de archivos están **confinadas** a las raíces permitidas.
- Todo uso de herramientas queda registrado en `~/.elielsito/audit.log` (JSONL).
- Límites de pasos y de tiempo para evitar bucles.
- El contenido externo se trata como **datos**, nunca como instrucciones.
