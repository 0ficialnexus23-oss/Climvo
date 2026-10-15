import Link from "next/link";

import { LoginForm } from "./login-form";

export const metadata = { title: "Entrar · Climvo" };

export default function LoginPage() {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="mb-4 text-lg font-semibold text-slate-900">Entrar</h1>
      <LoginForm />
      <p className="mt-5 text-center text-sm text-slate-500">
        ¿Aún no tienes cuenta?{" "}
        <Link href="/registro" className="font-medium text-sky-600">
          Crea tu empresa
        </Link>
      </p>
    </div>
  );
}
