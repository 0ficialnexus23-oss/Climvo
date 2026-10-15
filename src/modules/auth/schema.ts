import { z } from "zod";

export const registroSchema = z.object({
  companyName: z
    .string()
    .trim()
    .min(2, "Escribe el nombre de tu empresa")
    .max(120, "El nombre es demasiado largo"),
  name: z
    .string()
    .trim()
    .min(2, "Escribe tu nombre")
    .max(120, "El nombre es demasiado largo"),
  email: z.string().trim().toLowerCase().email("Escribe un correo valido"),
  password: z
    .string()
    .min(8, "La contrasena debe tener al menos 8 caracteres")
    .max(100, "La contrasena es demasiado larga"),
  phone: z.string().trim().max(30, "El telefono es demasiado largo").optional(),
});

export const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email("Escribe un correo valido"),
  password: z.string().min(1, "Escribe tu contrasena"),
});

export type RegistroInput = z.infer<typeof registroSchema>;
export type LoginInput = z.infer<typeof loginSchema>;
