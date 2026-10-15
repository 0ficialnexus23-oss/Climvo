"use client";

import { Button } from "@/components/ui/button";
import { logoutAction } from "@/modules/auth/actions";

export function LogoutButton() {
  return (
    <form action={logoutAction}>
      <Button type="submit" variant="outline" className="w-full">
        Cerrar sesión
      </Button>
    </form>
  );
}
