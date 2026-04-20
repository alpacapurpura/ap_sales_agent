"use client";

import { Copy, Check, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import { useCreateDomain, useGetDomainInstructions, useVerifyDomain } from "../hooks/use-domains";
import { isDomainConflict } from "../types";

import type { TenantDomain, DomainInstructions } from "../types";

type WizardStep = "input" | "dns" | "verify";

interface CustomDomainWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface CopyButtonProps {
  value: string;
  className?: string;
}

function CopyButton({ value, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      className={cn("h-7 w-7 p-0 shrink-0", className)}
      onClick={handleCopy}
      aria-label="Copiar valor"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
    </Button>
  );
}

interface DnsRowProps {
  label: string;
  value: string;
}

function DnsRow({ label, value }: DnsRowProps) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {label}
      </span>
      <div className="flex items-center gap-2 rounded-md border bg-muted px-3 py-2">
        <span className="font-mono text-xs flex-1 break-all">{value}</span>
        <CopyButton value={value} />
      </div>
    </div>
  );
}

/**
 *
 */
export function CustomDomainWizard({ open, onOpenChange }: CustomDomainWizardProps) {
  const [step, setStep] = useState<WizardStep>("input");
  const [hostname, setHostname] = useState("");
  const [conflictSuggestion, setConflictSuggestion] = useState<string | null>(null);
  const [conflictMessage, setConflictMessage] = useState<string | null>(null);
  const [createdDomain, setCreatedDomain] = useState<TenantDomain | null>(null);
  const [instructions, setInstructions] = useState<DomainInstructions | null>(null);
  const [verifySuccess, setVerifySuccess] = useState(false);
  const [inputError, setInputError] = useState<string | null>(null);

  const createDomain = useCreateDomain();
  const getInstructions = useGetDomainInstructions();
  const verifyDomain = useVerifyDomain();

  const handleClose = () => {
    onOpenChange(false);
    // Reset state after close animation
    setTimeout(() => {
      setStep("input");
      setHostname("");
      setConflictSuggestion(null);
      setConflictMessage(null);
      setCreatedDomain(null);
      setInstructions(null);
      setVerifySuccess(false);
      setInputError(null);
    }, 300);
  };

  const handleSubmitHostname = async (hostnameToSubmit: string) => {
    setInputError(null);
    setConflictSuggestion(null);
    setConflictMessage(null);

    try {
      const domain = await createDomain.mutateAsync({
        hostname: hostnameToSubmit,
        domainType: "custom",
      });
      setCreatedDomain(domain);

      const instr = await getInstructions.mutateAsync(domain.id);
      setInstructions(instr);
      setStep("dns");
    } catch (err: unknown) {
      if (isDomainConflict(err)) {
        setConflictSuggestion(err.suggestion);
        setConflictMessage(err.message);
      } else if (err instanceof Error) {
        setInputError(err.message);
      } else {
        setInputError("Error al añadir dominio. Inténtalo de nuevo.");
      }
    }
  };

  const handleUseSuggestion = () => {
    if (conflictSuggestion) {
      setHostname(conflictSuggestion);
      setConflictSuggestion(null);
      setConflictMessage(null);
    }
  };

  const handleVerify = async () => {
    if (!createdDomain) return;
    try {
      const updated = await verifyDomain.mutateAsync(createdDomain.id);
      if (updated.status === "active") {
        setVerifySuccess(true);
      } else {
        setCreatedDomain(updated);
        setStep("verify");
      }
    } catch {
      // error is shown via mutation state
    }
  };

  const isLoading = createDomain.isPending || getInstructions.isPending;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {step === "input" && "Añadir dominio personalizado"}
            {step === "dns" && "Configurar registros DNS"}
            {step === "verify" && "Verificar dominio"}
          </DialogTitle>
          <DialogDescription>
            {step === "input" && "Ingresa el dominio o subdominio que quieres usar con tu cuenta."}
            {step === "dns" && "Añade el siguiente registro CNAME en tu proveedor de DNS."}
            {step === "verify" && "Una vez añadido el registro DNS, verifica tu dominio."}
          </DialogDescription>
        </DialogHeader>

        {/* Step 1: Input */}
        {step === "input" && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="hostname">Dominio</Label>
              <Input
                id="hostname"
                placeholder="tienda.tudominio.com"
                value={hostname}
                onChange={(e) => setHostname(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && hostname.trim()) {
                    void handleSubmitHostname(hostname.trim());
                  }
                }}
                disabled={isLoading}
              />
            </div>

            {inputError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{inputError}</AlertDescription>
              </Alert>
            )}

            {conflictSuggestion && conflictMessage && (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="flex flex-col gap-2">
                  <span>{conflictMessage}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    className="self-start"
                    onClick={handleUseSuggestion}
                  >
                    Usar {conflictSuggestion} en su lugar
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={handleClose} disabled={isLoading}>
                Cancelar
              </Button>
              <Button
                onClick={() => handleSubmitHostname(hostname.trim())}
                disabled={!hostname.trim() || isLoading}
              >
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Continuar
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: DNS Instructions */}
        {step === "dns" && instructions && (
          <div className="flex flex-col gap-4">
            {instructions.cname_record && (
              <div className="flex flex-col gap-3 rounded-lg border p-4">
                <p className="text-sm font-semibold">Registro CNAME</p>
                <DnsRow label="Tipo" value={instructions.cname_record.type} />
                <DnsRow label="Nombre / Host" value={instructions.cname_record.name} />
                <DnsRow label="Destino / Target" value={instructions.cname_record.target} />
              </div>
            )}

            {instructions.txt_record && (
              <div className="flex flex-col gap-3 rounded-lg border p-4">
                <p className="text-sm font-semibold">Registro TXT (verificación)</p>
                <DnsRow label="Tipo" value={instructions.txt_record.type} />
                <DnsRow label="Nombre / Host" value={instructions.txt_record.name} />
                <DnsRow label="Valor" value={instructions.txt_record.value} />
              </div>
            )}

            <p className="text-xs text-muted-foreground">
              Los cambios de DNS pueden tardar hasta 48 horas en propagarse.
            </p>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setStep("input")}>
                Atrás
              </Button>
              <Button onClick={() => setStep("verify")}>He añadido el registro</Button>
            </div>
          </div>
        )}

        {/* Step 3: Verify */}
        {step === "verify" && (
          <div className="flex flex-col gap-4">
            {verifySuccess ? (
              <div className="flex flex-col items-center gap-3 py-4">
                <CheckCircle2 className="h-12 w-12 text-green-500" />
                <p className="text-center font-semibold">¡Dominio verificado correctamente!</p>
                <p className="text-center text-sm text-muted-foreground">
                  {createdDomain?.hostname} ya está activo en tu cuenta.
                </p>
                <Button onClick={handleClose}>Cerrar</Button>
              </div>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  Dominio: <span className="font-mono font-medium">{createdDomain?.hostname}</span>
                </p>

                {verifyDomain.isError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {verifyDomain.error instanceof Error
                        ? verifyDomain.error.message
                        : "Error al verificar. Asegúrate de que el registro DNS esté añadido correctamente."}
                    </AlertDescription>
                  </Alert>
                )}

                {verifyDomain.data?.status === "verifying" && (
                  <Alert>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <AlertDescription>
                      Verificación en progreso. Los cambios DNS pueden tardar unos minutos.
                    </AlertDescription>
                  </Alert>
                )}

                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setStep("dns")}>
                    Atrás
                  </Button>
                  <Button onClick={handleVerify} disabled={verifyDomain.isPending}>
                    {verifyDomain.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Verificar dominio
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
