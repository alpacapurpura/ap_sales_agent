"use client"
import { ClerkProvider } from "@clerk/nextjs"
import Link from "next/link"

export default function NotFound() {
  return (
    <ClerkProvider>
      <html>
        <body>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh", padding: "20px", textAlign: "center", fontFamily: "system-ui, sans-serif" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", marginBottom: "1rem" }}>404 - Página no encontrada</h2>
            <p style={{ marginBottom: "2rem", color: "#666" }}>Lo sentimos, la página que buscas no existe.</p>
            <Link 
              href="/"
              style={{ padding: "0.5rem 1rem", backgroundColor: "#000", color: "#fff", textDecoration: "none", borderRadius: "4px" }}
            >
              Volver al inicio
            </Link>
          </div>
        </body>
      </html>
    </ClerkProvider>
  )
}