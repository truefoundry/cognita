declare module 'redux-persist-cookie-storage'

declare module 'cookies-js'

declare module '@tailwindcss/typography' {
  import type { TailwindPlugin } from 'tailwindcss/plugin'
  const plugin: TailwindPlugin
  export default plugin
}

declare module '@tailwindcss/forms' {
  import type { TailwindPlugin } from 'tailwindcss/plugin'
  const plugin: TailwindPlugin
  export default plugin
}

declare module '@tailwindcss/line-clamp' {
  import type { TailwindPlugin } from 'tailwindcss/plugin'
  const plugin: TailwindPlugin
  export default plugin
}

declare module 'tailwind-scrollbar' {
  import type { TailwindPlugin } from 'tailwindcss/plugin'
  const plugin: TailwindPlugin
  export default plugin
}

declare module 'daisyui' {
  import type { TailwindPlugin } from 'tailwindcss/plugin'
  const plugin: TailwindPlugin
  export default plugin
}

// Silence ts error when importing images
declare module '*.jpg'
declare module '*.png'
declare module '*.jpeg'
declare module '*.svg'

declare interface ImportMetaEnv {
  readonly VITE_QA_FOUNDRY_URL: string
  readonly VITE_DOCS_QA_DELETE_COLLECTIONS: string
  readonly VITE_DOCS_QA_STANDALONE_PATH: string
  readonly VITE_DOCS_QA_ENABLE_REDIRECT: string
  readonly VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB: string
  readonly VITE_USE_LOCAL: string
  // * Seeded by VITE
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
  readonly BASE_URL: string
}

declare interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  globalConfig: ImportMetaEnv
}
