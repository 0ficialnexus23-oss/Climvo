import { AppError } from "@/lib/errors";
import { prisma } from "@/lib/prisma";
import { locationSchema, normalizarUbicacion } from "./schema";
import * as repo from "./repository";

/** Verifica que el cliente pertenezca al tenant antes de crear la ubicación. */
async function asegurarCliente(tenantId: string, customerId: string) {
  const cliente = await prisma.customer.findFirst({
    where: { id: customerId, tenantId },
    select: { id: true },
  });
  if (!cliente) {
    throw new AppError("El cliente no existe o no pertenece a tu empresa.");
  }
}

export async function crearUbicacion(
  tenantId: string,
  customerId: string,
  input: unknown,
) {
  const data = locationSchema.parse(input);
  await asegurarCliente(tenantId, customerId);
  return repo.crearUbicacion(tenantId, customerId, normalizarUbicacion(data));
}

export async function eliminarUbicacion(tenantId: string, id: string) {
  const ubicacion = await prisma.location.findFirst({
    where: { id, tenantId },
    select: { id: true },
  });
  if (!ubicacion) {
    throw new AppError("La ubicación no existe o no pertenece a tu empresa.");
  }
  await repo.eliminarUbicacion(tenantId, id);
}
