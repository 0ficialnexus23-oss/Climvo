import { prisma } from "@/lib/prisma";
import { hashPassword } from "@/lib/password";
import { registroSchema, type RegistroInput } from "./schema";

/** Error de negocio del modulo de autenticacion (mensaje apto para el usuario). */
export class RegistroError extends Error {}

/**
 * Crea una empresa (tenant) y su primer usuario como OWNER en una sola
 * transaccion. Si algo falla, no queda nada a medias.
 */
export async function registrarEmpresa(input: RegistroInput) {
  const data = registroSchema.parse(input);
  const email = data.email.trim().toLowerCase();

  const existente = await prisma.user.findUnique({ where: { email } });
  if (existente) {
    throw new RegistroError("Ya existe una cuenta con ese correo.");
  }

  const passwordHash = await hashPassword(data.password);

  const tenant = await prisma.tenant.create({
    data: {
      name: data.companyName,
      email,
      phone: data.phone || null,
      timezone: "America/Mexico_City",
      users: {
        create: {
          name: data.name,
          email,
          passwordHash,
          role: "OWNER",
          phone: data.phone || null,
        },
      },
    },
    select: { id: true, name: true },
  });

  return tenant;
}
