import * as React from "react";
import { cn } from "@/lib/utils";

export function Select({
  className,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-base text-slate-900",
        "focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20",
        className,
      )}
      {...props}
    >
      {children}
    </select>
  );
}
