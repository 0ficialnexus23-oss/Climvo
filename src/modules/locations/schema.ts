import { z } from "zod";

const optionalText = (max: number) =>
  z.string().trim().max(max).optional().or(z.literal(""));

export const locationSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Escribe un nombre para la ubicación")
    .max(160, "El nombre es demasiado largo"),
  address: optionalText(240),
  city: optionalText(120),
  state: optionalText(120),
  zip: optionalText(12),
  contactName: optionalText(120),
  phone: optionalText(30),
  notes: optionalText(1000),
});

export type LocationInput = z.infer<typeof locationSchema>;

export function normalizarUbicacion(data: LocationInput) {
  return {
    name: data.name,
    address: data.address || null,
    city: data.city || null,
    state: data.state || null,
    zip: data.zip || null,
    contactName: data.contactName || null,
    phone: data.phone || null,
    notes: data.notes || null,
  };
}
