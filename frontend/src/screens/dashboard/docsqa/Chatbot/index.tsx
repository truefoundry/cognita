import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import IconProvider from '@/components/assets/IconProvider'
import Button from '@/components/base/atoms/Button'
import Input from '@/components/base/atoms/Input'
import Markdown from '@/components/base/atoms/Markdown'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import {
  CollectionQueryDto,
  baseQAFoundryPath,
  useGetApplicationDetailsByNameQuery,
} from '@/stores/qafoundry'
import { startCase } from 'lodash'
import { SSE } from 'sse.js'

const DocsQAChatbot = () => {
  const params = useParams()
  const [prompt, setPrompt] = useState('')
  const [isRunningPrompt, setIsRunningPrompt] = useState(false)
  const [answer, setAnswer] = useState('')
  const [errorMessage, setErrorMessage] = useState(false)

  const {
    data: applicationsData,
    isLoading: isApplicationsDataLoading,
    isFetching: isApplicationsDataFetching,
  } = useGetApplicationDetailsByNameQuery(params?.id ?? '', {
    skip: !params?.id,
  })

  const handlePromptSubmit = async () => {
    setIsRunningPrompt(true)
    setAnswer('')
    setErrorMessage(false)
    try {
      const params: CollectionQueryDto = {
        ...applicationsData.config,
        query: prompt,
        stream: true,
      }
      const sseRequest = new SSE(`${baseQAFoundryPath}/retrievers/${applicationsData.config.query_controller}/answer`, {
        payload: JSON.stringify({
          ...params,
          stream: true,
        }),
        headers: {
          'Content-Type': 'application/json'
        },
      })

      sseRequest.addEventListener('data', (event: any) => {
        try {
          const parsed = JSON.parse(event.data)
          if (parsed?.type === "answer") {
            setAnswer((prevAnswer) => prevAnswer + parsed.content)
            setIsRunningPrompt(false)
          }
        } catch (err) {}
      })

      sseRequest.addEventListener('end', (event: any) => {
        sseRequest.close()
      })
    } catch (err: any) {
      setErrorMessage(true)
    }
  }

  return (
    <>
      <div className="flex gap-5 h-full w-full">
        {isApplicationsDataLoading || isApplicationsDataFetching ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : (
          <>
            <div className="h-full border-2 rounded-lg border-[#CEE0F8] w-full bg-white p-3">
              {answer ? (
                <div className="overflow-y-auto flex flex-col gap-4 h-[calc(100%-3.125rem)]">
                  <div className="h-full overflow-y-auto flex gap-4">
                    <div className="bg-indigo-400 w-5 h-5 rounded-full flex items-center justify-center mt-0.5">
                      <IconProvider
                        icon="message"
                        className="text-white"
                        size={0.625}
                      />
                    </div>
                    <div className="w-full font-inter text-base">
                      <div className="font-bold">Answer:</div>
                      <Markdown className="text-sm">{answer}</Markdown>
                    </div>
                  </div>
                </div>
              ) : isRunningPrompt ? (
                <div className="overflow-y-auto flex flex-col justify-center items-center gap-2 h-[calc(100%-3.125rem)]">
                  <div>
                    <Spinner center medium />
                  </div>
                  <div className="text-center">Fetching Answer...</div>
                </div>
              ) : errorMessage ? (
                <div className="overflow-y-auto flex gap-4 mt-7">
                  <div className="bg-error w-6 h-6 rounded-full flex items-center justify-center mt-0.5">
                    <IconProvider icon="message" className="text-white" />
                  </div>
                  <div className="w-full font-inter text-base text-error">
                    <div className="font-bold text-lg">Error</div>
                    We failed to get answer for your query, please try again by
                    resending query or try again in some time.
                  </div>
                </div>
              ) : (
                <div className="h-[calc(100%-3.125rem)] flex justify-center items-center overflow-y-auto">
                  <div className="h-full">
                    <div className="font-medium text-lg text-center">
                      Welcome to {startCase(applicationsData.name) ?? 'Cognita'}
                    </div>
                  </div>
                </div>
              )}
              <div className="flex gap-4 items-center">
                <form className="w-full relative" onSubmit={(e) => e.preventDefault()}>
                  <Input
                    className="w-full h-[2.75rem] text-sm pr-14"
                    placeholder="Ask any related question"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                  />
                  <Button
                    icon="paper-plane-top"
                    className="btn-sm absolute right-2 top-[0.375rem]"
                    onClick={handlePromptSubmit}
                    loading={isRunningPrompt}
                    disabled={!prompt}
                  />
                </form>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}

export default DocsQAChatbot
