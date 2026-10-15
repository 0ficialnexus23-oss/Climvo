import { redirect } from "next/navigation";

import { getSession } from "@/lib/session";

export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();
  if (session?.user?.id) redirect("/hoy");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="text-3xl font-bold tracking-tight text-sky-600">
            Climvo
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Mantenimiento HVAC sin perder nada.
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
