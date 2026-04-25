/// <reference types="vite/client" />

// Typed env vars exposed to the client at build time. Vite only injects
// keys prefixed with VITE_; anything else stays server-side.
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
  readonly VITE_USER_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
