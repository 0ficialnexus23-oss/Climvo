import { prisma } from "@/lib/prisma";
import { registrarEmpresa } from "@/modules/auth/service";
import { crearCliente } from "@/modules/customers/service";
import { crearUbicacion } from "@/modules/locations/service";
import { crearEquipo } from "@/modules/equipment/service";

async function main() {
  const email = "demo@climvo.test";

  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    await prisma.tenant.delete({ where: { id: existing.tenantId } });
  }

  const tenant = await registrarEmpresa({
    companyName: "Demo HVAC",
    name: "Demo Owner",
    email,
    password: "contrasena123",
  });

  const cliente = await crearCliente(tenant.id, {
    name: "Hotel Costa Azul",
    type: "COMMERCIAL",
    contactName: "Ing. López",
    phone: "8112345678",
    email: "contacto@costaazul.mx",
    notes: "Acceso por la puerta de servicio.",
  });

  const ubicacion = await crearUbicacion(tenant.id, cliente.id, {
    name: "Sucursal Centro",
    address: "Av. Juárez 123",
    city: "Monterrey",
    state: "NL",
    zip: "64000",
    contactName: "",
    phone: "",
    notes: "",
  });

  await crearEquipo(tenant.id, {
    customerId: cliente.id,
    locationId: ubicacion.id,
    type: "Minisplit",
    brand: "LG",
    model: "Dual Inverter",
    serialNumber: "SN-001",
    capacityTr: "2.5",
    refrigerant: "R-410A",
    installDate: "2024-03-15",
    warrantyUntil: "2026-03-15",
    notes: "Equipo de recepción.",
  });

  console.log("demo listo:", email, "/ contrasena123");
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
