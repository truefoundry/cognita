import React from 'react'

import Input from '@/components/base/atoms/Input'
import Button from '@/components/base/atoms/Button'

const Form = (props: any) => {
  const {
    setPrompt,
    handlePromptSubmit,
    isRunningPrompt,
    prompt,
    selectedQueryModel,
  } = props

  return (
    <div className="flex gap-4 items-center">
      <form className="w-full relative" onSubmit={(e) => e.preventDefault()}>
        <Input
          className="w-full min-h-[2.75rem] text-sm pr-14"
          placeholder="Ask any question related to this document"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <Button
          icon="paper-plane-top"
          className="btn-sm btn-neutral absolute right-2 top-[0.375rem]"
          onClick={handlePromptSubmit}
          loading={isRunningPrompt}
          disabled={!prompt || !selectedQueryModel}
        />
      </form>
    </div>
  )
}

export default Form
