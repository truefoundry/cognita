import IconProvider from '@/components/assets/IconProvider'
import Button from '@/components/base/atoms/Button'
import Input from '@/components/base/atoms/Input'
import Markdown from '@/components/base/atoms/Markdown'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import {
  CollectionQueryDto,
  baseQAFoundryPath,
  useGetAllEnabledChatModelsQuery,
  useGetCollectionNamesQuery,
  useGetOpenapiSpecsQuery,
} from '@/stores/qafoundry'
import React, { useEffect, useMemo, useState } from 'react'

const defaultRetrieverConfig = `{
  "search_type": "similarity",
  "k": 20,
  "fetch_k": 20,
  "filter": {}
}`

const defaultModelConfig = `{
  "parameters": {
    "temperature": 0.1
  }
}`

const defaultPrompt =
  'Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}'

interface SelectedRetrieverType {
  key: string
  name: string
  summary: string
  config: any
}

const staticObject = {
  collection_name: 'test',
  model_configuration: {
    name: 'truefoundry/openai-main/gpt-4-turbo',
    parameters: { temperature: 0.1 },
  },
  retriever_name: 'vectorstore',
  retriever_config: {
    search_type: 'similarity',
    search_kwargs: { k: 5 },
  },
  queryController: 'basic-rag',
}

const DocsQAChatbot = () => {
  const [selectedQueryModel, setSelectedQueryModel] = React.useState('')
  const [selectedCollection, setSelectedCollection] = useState('')
  const [selectedQueryController, setSelectedQueryController] = useState('')
  const [selectedRetriever, setSelectedRetriever] = useState<
    SelectedRetrieverType | undefined
  >()
  const [prompt, setPrompt] = useState('')
  const [isRunningPrompt, setIsRunningPrompt] = useState(false)
  const [answer, setAnswer] = useState('')
  const [errorMessage, setErrorMessage] = useState(false)
  const [modelConfig, setModelConfig] = useState(defaultModelConfig)
  const [retrieverConfig, setRetrieverConfig] = useState(defaultRetrieverConfig)
  const [promptTemplate, setPromptTemplate] = useState(defaultPrompt)

  const { data: collections, isLoading: isCollectionsLoading } =
    useGetCollectionNamesQuery()
  const { data: allEnabledModels } = useGetAllEnabledChatModelsQuery()
  const { data: openapiSpecs } = useGetOpenapiSpecsQuery()

  const allQueryControllers = useMemo(() => {
    if (!openapiSpecs?.paths) return []
    return Object.keys(openapiSpecs?.paths)
      .filter((path) => path.includes('/retrievers/'))
      .map((str) => {
        var parts = str.split('/')
        return parts[2]
      })
  }, [openapiSpecs])

  const allRetrieverOptions = useMemo(() => {
    const queryControllerPath = `/retrievers/${selectedQueryController}/answer`
    const examples =
      openapiSpecs?.paths[queryControllerPath]?.post?.requestBody?.content?.[
        'application/json'
      ]?.examples
    if (!examples) return []
    return Object.entries(examples).map(([key, value]: [string, any]) => ({
      key,
      name: value.value.retriever_name,
      summary: value.summary,
      config: value.value.retriever_config,
      promptTemplate: value.value.prompt_template ?? defaultPrompt,
    }))
  }, [selectedQueryController, openapiSpecs])

  const handlePromptSubmit = async () => {
    setIsRunningPrompt(true)
    setAnswer('')
    setErrorMessage(false)
    try {
      const selectedModel = allEnabledModels.find(
        (model: any) => model.name == selectedQueryModel
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

      const params: CollectionQueryDto = {
        ...staticObject,
        query: prompt,
        prompt_template: promptTemplate,
        stream: true,
      }
      const response = await fetch(
        `${baseQAFoundryPath}/retrievers/${selectedQueryController}/answer`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            ...params,
            stream: true,
          }),
        }
      )
      const reader = response?.body?.getReader()
      const readChunk = (value: any): any => {
        const chunkString = new TextDecoder().decode(value.value)
        try {
          const parsedResponse = JSON.parse(chunkString)
          if (parsedResponse?.end) return
          if (parsedResponse?.answer) {
            setAnswer((prevAnswer) => prevAnswer + parsedResponse.answer)
            setIsRunningPrompt(false)
          }
        } catch (err) {}
        return reader?.read().then(readChunk)
      }
      reader?.read().then(readChunk)
    } catch (err: any) {
      setErrorMessage(true)
    }
  }

  useEffect(() => {
    if (collections && collections.length) {
      setSelectedCollection(collections[0])
    }
  }, [collections])

  useEffect(() => {
    if (allQueryControllers && allQueryControllers.length) {
      setSelectedQueryController(allQueryControllers[0])
    }
  }, [allQueryControllers])

  useEffect(() => {
    if (allEnabledModels && allEnabledModels.length) {
      setSelectedQueryModel(allEnabledModels[0].name)
    }
  }, [allEnabledModels])

  useEffect(() => {
    if (allRetrieverOptions && allRetrieverOptions.length) {
      setSelectedRetriever(allRetrieverOptions[0])
      setPromptTemplate(allRetrieverOptions[0].promptTemplate)
    }
  }, [allRetrieverOptions])

  useEffect(() => {
    if (selectedRetriever) {
      setRetrieverConfig(JSON.stringify(selectedRetriever.config, null, 2))
    }
  }, [selectedRetriever])

  return (
    <>
      <div className="flex gap-5 h-full w-full">
        {isCollectionsLoading ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : selectedCollection ? (
          <>
            <div className="h-full border rounded-lg border-[#CEE0F8] w-full bg-white p-3">
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
                      Welcome to DocsQA
                    </div>
                  </div>
                </div>
              )}
              <div className="flex gap-4 items-center">
                <div className="w-full relative">
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
                    disabled={!prompt || !selectedQueryModel}
                  />
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center font-medium">
            Failed to get collection
          </div>
        )}
      </div>
    </>
  )
}

export default DocsQAChatbot
