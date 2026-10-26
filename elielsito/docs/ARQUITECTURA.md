# Arquitectura de Elielsito AI

Documento vivo. Recoge las decisiones técnicas, su justificación y el estado real
de cada etapa.

## 1. Principios

1. **Modular de verdad.** El modelo de IA es una pieza intercambiable; cambiar de
   proveedor no debe obligar a tocar memoria, herramientas ni planificador.
2. **Local primero, gratis primero.** Debe funcionar sin pagar nada (modelo local o
   modo simulado) y solo usar servicios de pago si el usuario lo autoriza.
3. **Nada sin evidencia.** Cada módulo se prueba. Se distingue entre implementado,
   probado, parcial y pendiente.
4. **Seguridad por diseño.** Permisos mínimos, confinamiento de rutas, auditoría y
   límites de ejecución.
5. **Sin dependencias innecesarias.** El núcleo usa solo la biblioteca estándar de
   Python, para que sea fácil de instalar y de auditar.

## 2. Stack y justificación

| Capa | Elección | Motivo |
|------|----------|--------|
| Lenguaje | **Python 3.11+** | Ecosistema de IA, voz y automatización; legible y multiplataforma |
| Persistencia | **SQLite** (biblioteca estándar) | Un solo archivo, sin servidor, con FTS5 para búsqueda; portable |
| HTTP | **`urllib`** (estándar) | Cero dependencias en el núcleo |
| Modelo de IA | **Adaptador intercambiable** | OpenAI-compatible (OpenAI, Ollama, LM Studio), Anthropic, Gemini y `mock` |
| CLI | **`argparse`** (estándar) | Sin dependencias; base para la interfaz web futura |
| Pruebas | **pytest** | Estándar del ecosistema (única dependencia de desarrollo) |

**Descartado por ahora y por qué:**
- **Framework de agentes externo (LangChain y similares):** añade peso y capas de
  abstracción que ocultan el control de seguridad. El bucle del agente aquí es
  explícito y auditable.
- **Base de datos con servidor (Postgres):** innecesaria para un asistente personal;
  añade instalación y mantenimiento.
- **Modelo propio entrenado desde cero:** no es viable ni necesario. Se usa un
  modelo existente. El sistema está preparado para *ajustar* o *conectar* modelos
  en el futuro, no para entrenar uno fundacional.

## 3. Módulos

```
elielsito/
  config.py        Configuración (JSON) + variables de entorno. Sin secretos.
  identity.py      Identidad, personalidad y reglas de honestidad/seguridad.
  audit.py         Registro de auditoría en JSONL (añadir sin reescribir).
  http.py          Cliente HTTP mínimo (stdlib).
  core.py          Bucle del agente: conversación + herramientas + límites.
  cli.py           Interfaz de línea de comandos.
  models/
    base.py              Contrato: Message, ToolCall, ModelResponse, ModelAdapter.
    mock.py              Simulador (pruebas sin coste ni internet).
    openai_compatible.py OpenAI y servidores locales compatibles.
    anthropic.py         Claude (implementado, sin probar contra el servicio).
    gemini.py            Google Gemini (implementado, sin probar contra el servicio).
    factory.py           Configuración -> adaptador concreto.
  memory/
    store.py       Memoria SQLite: categorías, FTS5, deduplicación, respaldo.
  tools/
    base.py        Contrato de herramienta + validación de argumentos.
    registry.py    Registro: permisos, aprobación, auditoría.
    filesystem.py  Archivos confinados a raíces permitidas.
    memory_tools.py Guardar y buscar en la memoria.
tests/            58 pruebas automatizadas.
```

## 4. Flujo de una conversación

```
mensaje del usuario
   │
   ├─ buscar memoria relevante ──> se inyecta en el mensaje de sistema
   │
   ├─ construir mensajes (sistema + historial + usuario)
   │
   └─ bucle (máx. max_steps, máx. max_seconds):
         modelo.complete(...)
           ├─ ¿pide herramientas? → registry.execute(...)  [valida + permisos + audita]
           │                        └─ resultado vuelve al modelo
           └─ ¿respuesta final? → devolver
```

## 5. Modelo de seguridad

| Control | Implementación |
|---------|----------------|
| Permisos por herramienta | `read` / `write` / `network` / `execute` / `danger` |
| Autorización previa | `safety.require_approval` (por defecto `execute` y `danger`) |
| Shell desactivado por defecto | `ELELSITO_ALLOW_SHELL=0` |
| Confinamiento de archivos | `resolve_safe()` comprueba que la ruta esté dentro de las raíces |
| Validación de argumentos | Esquema JSON por herramienta |
| Límites de ejecución | `max_steps` y `max_seconds` |
| Auditoría | Todo uso de herramienta se registra en `audit.log` |
| Secretos | Nunca se guardan en memoria (`looks_secret`) ni en la configuración |
| Contenido externo | Se trata como datos, nunca como instrucciones |

## 6. Estado real por etapa

| Etapa | Estado | Nota |
|-------|--------|------|
| 1. Análisis de entorno | ✅ Hecho | Sandbox: 2 vCPU, 1,9 GB RAM, sin GPU, sin audio |
| 2. Núcleo + configuración | ✅ Implementado y probado | `config.py`, `core.py`, `cli.py` |
| 3. Modelo de IA + conversación | ✅ Implementado y probado (mock) · ⚠️ APIs sin probar contra el servicio | Falta clave |
| 4. Memoria persistente | ✅ Implementado y probado | SQLite + FTS5 |
| 5. Voz y activación | ⛔ No implementado | Requiere tu equipo (aquí no hay audio) |
| 6. Navegación web | ⛔ No implementado | Etapa siguiente prevista |
| 7. Control del ordenador | ⚠️ Parcial | Archivos sí; shell diseñado pero desactivado |
| 8. Planificación de tareas | ⚠️ Parcial | El bucle tiene pasos y trazas; falta el planificador con estados |
| 9. Habilidades modulares | ⛔ No implementado | Diseño previsto |
| 10. Aprendizaje continuo | ⛔ No implementado | — |
| 11. Automejora | ⛔ No implementado | — |
| 12. Interfaz visual | ⛔ No implementado | Solo CLI |
| 13. Pruebas de integración | ⚠️ Parcial | 58 pruebas unitarias; falta integración completa |

## 7. Decisiones pendientes del usuario

1. **Sistema operativo y hardware de tu computadora** (Windows/macOS/Linux, RAM,
   GPU). Determina si conviene un modelo local y qué motor de voz usar.
2. **Modelo de IA:** local (gratis, requiere hardware) o por API (de pago, requiere
   clave). Por ahora funciona en modo simulado.
3. **Dónde alojar el proyecto:** ¿repositorio privado en GitHub como Climvo?

## 8. Próximos hitos propuestos

1. **Planificador de tareas** con estados (pendiente, en ejecución, verificando,
   completada, bloqueada, fallida) y persistencia.
2. **Navegación web** con `httpx` + extracción de contenido y guardado de fuentes.
3. **Herramientas de ejecución** con lista blanca y confirmación.
4. **Voz** (reconocimiento y síntesis) en tu equipo.
5. **Interfaz web local** para ver estado, tareas, memoria y autorizaciones.
