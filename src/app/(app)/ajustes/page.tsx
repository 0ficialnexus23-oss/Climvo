import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LogoutButton } from "@/components/app-shell/logout-button";
import { prisma } from "@/lib/prisma";
import { requireSession } from "@/lib/session";

export const metadata = { title: "Ajustes · Climvo" };

const roleLabels: Record<string, string> = {
  OWNER: "Dueño",
  OFFICE: "Oficina",
  TECH: "Técnico",
};

export default async function AjustesPage() {
  const session = await requireSession();

  const [tenant, users] = await Promise.all([
    prisma.tenant.findUnique({
      where: { id: session.user.tenantId },
      select: { name: true, email: true, phone: true, timezone: true },
    }),
    prisma.user.findMany({
      where: { tenantId: session.user.tenantId },
      orderBy: { createdAt: "asc" },
      select: { id: true, name: true, email: true, role: true, active: true },
    }),
  ]);

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-semibold text-slate-900">Ajustes</h1>

      <Card>
        <CardHeader>
          <CardTitle>Empresa</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <p className="font-medium text-slate-900">{tenant?.name}</p>
          <p className="text-slate-500">{tenant?.email ?? "Sin correo"}</p>
          <p className="text-slate-500">{tenant?.phone ?? "Sin teléfono"}</p>
          <p className="text-slate-500">Zona horaria: {tenant?.timezone}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Usuarios</CardTitle>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100">
          {users.map((u) => (
            <div key={u.id} className="flex items-center justify-between py-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">
                  {u.name}
                </p>
                <p className="truncate text-xs text-slate-500">{u.email}</p>
              </div>
              <Badge tone={u.role === "OWNER" ? "info" : "neutral"}>
                {roleLabels[u.role] ?? u.role}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>

      <LogoutButton />
    </div>
  );
}
