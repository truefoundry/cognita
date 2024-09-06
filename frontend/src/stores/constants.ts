export const IS_DOCS_QA_REDIRECT_ENABLED =
  import.meta.env.VITE_DOCS_QA_ENABLE_REDIRECT === 'true'
export const DOCS_QA_STANDALONE_PATH = import.meta.env
  .VITE_DOCS_QA_STANDALONE_PATH
export const DOCS_QA_MAX_UPLOAD_SIZE_MB = parseInt(
  import.meta.env.VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB || '2'
)
export const IS_LOCAL_DEVELOPMENT = import.meta.env.VITE_USE_LOCAL === 'true'
export const GTAG_ID = import.meta.env.VITE_GTAG_ID
export const CARBON_API_KEY = import.meta.env.VITE_CARBON_API_KEY
