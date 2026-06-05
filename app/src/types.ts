export type Mode = "combined" | "full";

export type Screen = "main" | "services" | "account" | "activate";

export interface ServiceInfo {
  name: string;
  icon: string;
  domains: string[];
}

export interface AppSettings {
  key: string;
  mode: Mode;
  selectedServices: string[];
  autostart: string;
  minimizeOnStart: boolean;
  minimizeOnClose: boolean;
  apiUrl: string;
}

export interface ConnectionStatus {
  connected: boolean;
  message: string;
}
