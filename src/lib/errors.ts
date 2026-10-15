import { ZodError } from "zod";

/** Error de negocio con mensaje apto para mostrar al usuario. */
export class AppError extends Error {}

/**
 * Convierte cualquier error en un mensaje seguro para el usuario.
 * Los errores inesperados se registran en consola y se ocultan.
 */
export function toUserMessage(
  error: unknown,
  fallback = "No se pudo completar la operación. Intenta de nuevo.",
): string {
  if (error instanceof AppError) return error.message;
  if (error instanceof ZodError) {
    return error.issues[0]?.message ?? fallback;
  }
  console.error(error);
  return fallback;
}
