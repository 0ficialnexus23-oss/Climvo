import { prisma } from "@/lib/prisma";
import { registrarEmpresa } from "@/modules/auth/service";
import {
  actualizarCliente,
  crearCliente,
  eliminarCliente,
} from "@/modules/customers/service";
import { listarClientes, obtenerCliente } from "@/modules/customers/repository";
import { crearUbicacion } from "@/modules/locations/service";
import { crearEquipo } from "@/modules/equipment/service";
import { listarEquipos } from "@/modules/equipment/repository";
import { AppError } from "@/lib/errors";

function ok(n: number, label: string, cond: boolean) {
  console.log(`${cond ? "PASA" : "FALLA"}  ${n}) ${label}`);
  if (!cond) process.exitCode = 1;
}

async function main() {
  const s = Date.now();

  const tA = await registrarEmpresa({ companyName: "Empresa A", name: "Owner A", email: `a+${s}@climvo.test`, password: "contrasena123" });
  const tB = await registrarEmpresa({ companyName: "Empresa B", name: "Owner B", email: `b+${s}@climvo.test`, password: "contrasena123" });
  ok(1, "dos empresas creadas", tA.id !== tB.id);

  const clienteA = await crearCliente(tA.id, {
    name: "Hotel Costa Azul",
    type: "COMMERCIAL",
    contactName: "Ing. López",
    phone: "8112345678",
    email: "contacto@costaazul.mx",
    notes: "",
  });
  ok(2, "cliente creado en empresa A", clienteA.tenantId === tA.id);

  const ubicacionA = await crearUbicacion(tA.id, clienteA.id, {
    name: "Sucursal Centro",
    address: "Av. Juárez 123",
    city: "Monterrey",
    state: "NL",
    zip: "64000",
    contactName: "",
    phone: "",
    notes: "",
  });
  ok(3, "ubicación creada", ubicacionA.customerId === clienteA.id);

  const equipoA = await crearEquipo(tA.id, {
    customerId: clienteA.id,
    locationId: ubicacionA.id,
    type: "Minisplit",
    brand: "LG",
    model: "Dual Inverter",
    serialNumber: "SN-001",
    capacityTr: "2.5",
    refrigerant: "R-410A",
    installDate: "2024-03-15",
    warrantyUntil: "2026-03-15",
    notes: "",
  });
  ok(4, "equipo creado con QR", Boolean(equipoA.qrToken) && equipoA.qrToken.length >= 16);
  ok(5, "capacidad numérica guardada", Number(equipoA.capacityTr) === 2.5);
  ok(6, "fecha guardada", equipoA.installDate?.toISOString().slice(0, 10) === "2024-03-15");

  ok(7, "empresa B NO ve al cliente de A", (await obtenerCliente(tB.id, clienteA.id)) === null);
  const listaB = await listarClientes(tB.id);
  ok(8, "lista de B no incluye al cliente de A", !listaB.some((c) => c.id === clienteA.id));

  let bloqueado = false;
  try {
    await actualizarCliente(tB.id, clienteA.id, {
      name: "Hackeado",
      type: "COMMERCIAL",
      contactName: "",
      phone: "",
      email: "",
      notes: "",
    });
  } catch (e) {
    bloqueado = e instanceof AppError;
  }
  ok(9, "B NO puede editar al cliente de A", bloqueado);

  let eliminadoBloqueado = false;
  try {
    await eliminarCliente(tB.id, clienteA.id);
  } catch (e) {
    eliminadoBloqueado = e instanceof AppError;
  }
  ok(10, "B NO puede eliminar al cliente de A", eliminadoBloqueado);

  let equipoCruzadoBloqueado = false;
  try {
    await crearEquipo(tB.id, { customerId: clienteA.id, locationId: "", type: "Minisplit", brand: "", model: "", serialNumber: "", capacityTr: "", refrigerant: "", installDate: "", warrantyUntil: "", notes: "" });
  } catch (e) {
    equipoCruzadoBloqueado = e instanceof AppError;
  }
  ok(11, "B NO puede crear equipo para cliente de A", equipoCruzadoBloqueado);

  const equiposA = await listarEquipos(tA.id);
  const equiposB = await listarEquipos(tB.id);
  ok(12, "A ve su equipo", equiposA.some((e) => e.id === equipoA.id));
  ok(13, "B no ve el equipo de A", !equiposB.some((e) => e.id === equipoA.id));

  // Limpieza de datos de prueba
  await prisma.tenant.deleteMany({ where: { id: { in: [tA.id, tB.id] } } });
  ok(14, "limpieza de datos de prueba", (await prisma.tenant.count({ where: { id: { in: [tA.id, tB.id] } } })) === 0);
}

main()
  .catch((e) => {
    console.error("ERROR:", e);
    process.exitCode = 1;
  })
  .finally(() => prisma.$disconnect());
