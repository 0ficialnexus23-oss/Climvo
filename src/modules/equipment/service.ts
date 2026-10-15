import { randomBytes } from "node:crypto";

import { AppError } from "@/lib/errors";
import { prisma } from "@/lib/prisma";
import {
  equipmentSchema,
  parseFecha,
  parseNumero,
  type EquipmentInput,
} from "./schema";
import * as repo from "./repository";

async function asegurarCliente(tenantId: string, customerId: string) {
  const cliente = await prisma.customer.findFirst({
    where: { id: customerId, tenantId },
    select: { id: true },
  });
  if (!cliente) {
    throw new AppError("El cliente no existe o no pertenece a tu empresa.");
  }
}

async function asegurarUbicacion(
  tenantId: string,
  customerId: string,
  locationId: string,
) {
  const ubicacion = await prisma.location.findFirst({
    where: { id: locationId, tenantId, customerId },
    select: { id: true },
  });
  if (!ubicacion) {
    throw new AppError("La ubicación seleccionada no pertenece a este cliente.");
  }
}

function normalizar(data: EquipmentInput): repo.EquipoData {
  return {
    customerId: data.customerId,
    locationId: data.locationId || null,
    type: data.type,
    brand: data.brand || null,
    model: data.model || null,
    serialNumber: data.serialNumber || null,
    capacityTr: parseNumero(data.capacityTr),
    refrigerant: data.refrigerant || null,
    installDate: parseFecha(data.installDate),
    warrantyUntil: parseFecha(data.warrantyUntil),
    notes: data.notes || null,
  };
}

export async function crearEquipo(tenantId: string, input: unknown) {
  const data = equipmentSchema.parse(input);
  await asegurarCliente(tenantId, data.customerId);
  if (data.locationId) {
    await asegurarUbicacion(tenantId, data.customerId, data.locationId);
  }

  const qrToken = randomBytes(12).toString("hex");
  return repo.crearEquipo(tenantId, normalizar(data), qrToken);
}

export async function actualizarEquipo(
  tenantId: string,
  id: string,
  input: unknown,
) {
  const data = equipmentSchema.parse(input);
  const existente = await repo.obtenerEquipo(tenantId, id);
  if (!existente) {
    throw new AppError("El equipo no existe o no pertenece a tu empresa.");
  }
  await asegurarCliente(tenantId, data.customerId);
  if (data.locationId) {
    await asegurarUbicacion(tenantId, data.customerId, data.locationId);
  }

  await repo.actualizarEquipo(tenantId, id, normalizar(data));
  return { id };
}

export async function eliminarEquipo(tenantId: string, id: string) {
  const existente = await repo.obtenerEquipo(tenantId, id);
  if (!existente) {
    throw new AppError("El equipo no existe o no pertenece a tu empresa.");
  }
  await repo.eliminarEquipo(tenantId, id);
}
