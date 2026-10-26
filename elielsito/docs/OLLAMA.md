# Elielsito con Ollama — modelo local, gratis y privado

Ollama ejecuta modelos de IA **en tu propio equipo**: sin claves, sin cuotas y
sin enviar tus conversaciones a ningún servidor. Elielsito ya está preparado:
Ollama expone una API compatible con OpenAI en `/v1`, así que no hay que cambiar
nada de código.

## 1. Requisitos

| Requisito | Detalle |
|---|---|
| Sistema | Windows 10/11, macOS (Intel o Apple Silicon) o Linux |
| RAM | El factor decisivo. Ver tabla de modelos |
| Disco | 2–5 GB por modelo de 3B–8B |
| GPU | Opcional. NVIDIA/AMD/Apple Silicon aceleran; con CPU funciona más lento |
| Internet | Solo para descargar Ollama y el modelo; después funciona sin conexión |

## 2. Qué modelo elegir según tu RAM

| RAM total | Modelo recomendado | Descarga aprox. | Velocidad esperada |
|---|---|---|---|
| 8 GB o menos | `qwen2.5:3b` | ~2 GB | Rápida en CPU |
| 8–15 GB | `qwen2.5:7b` / `llama3.1:8b` | ~4–5 GB | Aceptable en CPU, buena con GPU |
| 16–31 GB | `qwen2.5:14b` | ~9 GB | Buena |
| 32 GB o más | `qwen2.5:32b` | ~20 GB | Muy buena (mejor con GPU) |

> Regla práctica: el modelo debe caber en RAM **con margen**. Si tu equipo tiene
> 8 GB, usa 3B; si fuerzas un 7B, el sistema empezará a usar disco y será lento.

## 3. Instalar Ollama

**Windows:** descarga el instalador de <https://ollama.com/download> y ejecútalo.

**macOS:**
```bash
brew install ollama
# o descarga la app desde https://ollama.com/download
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## 4. Descargar el modelo y arrancar

```bash
ollama pull qwen2.5:7b     # cambia el modelo según tu RAM
ollama serve               # suele arrancar solo; deja el servidor activo
```

Comprueba que responde:

```bash
curl http://localhost:11434/api/tags
```

## 5. Configurar Elielsito

La forma recomendada es el script, que **detecta tu RAM y elige el modelo**:

```bash
python scripts/configurar_ollama.py
```

También puedes forzar un modelo concreto:

```bash
python scripts/configurar_ollama.py --model qwen2.5:14b
```

El script escribe `~/.elielsito/config.json` con:

```json
{
  "model": {
    "provider": "ollama",
    "name": "qwen2.5:7b",
    "base_url": "http://localhost:11434/v1"
  }
}
```

### Alternativa con variables de entorno

```bash
# Linux / macOS
export ELELSITO_MODEL_PROVIDER=ollama
export ELELSITO_MODEL_NAME=qwen2.5:7b
export ELELSITO_MODEL_BASE_URL=http://localhost:11434/v1

# Windows (PowerShell)
$env:ELELSITO_MODEL_PROVIDER="ollama"
$env:ELELSITO_MODEL_NAME="qwen2.5:7b"
$env:ELELSITO_MODEL_BASE_URL="http://localhost:11434/v1"
```

## 6. Verificar

```bash
python scripts/configurar_ollama.py --check   # ¿responde Ollama?
python scripts/verificar_ollama.py            # comprobación completa (4 puntos)
elielsito doctor                             # configuración y estado
elielsito chat -m "Hola Elielsito"           # primera conversación real
elielsito chat                               # modo interactivo
```

`verificar_ollama.py` comprueba, en orden: que la configuración apunte a Ollama,
que el servidor responda, que el modelo esté descargado y que el modelo conteste
de verdad. Si algo falla, imprime la orden exacta para resolverlo.

## 7. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Connection refused` en `:11434` | Ollama no está corriendo | `ollama serve` |
| `model not found` | El modelo no está descargado | `ollama pull <modelo>` |
| Respuestas muy lentas | Modelo demasiado grande para tu RAM/CPU | Usa un modelo menor (3B) |
| Se queda sin memoria | Modelo no cabe | Baja a 3B o 7B |
| `doctor` muestra otro proveedor | Variables de entorno pisan la config | Revisa `ELELSITO_MODEL_PROVIDER` |

## 8. Privacidad y costo

- **Costo: 0.** No hay clave ni suscripción.
- **Privacidad:** todo se procesa en tu equipo. Nada sale a internet.
- **Offline:** tras descargar el modelo, funciona sin conexión.

## 9. Cambiar de modelo más adelante

```bash
ollama pull llama3.1:8b
python scripts/configurar_ollama.py --model llama3.1:8b
```

O edita `~/.elielsito/config.json`. No hace falta tocar código: el adaptador es
intercambiable.

## 10. Límites honestos

Un modelo local de 3B–14B **no** es comparable a los modelos por API en
razonamiento complejo. Es excelente para conversación, resúmenes, redacción,
ayuda con código y tareas guiadas; para problemas muy complejos, un modelo mayor
(o una API) rendirá mejor. Elielsito no oculta esta diferencia: te dirá cuándo
algo supera su capacidad.
