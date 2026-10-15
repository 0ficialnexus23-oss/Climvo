import { hash, compare } from "bcryptjs";

const ROUNDS = 12;

/** Genera el hash de una contrasena. Nunca se guarda la contrasena en claro. */
export function hashPassword(plain: string): Promise<string> {
  return hash(plain, ROUNDS);
}

/** Compara una contrasena en claro contra su hash. */
export function verifyPassword(plain: string, passwordHash: string): Promise<boolean> {
  return compare(plain, passwordHash);
}
