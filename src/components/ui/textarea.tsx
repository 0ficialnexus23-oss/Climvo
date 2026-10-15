import * as React from "react";
import { cn } from "@/lib/utils";

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-24 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-base text-slate-900",
        "placeholder:text-slate-400",
        "focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20",
        className,
      )}
      {...props}
    />
  );
}
