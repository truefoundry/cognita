export const IS_DOCS_QA_REDIRECT_ENABLED =
  import.meta.env.VITE_DOCS_QA_ENABLE_REDIRECT === 'true'
export const DOCS_QA_STANDALONE_PATH = import.meta.env
  .VITE_DOCS_QA_STANDALONE_PATH
export const DOCS_QA_MAX_UPLOAD_SIZE_MB = parseInt(
  import.meta.env.VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB || '2'
)
export const IS_LOCAL_DEVELOPMENT = import.meta.env.VITE_USE_LOCAL === 'true'

console.log('LOCAL:', import.meta.env.VITE_USE_LOCAL)
console.log('QA FOUNDRY URL:', import.meta.env.VITE_QA_FOUNDRY_URL)
