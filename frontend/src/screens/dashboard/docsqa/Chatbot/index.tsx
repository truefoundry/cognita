import React, { useEffect, useState } from 'react'
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
import { set, startCase } from 'lodash'
import { SSE } from 'sse.js'

interface Message {
  sender: 'user' | 'bot'
  content: string
}

const DocsQAChatbot = () => {
  const params = useParams()
  const [prompt, setPrompt] = useState('')
  const [answer, setAnswer] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [errorMessage, setErrorMessage] = useState(false)
  const [isRunningPrompt, setIsRunningPrompt] = useState(false)

  const {
    data: applicationsData,
    isLoading: isApplicationsDataLoading,
    isFetching: isApplicationsDataFetching,
  } = useGetApplicationDetailsByNameQuery(params?.id ?? '', {
    skip: !params?.id,
  })

  const handlePromptSubmit = async () => {
    setIsRunningPrompt(true)
    setErrorMessage(false)

    setMessages((prevMessages) => [
      ...prevMessages,
      { sender: 'user', content: prompt },
      { sender: 'bot', content: '' },
    ])

    setAnswer('')

    try {
      const params: CollectionQueryDto = {
        ...applicationsData.config,
        query: prompt,
        stream: true,
      }

      const sseRequest = new SSE(
        `${baseQAFoundryPath}/retrievers/${applicationsData.config.query_controller}/answer`,
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
            setPrompt('')
            setIsRunningPrompt(false)
            setAnswer((prevAnswer) => prevAnswer + parsed.content)
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

  useEffect(() => {
    if (answer !== '')
      setMessages((prev) => {
        const updated = [...prev]
        if (updated) updated[updated.length - 1].content = answer
        return updated
      })
  }, [answer])

  return (
    <>
      <div className="flex gap-5 h-full w-full">
        {isApplicationsDataLoading || isApplicationsDataFetching ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : (
          <>
            <div className="h-full border-2 rounded-lg border-[#CEE0F8] w-full bg-white p-2">
              {messages.length > 0 ? (
                <div className="h-[calc(100%-3.75rem)]  mb-4  overflow-y-auto flex flex-col gap-4">
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`chat  ${msg.sender === 'user' ? 'chat-end' : 'chat-start '}  `}
                    >
                      <div
                        key={index}
                        className={`chat-bubble font-inter  text-sm ${msg.sender === 'user' && 'text-white'}   ${msg.sender === 'bot' ? 'text-black bg-[#CEE0F8]' : 'bg-[#6366F1]'}`}
                      >
                        {msg.sender === 'bot' && <p>Assistant</p>}
                        {msg.content === '' && answer === '' ? (
                          <div className="flex space-x-1 mt-3">
                            <span className="w-2 5 h-2 5 bg-[#6366F1] rounded-full animate-dot-3"></span>
                            <span className="w-2 5 h-2 5 bg-[#6366F1] rounded-full animate-dot-2"></span>
                            <span className="w-2 5 h-2 5 bg-[#6366F1] rounded-full animate-dot-1"></span>
                          </div>
                        ) : (
                          <Markdown>
                            {answer.length > 0 && msg.content === ''
                              ? answer
                              : msg.content}
                          </Markdown>
                        )}
                      </div>
                    </div>
                  ))}
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
                  <div className="h-full flex flex-col justify-between">
                    <div className="font-medium text-lg text-center">
                      Welcome to {startCase(applicationsData.name) ?? 'Cognita'}
                    </div>
                    <div className="flex flex-wrap mb-5 justify-center">
                      {applicationsData?.questions?.map(
                        (question: string, index: number) => (
                          <div
                            key={index}
                            className="bg-gray-50 p-2 rounded m-1 border text-sm border-gray-250 cursor-pointer"
                            onClick={() => setPrompt(question)}
                          >
                            {question}
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                </div>
              )}
              <div className="flex gap-4 items-center">
                <form
                  className="w-full relative"
                  onSubmit={(e) => e.preventDefault()}
                >
                  <Input
                    className="w-full h-[2.75rem] text-sm pr-14"
                    placeholder="Ask any related question"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                  />
                  <Button
                    icon="paper-plane-top"
                    className="btn-sm absolute right-2 top-[0.375rem] btn-neutral"
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
