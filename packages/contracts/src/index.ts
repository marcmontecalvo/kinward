export type PersonRole = "admin" | "adult" | "teen" | "child";
export type AssistantKind = "primary" | "specialist" | "temporary" | "shared-fallback";

export interface PersonSummary {
  id: string;
  displayName: string;
  role: PersonRole;
  activeAssistantId?: string;
}

export interface AssistantSummary {
  id: string;
  ownerId?: string;
  name: string;
  kind: AssistantKind;
  accent?: string;
}

export interface HealthCapability {
  state: "available" | "degraded" | "disabled";
  detail?: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  service: "kinward";
  capabilities: {
    memory: HealthCapability;
    knowledge: HealthCapability;
    homeAssistant: HealthCapability;
  };
}
