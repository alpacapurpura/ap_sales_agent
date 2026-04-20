export type DomainStatus = "pending_verification" | "verifying" | "active" | "failed" | "suspended";

export type DomainType = "platform" | "custom";

export interface TenantDomain {
  id: string;
  tenant_id: string;
  hostname: string;
  domain_type: DomainType;
  status: DomainStatus;
  is_primary: boolean;
  ssl_status: string | null;
  verification_method: string | null;
  verification_cname_target: string | null;
  verification_txt_name: string | null;
  verification_txt_value: string | null;
  verified_at: string | null;
  created_at: string | null;
}

export interface DomainInstructions {
  hostname: string;
  domain_type: DomainType;
  status: DomainStatus;
  cname_record: {
    type: "CNAME";
    name: string;
    target: string;
  } | null;
  txt_record: {
    type: "TXT";
    name: string;
    value: string;
  } | null;
}

export interface DomainConflict {
  code: "DOMAIN_CONFLICT";
  provider: string;
  suggestion: string;
  message: string;
}

/**
 *
 */
export function isDomainConflict(err: unknown): err is DomainConflict {
  return (
    typeof err === "object" && err !== null && (err as DomainConflict).code === "DOMAIN_CONFLICT"
  );
}
