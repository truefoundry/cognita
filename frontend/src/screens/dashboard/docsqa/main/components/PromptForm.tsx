import React, { useState } from 'react'
import { SSE } from 'sse.js'

import { baseQAFoundryPath, CollectionQueryDto } from '@/stores/qafoundry'
import Input from '@/components/base/atoms/Input'
import Button from '@/components/base/atoms/Button'
import { useDocsQAContext } from '../context'
import { notifyError } from '@/utils/error'

const Form = (props: any) => {
  const {
    setErrorMessage,
    setSourceDocs,
    setAnswer,
    setPrompt,
    selectedQueryModel,
    allEnabledModels,
    modelConfig,
    retrieverConfig,
    selectedCollection,
    selectedRetriever,
    promptTemplate,
    prompt,
    isInternetSearchEnabled,
    selectedQueryController,
  } = useDocsQAContext()

  const { isRunningPrompt, setIsRunningPrompt } = props

  const handlePromptSubmit = async () => {
    setIsRunningPrompt(true)
    setAnswer('')
    setSourceDocs([])
    setErrorMessage(false)
    try {
      const selectedModel = allEnabledModels.find(
        (model: any) => model.name == selectedQueryModel,
      )
      if (!selectedModel) {
        throw new Error('Model not found')
      }
      try {
        JSON.parse(modelConfig)
      } catch (err: any) {
        throw new Error('Invalid Model Configuration')
      }
      try {
        JSON.parse(retrieverConfig)
      } catch (err: any) {
        throw new Error('Invalid Retriever Configuration')
      }

      const params: CollectionQueryDto = Object.assign(
        {
          collection_name: selectedCollection,
          query: prompt,
          model_configuration: {
            name: selectedModel.name,
            provider: selectedModel.provider,
            ...JSON.parse(modelConfig),
          },
          retriever_name: selectedRetriever?.name ?? '',
          retriever_config: JSON.parse(retrieverConfig),
          prompt_template: promptTemplate,
          internet_search_enabled: isInternetSearchEnabled,
        },
        {},
      )

      const sseRequest = new SSE(
        `${baseQAFoundryPath}/retrievers/${selectedQueryController}/answer`,
        {
          payload: JSON.stringify({
            ...params,
            stream: true,
          }),
          headers: {
            'Content-Type': 'application/json',
          },
        },
      )

      sseRequest.addEventListener('data', (event: any) => {
        try {
          const parsed = JSON.parse(event.data)
          if (parsed?.type === 'answer') {
            setAnswer((prevAnswer: string) => prevAnswer + parsed.content)
            setIsRunningPrompt(false)
          } else if (parsed?.type === 'docs') {
            setSourceDocs((prevDocs) => [...prevDocs, ...parsed.content])
          }
        } catch (err: any) {
          throw new Error('An error occurred while processing the response.')
        }
      })

      sseRequest.addEventListener('end', (event: any) => {
        sseRequest.close()
      })

      sseRequest.addEventListener('error', (event: any) => {
        sseRequest.close()
        setPrompt('')
        setIsRunningPrompt(false)
        const message = JSON.parse(event.data).detail[0].msg
        notifyError('Failed to retrieve answer', { message })
      })
    } catch (err: any) {
      setPrompt('')
      setIsRunningPrompt(false)
      notifyError('Failed to retrieve answer', err)
    }
  }

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
