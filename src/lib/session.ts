import { redirect } from "next/navigation";
import type { UserRole } from "@prisma/client";

import { auth } from "@/lib/auth";

/**
 * Devuelve la sesion actual o null.
 * Nota: la sesion NO es una fuente de verdad para permisos finos;
 * el tenantId y el rol se verifican siempre en la capa de servicio.
 */
export async function getSession() {
  return auth();
}

/** Exige sesion activa. Redirige a /login si no hay. */
export async function requireSession() {
  const session = await auth();
  if (!session?.user?.id || !session.user.tenantId) {
    redirect("/login");
  }
  return session;
}

/** Exige sesion activa y uno de los roles indicados. */
export async function requireRole(roles: UserRole[]) {
  const session = await requireSession();
  if (!roles.includes(session.user.role)) {
    redirect("/hoy");
  }
  return session;
}
