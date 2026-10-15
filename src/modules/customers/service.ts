import { AppError } from "@/lib/errors";
import { customerSchema, normalizarCliente } from "./schema";
import * as repo from "./repository";

export async function crearCliente(tenantId: string, input: unknown) {
  const data = customerSchema.parse(input);
  return repo.crearCliente(tenantId, normalizarCliente(data));
}

export async function actualizarCliente(
  tenantId: string,
  id: string,
  input: unknown,
) {
  const data = customerSchema.parse(input);
  const existente = await repo.obtenerCliente(tenantId, id);
  if (!existente) throw new AppError("El cliente no existe o no pertenece a tu empresa.");

  await repo.actualizarCliente(tenantId, id, normalizarCliente(data));
  return { id };
}

export async function eliminarCliente(tenantId: string, id: string) {
  const existente = await repo.obtenerCliente(tenantId, id);
  if (!existente) throw new AppError("El cliente no existe o no pertenece a tu empresa.");
  await repo.eliminarCliente(tenantId, id);
}
