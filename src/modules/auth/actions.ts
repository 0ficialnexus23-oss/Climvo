"use server";

import { AuthError } from "next-auth";
import { revalidatePath } from "next/cache";

import { signIn, signOut } from "@/lib/auth";
import { loginSchema, registroSchema } from "./schema";
import { registrarEmpresa, RegistroError } from "./service";

export type ActionState = { error?: string } | undefined;

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

export async function registrarAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = registroSchema.safeParse({
    companyName: field(formData, "companyName"),
    name: field(formData, "name"),
    email: field(formData, "email"),
    password: field(formData, "password"),
    phone: field(formData, "phone"),
  });

  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message ?? "Datos invalidos." };
  }

  try {
    await registrarEmpresa(parsed.data);
  } catch (error) {
    if (error instanceof RegistroError) return { error: error.message };
    console.error("Error al registrar empresa:", error);
    return { error: "No se pudo crear la cuenta. Intenta de nuevo." };
  }

  try {
    await signIn("credentials", {
      email: parsed.data.email,
      password: parsed.data.password,
      redirectTo: "/hoy",
    });
  } catch (error) {
    if (error instanceof AuthError) {
      return {
        error:
          "Tu cuenta se creo, pero no se pudo iniciar sesion automaticamente. Entra desde la pantalla de acceso.",
      };
    }
    throw error;
  }
}

export async function loginAction(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const parsed = loginSchema.safeParse({
    email: field(formData, "email"),
    password: field(formData, "password"),
  });

  if (!parsed.success) {
    return { error: "Correo o contrasena incorrectos." };
  }

  try {
    await signIn("credentials", {
      email: parsed.data.email,
      password: parsed.data.password,
      redirectTo: "/hoy",
    });
  } catch (error) {
    if (error instanceof AuthError) {
      return { error: "Correo o contrasena incorrectos." };
    }
    throw error;
  }
}

export async function logoutAction(): Promise<void> {
  revalidatePath("/", "layout");
  await signOut({ redirectTo: "/login" });
}
