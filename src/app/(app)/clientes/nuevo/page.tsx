import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { CustomerForm } from "@/components/customers/customer-form";
import { Card, CardContent } from "@/components/ui/card";
import { requireSession } from "@/lib/session";
import { crearClienteAction } from "@/modules/customers/actions";

export const metadata = { title: "Nuevo cliente · Climvo" };

export default async function NuevoClientePage() {
  await requireSession();

  return (
    <div className="space-y-4">
      <Link
        href="/clientes"
        className="inline-flex items-center gap-1 text-sm text-slate-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Clientes
      </Link>
      <h1 className="text-xl font-semibold text-slate-900">Nuevo cliente</h1>
      <Card>
        <CardContent>
          <CustomerForm
            action={crearClienteAction}
            submitLabel="Crear cliente"
          />
        </CardContent>
      </Card>
    </div>
  );
}
