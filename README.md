# Climvo

**Micro-FSM WhatsApp-first para empresas de mantenimiento de aire acondicionado y refrigeración (HVAC) en México.**

> El sistema que convierte tu WhatsApp desordenado en contratos de mantenimiento que no se pierden.

Climvo ayuda a empresas HVAC de 2 a 10 técnicos a gestionar clientes, equipos, solicitudes, presupuestos, agenda, órdenes de servicio, evidencia, reportes y cobros — sin dejar Excel, papel ni WhatsApp.

## Estado

**Fase 1 — Núcleo operativo (terminada y probada).**

Ya funciona:

- Autenticación: registro de empresa, inicio y cierre de sesión, sesión en cookie `httpOnly`.
- Roles de usuario: `OWNER`, `OFFICE`, `TECH`.
- Aislamiento multi-tenant verificado en todas las consultas (probado con dos empresas).
- **Clientes**: alta, edición, eliminación, búsqueda y ficha con historial.
- **Ubicaciones** por cliente.
- **Equipos**: ficha técnica (marca, modelo, serie, capacidad, refrigerante, garantía), código QR e historial de mantenimiento.

En construcción: solicitudes, presupuestos, agenda, órdenes de servicio, evidencia, reportes, mantenimiento preventivo y cobros.

### Pruebas

El proyecto incluye comprobaciones automáticas del núcleo en `scripts/`:

```bash
npx tsx scripts/test-registro.ts   # registro, hash y validaciones
npx tsx scripts/test-fase1.ts      # CRUD y aislamiento entre empresas
```

## Flujo central del producto

```
Solicitud → Presupuesto → Aprobación → Agenda → Orden de servicio
          → Evidencia → Reporte → Cobro → Próximo mantenimiento
```

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend + Backend | Next.js 15 (App Router) + TypeScript |
| UI | Tailwind CSS v4 + shadcn/ui |
| Base de datos | PostgreSQL |
| ORM | Prisma |
| Autenticación | Auth.js (NextAuth v5) — credenciales |
| Validación | Zod + react-hook-form |
| PDF | @react-pdf/renderer |
| Hosting (previsto) | Vercel + Neon/Supabase |

## Estructura

```
src/
  app/            Rutas, layouts y server actions
  modules/        Dominio por funcionalidad (customers, equipment, quotes, work-orders…)
  components/     UI compartida
  lib/            db, auth, storage, pdf, messaging, validation
prisma/
  schema.prisma   Modelo de datos
docs/             Documentación de arquitectura y producto
```

## Puesta en marcha (desarrollo)

Requisitos: Node.js 20+, PostgreSQL 15+.

```bash
npm install
cp .env.example .env      # completa las variables
npx prisma migrate dev    # crea el esquema en tu base de datos
npm run dev
```

## Seguridad

- Los secretos **nunca** se versionan. Usa `.env` (ignorado por git) y `.env.example` como plantilla.
- Todas las consultas están aisladas por `tenantId` (multi-tenant).
- Validación de entrada con Zod en cliente y servidor.

## Documentación

- [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) — decisiones técnicas y modelo de datos.
- [`docs/PLAN-FASE-1.md`](docs/PLAN-FASE-1.md) — alcance del MVP y plan de construcción.

## Licencia

Privado y propietario. Todos los derechos reservados.
