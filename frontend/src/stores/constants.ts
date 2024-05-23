export const IS_DOCS_QA_REDIRECT_ENABLED =
  import.meta.env.VITE_DOCS_QA_ENABLE_REDIRECT === 'true'
export const DOCS_QA_STANDALONE_PATH =
  process.env.VITE_DEPLOYMENT_PATH ||
  import.meta.env.VITE_DOCS_QA_STANDALONE_PATH ||
  'docs-qa'
export const DOCS_QA_MAX_UPLOAD_SIZE_MB = parseInt(
  import.meta.env.VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB || '2'
)
