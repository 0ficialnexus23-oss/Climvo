# Arquitectura — Climvo

Documento vivo. Recoge las decisiones técnicas del proyecto y su justificación.

## Principios

1. **Simplicidad radical.** El usuario objetivo (dueño o técnico de una empresa HVAC de 2–10 personas) no es ofimático. Si una pantalla no se entiende en 10 segundos, está mal.
2. **Mobile-first.** El trabajo ocurre en campo, desde el móvil.
3. **WhatsApp como ciudadano de primera.** El producto convive con WhatsApp; no exige migrar de él.
4. **Multi-tenant seguro.** Toda consulta está aislada por `tenantId`.
5. **Nada de funcionalidad especulativa.** Solo se construye lo que resuelve el flujo central.

## Stack

| Capa | Elección | Motivo |
|------|----------|--------|
| Framework | Next.js 15 (App Router) | Un solo lenguaje, SSR/RSC, server actions, mobile-first |
| Lenguaje | TypeScript (strict) | Seguridad de tipos de extremo a extremo |
| UI | Tailwind CSS v4 + shadcn/ui | Accesible, rápido, sin diseño desde cero |
| Base de datos | PostgreSQL | Relacional, integridad referencial |
| ORM | Prisma | Migraciones, tipado, DX |
| Auth | Auth.js (NextAuth v5) + credenciales | Sesión en cookie httpOnly, CSRF integrado |
| Validación | Zod | Esquema único compartido cliente/servidor |
| PDF | @react-pdf/renderer | Genera PDF sin navegador headless (apto para serverless) |
| Hosting previsto | Vercel + Neon/Supabase | Free tier suficiente para el MVP |

### Decisiones y alternativas descartadas

- **Supabase como backend integrado:** se descartó por acoplamiento; se prefiere un Postgres gestionado + Prisma, que es portable.
- **NextAuth v5 está en beta:** se acepta porque es el estándar del ecosistema y resuelve CSRF y sesiones con seguridad probada. Alternativa considerada: implementación propia con sesiones en base de datos.
- **bcryptjs en lugar de argon2:** `bcryptjs` es JavaScript puro, sin compilación nativa, lo que evita problemas de build en serverless. Es una elección de portabilidad, no de máxima seguridad; si más adelante se migra a un entorno con binarios nativos, se puede cambiar a argon2id.

## Capas

```
UI (app/ + components/)
      │  server actions / route handlers
      ▼
Servicio (modules/<feature>/service.ts)   ← reglas de negocio + autorización
      ▼
Repositorio (modules/<feature>/repository.ts)
      ▼
Prisma (lib/prisma.ts)
      ▼
PostgreSQL
```

**Regla:** ninguna consulta a base de datos desde un componente de UI. Toda la lógica de negocio vive en la capa de servicio.

## Multi-tenancy

- Cada tabla de negocio tiene `tenantId`.
- La capa de servicio recibe siempre el `tenantId` de la sesión y lo incluye en cada `where`.
- **Nunca** se confía en un `tenantId` enviado por el cliente.
- Postgres Row-Level Security se puede añadir después como defensa en profundidad.

## Modelo de datos

Entidades principales y relaciones:

```
Tenant 1─N User
Tenant 1─N Customer
Customer 1─N Location
Customer 1─N Equipment
Location 1─N Equipment
Customer 1─N ServiceRequest
ServiceRequest 1─0..1 Quote
Quote 1─N QuoteItem
Quote 1─0..1 Appointment
Appointment 1─0..1 WorkOrder
WorkOrder 1─N WorkOrderTask
WorkOrder 1─N Attachment
Equipment 1─N MaintenancePlan
WorkOrder 1─0..1 Payment
WorkOrder 1─0..1 ServiceReport (PDF generado bajo demanda)
```

El esquema completo está en [`prisma/schema.prisma`](../prisma/schema.prisma).

## Roles

| Rol | Permisos |
|-----|----------|
| `OWNER` | Todo, incluida gestión de usuarios y suscripción |
| `OFFICE` | Operación completa; sin gestión de usuarios |
| `TECH` | Solo sus citas y órdenes; sube evidencia y firma |

## Estrategia de WhatsApp

- **MVP:** deep links `wa.me` con mensajes pre-rellenados (coste cero, sin API, compatible con la app gratuita).
- **Fase 2:** WhatsApp Cloud API de Meta (requiere verificación, número propio, plantillas aprobadas y tiene coste por mensaje).
- El dominio usa una abstracción `MessagingProvider` para no reescribir lógica al cambiar de proveedor. Todo envío se registra en `MessageLog`.

## Estrategia de pagos

- **MVP:** seguimiento manual de estado (pendiente / parcial / pagado) y recibo en PDF.
- **Fase 2:** pasarela con abstracción `PaymentProvider` (Mercado Pago como candidato principal para México).

## Riesgos técnicos conocidos

| Riesgo | Mitigación |
|--------|-----------|
| Fuga de datos entre tenants | `tenantId` obligatorio + verificación en servicio + pruebas |
| Coste de WhatsApp API | Deep links en el MVP; API solo con ingresos |
| Facturación CFDI/SAT | Fuera del MVP; integración con PAC en el futuro |
| Adopción por usuarios no técnicos | UX móvil, onboarding de una tarde |
| Fotos pesadas | Compresión en cliente + almacenamiento de objetos |
| Falta de señal en sitio | UI optimista + cola de subida; offline completo después |
| PDF en serverless | `@react-pdf/renderer` (sin navegador) |
