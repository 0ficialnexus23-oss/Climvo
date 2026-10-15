import { PrismaClient } from "@prisma/client";

/**
 * Cliente Prisma singleton.
 * En desarrollo, Next.js recarga los módulos en caliente; sin este patrón
 * se crearian multiples conexiones a la base de datos.
 */
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
