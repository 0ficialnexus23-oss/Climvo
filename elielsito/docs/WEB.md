# Interfaz web de Elielsito

Servidor local con **FastAPI** y una interfaz en **HTML, CSS y JavaScript** sin
dependencias externas. Reutiliza el mismo motor que la CLI: no hay dos cerebros.

## Arrancar

```bash
pip install -e ".[web]"
elielsito web                  # http://127.0.0.1:8765
elielsito web --port 9000      # otro puerto
```

> `--host 0.0.0.0` expone Elielsito a tu red local. No lo uses salvo que sepas
> lo que haces: **no hay autenticación** en esta etapa.

## Qué incluye

| Sección | Contenido |
|---|---|
| **Chat** | Conversación con historial, indicador de escritura, botón **Detener**, traza de herramientas |
| **Herramientas** | Lista real con su nivel de permiso (`read`, `write`, `execute`…) |
| **Memoria** | Listar, buscar, añadir (hecho/hipótesis, categoría) y eliminar |
| **Auditoría** | Últimos eventos del sistema, con resultado y duración |
| **Estado** | Identidad, proveedor, modelo, límites, shell y número de recuerdos |

En móvil, la barra lateral se convierte en navegación inferior.

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Interfaz |
| GET | `/health` | Comprobación de vida |
| GET | `/api/status` | Configuración y estado |
| GET | `/api/tools` | Herramientas registradas |
| POST | `/api/chat` | `{message, history[]}` → respuesta del agente |
| GET | `/api/memory?q=&category=&limit=` | Listar o buscar |
| POST | `/api/memory` | `{content, category, kind, source}` |
| DELETE | `/api/memory/{id}` | Eliminar un recuerdo |
| GET | `/api/audit?limit=` | Últimos eventos |

Ejemplo:

```bash
curl -X POST http://127.0.0.1:8765/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hola Elielsito"}'
```

## Seguridad

- Escucha en `127.0.0.1` por defecto.
- Las herramientas con permiso `execute` o `danger` se **deniegan** desde la web
  (la aprobación interactiva llegar\u00e1 en una etapa posterior).
- El confinamiento de rutas y la auditoría son los mismos que en la CLI.
- El texto del modelo se inserta con `textContent`, nunca con `innerHTML`:
  no se interpreta como HTML.

## Pruebas

```bash
python -m pytest tests/test_web.py -q
```

Cubren: página, estáticos, estado, herramientas, chat, validación, memoria
(alta/búsqueda/borrado), rechazo de secretos y auditoría.
