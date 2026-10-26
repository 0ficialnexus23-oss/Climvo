# Primera vez: de cero a tu primera conversación

Checklist para ejecutar **en tu computadora**. Sustituye las rutas por las tuyas.

## 0. Requisitos

- Python 3.11 o superior (`python --version`)
- Ollama instalado y el modelo descargado (`ollama list`)

## 1. Entrar al proyecto y crear el entorno

**Windows (PowerShell)**
```powershell
cd C:\ruta\a\elielsito
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

**macOS / Linux**
```bash
cd ~/ruta/a/elielsito
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

> Si PowerShell bloquea la activación:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## 2. Configurar el modelo según tu RAM

```bash
python scripts/configurar_ollama.py
```

Detecta tu sistema y tu RAM, elige el modelo y escribe `~/.elielsito/config.json`.
Si quieres forzar otro modelo: `--model qwen2.5:14b`.

## 3. Verificar (4 comprobaciones)

```bash
python scripts/verificar_ollama.py
```

Salida esperada:

```
  [OK   ] Configuración apunta a Ollama
  [OK   ] Servidor Ollama responde
  [OK   ] Modelo 'qwen2.5:7b' descargado
  [OK   ] Respuesta real del modelo
```

Si algo falla, el script imprime **la orden exacta** para resolverlo.

## 4. Primera conversación

```bash
elielsito chat -m "Hola Elielsito, ¿estás listo?"
```

O en modo interactivo (escribe `salir` para terminar):

```bash
elielsito chat
```

> Si el comando `elielsito` no se reconoce, usa `python -m elielsito.cli chat`.

## 5. Comprobar que la memoria persiste

```bash
elielsito memory add "Me llamo Eliel y prefiero respuestas directas" --category personal
elielsito memory list
elielsito chat -m "¿Cómo me llamo?"
```

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `Connection refused` en `:11434` | `ollama serve` en otra terminal |
| `model not found` | `ollama pull <modelo>` |
| `provider = mock` en la verificación | `python scripts/configurar_ollama.py` |
| `elielsito: command not found` | `python -m elielsito.cli ...` |
| Respuestas lentas | Usa un modelo menor (3B) |
| Se queda sin memoria | El modelo no cabe en tu RAM |
