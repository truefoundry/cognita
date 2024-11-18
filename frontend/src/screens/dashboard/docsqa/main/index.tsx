import React from 'react'
import { DocsQAProvider } from './context'
import DocsQA from './DocsQA'

const index = () => {
  return (
    <DocsQAProvider>
      <DocsQA />
    </DocsQAProvider>
  )
}

export default index
