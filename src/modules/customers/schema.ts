import { z } from "zod";

export const customerTypes = ["RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL"] as const;
export type CustomerType = (typeof customerTypes)[number];

export const customerTypeLabels: Record<CustomerType, string> = {
  RESIDENTIAL: "Residencial",
  COMMERCIAL: "Comercial",
  INDUSTRIAL: "Industrial",
};

const optionalText = (max: number) =>
  z.string().trim().max(max).optional().or(z.literal(""));

export const customerSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Escribe el nombre del cliente")
    .max(160, "El nombre es demasiado largo"),
  type: z.enum(customerTypes),
  contactName: optionalText(120),
  phone: optionalText(30),
  email: z
    .string()
    .trim()
    .toLowerCase()
    .email("Escribe un correo válido")
    .optional()
    .or(z.literal("")),
  notes: optionalText(2000),
});

export type CustomerInput = z.infer<typeof customerSchema>;

export function normalizarCliente(data: CustomerInput) {
  return {
    name: data.name,
    type: data.type,
    contactName: data.contactName || null,
    phone: data.phone || null,
    email: data.email || null,
    notes: data.notes || null,
  };
}
