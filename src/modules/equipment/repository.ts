import { prisma } from "@/lib/prisma";

export type EquipoData = {
  customerId: string;
  locationId: string | null;
  type: string;
  brand: string | null;
  model: string | null;
  serialNumber: string | null;
  capacityTr: number | null;
  refrigerant: string | null;
  installDate: Date | null;
  warrantyUntil: Date | null;
  notes: string | null;
};

export function listarEquipos(tenantId: string, q?: string) {
  const filtro = q
    ? {
        OR: [
          { type: { contains: q, mode: "insensitive" as const } },
          { brand: { contains: q, mode: "insensitive" as const } },
          { model: { contains: q, mode: "insensitive" as const } },
          { serialNumber: { contains: q, mode: "insensitive" as const } },
          { customer: { name: { contains: q, mode: "insensitive" as const } } },
        ],
      }
    : {};

  return prisma.equipment.findMany({
    where: { tenantId, ...filtro },
    orderBy: { createdAt: "desc" },
    include: {
      customer: { select: { id: true, name: true } },
      location: { select: { id: true, name: true } },
    },
  });
}

export function obtenerEquipo(tenantId: string, id: string) {
  return prisma.equipment.findFirst({
    where: { id, tenantId },
    include: {
      customer: { select: { id: true, name: true } },
      location: { select: { id: true, name: true } },
    },
  });
}

export function crearEquipo(
  tenantId: string,
  data: EquipoData,
  qrToken: string,
) {
  return prisma.equipment.create({ data: { tenantId, ...data, qrToken } });
}

export function actualizarEquipo(
  tenantId: string,
  id: string,
  data: EquipoData,
) {
  return prisma.equipment.updateMany({ where: { id, tenantId }, data });
}

export function eliminarEquipo(tenantId: string, id: string) {
  return prisma.equipment.deleteMany({ where: { id, tenantId } });
}

export function contarEquipos(tenantId: string) {
  return prisma.equipment.count({ where: { tenantId } });
}
