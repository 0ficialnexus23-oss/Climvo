# Plan Fase 1 — Alcance y construcción

## Propuesta de valor

> El sistema que convierte tu WhatsApp desordenado en contratos de mantenimiento que no se pierden.

## Cliente ideal (ICP)

Empresa HVAC en México, de 2 a 10 técnicos, que atiende clientes residenciales y comerciales y tiene (o quiere tener) contratos de mantenimiento preventivo.

## Flujo central

```
Solicitud → Presupuesto → Aprobación → Agenda → Orden de servicio
          → Evidencia → Reporte → Cobro → Próximo mantenimiento
```

## Alcance del MVP

| # | Módulo | Incluye |
|---|--------|---------|
| 1 | Auth + Empresa | Registro de empresa, login, usuarios con roles |
| 2 | Clientes | CRUD, contacto, tipo, N ubicaciones |
| 3 | Equipos | Ficha técnica + QR |
| 4 | Solicitudes | Alta, prioridad, estado |
| 5 | Presupuestos | Partidas, totales, envío por WhatsApp, aprobación |
| 6 | Agenda | Vista día/semana, asignación de técnico |
| 7 | Órdenes de servicio | Checklist, mediciones, fotos, firma |
| 8 | Reporte técnico | PDF para el cliente |
| 9 | Preventivo | Planes recurrentes + próximos/vencidos |
| 10 | Cobros | Estado manual + recibo |
| 11 | WhatsApp | Deep links `wa.me` con plantillas |
| 12 | Panel "Hoy" | Citas, presupuestos, vencidos, impagos |

## Fuera del MVP

WhatsApp Cloud API automatizada · pasarela de pagos real · facturación CFDI/SAT · inventario y refacciones · rutas/GPS · portal del cliente · analítica avanzada · modo offline completo · PMOC/RETSIT formales · app nativa.

## Criterio de éxito

Una empresa real gestiona de punta a punta una solicitud y su mantenimiento preventivo durante **30 días sin volver a Excel**.

## Plan de construcción

| Fase | Entregable | Estimación |
|------|-----------|-----------|
| 0. Setup | Repo, Next.js, Prisma, Tailwind, CI, `.env.example`, estructura | 1–2 días |
| 1. Núcleo | Auth + tenant + roles + Clientes + Ubicaciones + Equipos + QR | 1 semana |
| 2. Comercial | Solicitudes + Presupuestos + PDF + aprobación | 1 semana |
| 3. Operación | Agenda + Órdenes + checklist + evidencia + firma | 1,5 semanas |
| 4. Preventivo | Planes de mantenimiento + recurrencia + reportes PDF | 1 semana |
| 5. Comunicación | WhatsApp deep links + plantillas + Cobros + recibos | 3–4 días |
| 6. Cierre | Panel "Hoy" + pulido UX + pruebas + staging | 1 semana |

**Total estimado: 6–7 semanas de trabajo efectivo.**

## Metodología

- Ramas por funcionalidad, PRs revisables, `main` siempre desplegable.
- Commits atómicos y descriptivos.
- Sin secretos en el repositorio: `.env.example` + `.gitignore`.
- Nada se declara terminado si no está implementado y probado.

## Decisiones pendientes de autorización

- Conexión de servicios externos distintos de GitHub (hosting, base de datos gestionada, email, almacenamiento): se pedirá autorización antes de contratar nada.
- Despliegue público: requiere autorización explícita.
