"use client";

import { Button } from "@/components/ui/button";

export function DeleteForm({
  action,
  label = "Eliminar",
  confirmText = "¿Seguro que quieres eliminarlo? Esta acción no se puede deshacer.",
  className,
}: {
  action: () => Promise<void>;
  label?: string;
  confirmText?: string;
  className?: string;
}) {
  return (
    <form
      action={action}
      className={className}
      onSubmit={(event) => {
        if (!window.confirm(confirmText)) {
          event.preventDefault();
        }
      }}
    >
      <Button type="submit" variant="danger" size="sm">
        {label}
      </Button>
    </form>
  );
}
