# Climvo

**Micro-FSM WhatsApp-first para empresas de mantenimiento de aire acondicionado y refrigeración (HVAC) en México.**

> El sistema que convierte tu WhatsApp desordenado en contratos de mantenimiento que no se pierden.

Climvo ayuda a empresas HVAC de 2 a 10 técnicos a gestionar clientes, equipos, solicitudes, presupuestos, agenda, órdenes de servicio, evidencia, reportes y cobros — sin dejar Excel, papel ni WhatsApp.

## Estado

**Fase 0 — Setup.** Proyecto en construcción. Este repositorio todavía no contiene funcionalidad operativa.

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
