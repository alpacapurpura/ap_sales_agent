export interface PaymentGatewayConfig {
  provider: "culqi" | "mercadopago";
  mode: "sandbox" | "production";
  sandboxKeys: {
    publicKey: string;
    secretKey: string;
  };
  productionKeys: {
    publicKey: string;
    secretKey: string;
  };
  isEnabled: boolean;
}
