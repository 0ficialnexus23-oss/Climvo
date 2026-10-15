import { z } from "zod";

/**
 * Validacion de variables de entorno al arranque.
 * Falla rapido si falta algo critico, en lugar de fallar en tiempo de ejecucion.
 */
const envSchema = z.object({
  NODE_ENV: z
    .enum(["development", "test", "production"])
    .default("development"),
  DATABASE_URL: z.string().url(),
  AUTH_SECRET: z.string().min(32, "AUTH_SECRET debe tener al menos 32 caracteres"),
  NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:3000"),
  STORAGE_DRIVER: z.enum(["local", "s3"]).default("local"),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error(
    "Variables de entorno invalidas:",
    parsed.error.flatten().fieldErrors,
  );
  throw new Error("Configuracion de entorno invalida");
}

export const env = parsed.data;
