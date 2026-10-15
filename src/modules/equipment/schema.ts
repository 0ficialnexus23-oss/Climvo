import { z } from "zod";

const optionalText = (max: number) =>
  z.string().trim().max(max).optional().or(z.literal(""));

export const equipmentSchema = z.object({
  customerId: z.string().min(1, "Selecciona un cliente"),
  locationId: optionalText(40),
  type: z
    .string()
    .trim()
    .min(2, "Escribe el tipo de equipo (por ejemplo: minisplit)")
    .max(80, "El tipo es demasiado largo"),
  brand: optionalText(80),
  model: optionalText(80),
  serialNumber: optionalText(80),
  capacityTr: optionalText(10),
  refrigerant: optionalText(40),
  installDate: optionalText(20),
  warrantyUntil: optionalText(20),
  notes: optionalText(2000),
});

export type EquipmentInput = z.infer<typeof equipmentSchema>;

export function parseNumero(value?: string | null): number | null {
  if (!value) return null;
  const n = Number(value.replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

export function parseFecha(value?: string | null): Date | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}
