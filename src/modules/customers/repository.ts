import { prisma } from "@/lib/prisma";

export type ClienteData = {
  name: string;
  type: "RESIDENTIAL" | "COMMERCIAL" | "INDUSTRIAL";
  contactName: string | null;
  phone: string | null;
  email: string | null;
  notes: string | null;
};

export function listarClientes(tenantId: string, q?: string) {
  const filtro = q
    ? {
        OR: [
          { name: { contains: q, mode: "insensitive" as const } },
          { contactName: { contains: q, mode: "insensitive" as const } },
          { phone: { contains: q } },
        ],
      }
    : {};

  return prisma.customer.findMany({
    where: { tenantId, ...filtro },
    orderBy: { name: "asc" },
    include: { _count: { select: { equipment: true, locations: true } } },
  });
}

export function obtenerCliente(tenantId: string, id: string) {
  return prisma.customer.findFirst({
    where: { id, tenantId },
    include: {
      locations: { orderBy: { name: "asc" } },
      equipment: {
        orderBy: { createdAt: "desc" },
        include: { location: true },
      },
    },
  });
}

export function crearCliente(tenantId: string, data: ClienteData) {
  return prisma.customer.create({ data: { tenantId, ...data } });
}

export function actualizarCliente(
  tenantId: string,
  id: string,
  data: ClienteData,
) {
  return prisma.customer.updateMany({ where: { id, tenantId }, data });
}

export function eliminarCliente(tenantId: string, id: string) {
  return prisma.customer.deleteMany({ where: { id, tenantId } });
}

export function contarClientes(tenantId: string) {
  return prisma.customer.count({ where: { tenantId } });
}

export function listarOpcionesClientes(tenantId: string) {
  return prisma.customer.findMany({
    where: { tenantId },
    select: { id: true, name: true },
    orderBy: { name: "asc" },
  });
}
