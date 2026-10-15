import Link from "next/link";

import { RegistroForm } from "./registro-form";

export const metadata = { title: "Crear empresa · Climvo" };

export default function RegistroPage() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-lg font-semibold text-slate-900">Crea tu empresa</h1>
      <p className="mb-4 mt-1 text-sm text-slate-500">
        Tendrás tu espacio de trabajo listo en un minuto.
      </p>
      <RegistroForm />
      <p className="mt-5 text-center text-sm text-slate-500">
        ¿Ya tienes cuenta?{" "}
        <Link href="/login" className="font-medium text-sky-600">
          Entrar
        </Link>
      </p>
    </div>
  );
}
