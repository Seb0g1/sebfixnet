import type { ServiceInfo } from "../types";

export const SERVICE_CATALOG: Record<string, ServiceInfo> = {
  telegram: { name: "Telegram", icon: "telegram", domains: ["t.me", "telegram.org", "web.telegram.org"] },
  discord: { name: "Discord", icon: "discord", domains: ["discord.com", "discord.gg"] },
  youtube: { name: "YouTube", icon: "youtube", domains: ["youtube.com", "youtu.be"] },
  twitch: { name: "Twitch", icon: "twitch", domains: ["twitch.tv"] },
  chatgpt: { name: "ChatGPT", icon: "chatgpt", domains: ["chatgpt.com", "openai.com"] },
  twitter: { name: "Twitter", icon: "twitter", domains: ["twitter.com", "x.com"] },
  instagram: { name: "Instagram", icon: "instagram", domains: ["instagram.com"] },
  tiktok: { name: "TikTok", icon: "tiktok", domains: ["tiktok.com"] },
  facebook: { name: "Facebook", icon: "facebook", domains: ["facebook.com"] },
  cloudflare: { name: "CloudFlare", icon: "cloudflare", domains: ["cloudflare.com"] },
  roblox: { name: "Roblox", icon: "roblox", domains: ["roblox.com"] },
  soundcloud: { name: "SoundCloud", icon: "soundcloud", domains: ["soundcloud.com"] },
  whatsapp: { name: "WhatsApp", icon: "whatsapp", domains: ["whatsapp.com"] },
  notion: { name: "Notion", icon: "notion", domains: ["notion.so"] },
  figma: { name: "Figma", icon: "figma", domains: ["figma.com"] },
  google_ai: { name: "Google AI", icon: "google_ai", domains: ["gemini.google.com"] },
};

export const DEFAULT_SERVICES = ["telegram", "discord", "youtube"];
