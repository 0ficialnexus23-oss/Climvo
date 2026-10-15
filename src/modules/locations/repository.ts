import { prisma } from "@/lib/prisma";

export function listarUbicaciones(tenantId: string, customerId: string) {
  return prisma.location.findMany({
    where: { tenantId, customerId },
    orderBy: { name: "asc" },
  });
}

export function crearUbicacion(
  tenantId: string,
  customerId: string,
  data: {
    name: string;
    address: string | null;
    city: string | null;
    state: string | null;
    zip: string | null;
    contactName: string | null;
    phone: string | null;
    notes: string | null;
  },
) {
  return prisma.location.create({
    data: { tenantId, customerId, ...data },
  });
}

export function eliminarUbicacion(tenantId: string, id: string) {
  return prisma.location.deleteMany({ where: { id, tenantId } });
}

export function listarOpcionesUbicaciones(tenantId: string) {
  return prisma.location.findMany({
    where: { tenantId },
    select: { id: true, name: true, customerId: true },
    orderBy: { name: "asc" },
  });
}
