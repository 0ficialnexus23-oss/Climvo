import { registrarEmpresa, RegistroError } from "@/modules/auth/service";
import { prisma } from "@/lib/prisma";

async function main() {
  const email = `test+${Date.now()}@climvo.test`;

  const tenant = await registrarEmpresa({
    companyName: "Climas del Norte",
    name: "Juan Perez",
    email,
    password: "contrasena123",
    phone: "8112345678",
  });
  console.log("1) tenant creado:", tenant.name, tenant.id);

  const user = await prisma.user.findUnique({ where: { email } });
  console.log("2) usuario:", user?.name, "| rol:", user?.role, "| mismo tenant:", user?.tenantId === tenant.id);
  console.log("3) contrasena hasheada:", user?.passwordHash.startsWith("$2") === true);
  console.log("4) hash NO contiene la clave:", !user?.passwordHash.includes("contrasena123"));

  try {
    await registrarEmpresa({ companyName: "Otra", name: "Xavier", email, password: "contrasena123" });
    console.log("5) duplicado: NO detectado (FALLO)");
  } catch (e) {
    console.log("5) duplicado rechazado:", e instanceof RegistroError);
  }

  const otroTenant = await prisma.tenant.create({ data: { name: "Otra Empresa" } });
  const aislado = await prisma.customer.count({ where: { tenantId: otroTenant.id } });
  console.log("6) aislamiento por tenant (otra empresa ve 0):", aislado === 0);
}

main()
  .catch((e) => { console.error("ERROR:", e); process.exitCode = 1; })
  .finally(() => prisma.$disconnect());
