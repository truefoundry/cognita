// docs qa
export const IS_DOCS_QA_STANDALONE_ENABLED =
  import.meta.env.VITE_DOCS_QA_ENABLE_STANDALONE === 'true'
export const IS_DOCS_QA_REDIRECT_ENABLED =
  import.meta.env.VITE_DOCS_QA_ENABLE_REDIRECT === 'true'
export const DOCS_QA_STANDALONE_PATH =
  import.meta.env.VITE_DOCS_QA_STANDALONE_PATH || 'docs-qa'
export const DOCS_QA_SEARCH_PAYLOAD_PATCH: any = JSON.parse(
  import.meta.env.VITE_DOCS_QA_SEARCH_PAYLOAD_PATCH ?? {}
)
export const DOCS_QA_MAX_UPLOAD_SIZE_MB = parseInt(
  import.meta.env.VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB || '2'
)
