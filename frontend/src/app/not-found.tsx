"use client";

import Link from "next/link";

/**
 *
 */
export default function NotFound() {
  return (
    <div className="flex h-screen w-full items-center justify-center flex-col gap-4">
      <h2 className="text-2xl font-semibold">404 — Página no encontrada</h2>
      <Link href="/" className="text-primary underline text-sm">
        Volver al inicio
      </Link>
    </div>
  );
}
