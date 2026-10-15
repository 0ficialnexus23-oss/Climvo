import { BottomNav } from "@/components/app-shell/bottom-nav";
import { requireSession } from "@/lib/session";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await requireSession();

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <span className="font-semibold tracking-tight text-sky-600">
            Climvo
          </span>
          <span className="max-w-[55%] truncate text-xs text-slate-500">
            {session.user.name}
          </span>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-4">{children}</main>
      <BottomNav />
    </div>
  );
}
