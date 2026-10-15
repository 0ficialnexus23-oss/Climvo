import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { CustomerForm } from "@/components/customers/customer-form";
import { Card, CardContent } from "@/components/ui/card";
import { requireSession } from "@/lib/session";
import { actualizarClienteAction } from "@/modules/customers/actions";
import { obtenerCliente } from "@/modules/customers/repository";

export default async function EditarClientePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requireSession();
  const { id } = await params;
  const cliente = await obtenerCliente(session.user.tenantId, id);

  if (!cliente) notFound();

  const action = actualizarClienteAction.bind(null, cliente.id);

  return (
    <div className="space-y-4">
      <Link
        href={`/clientes/${cliente.id}`}
        className="inline-flex items-center gap-1 text-sm text-slate-500"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Volver
      </Link>
      <h1 className="text-xl font-semibold text-slate-900">Editar cliente</h1>
      <Card>
        <CardContent>
          <CustomerForm
            action={action}
            submitLabel="Guardar cambios"
            defaultValues={{
              name: cliente.name,
              type: cliente.type,
              contactName: cliente.contactName,
              phone: cliente.phone,
              email: cliente.email,
              notes: cliente.notes,
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
