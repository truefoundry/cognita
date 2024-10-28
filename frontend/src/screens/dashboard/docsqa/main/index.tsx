import { Switch, TextareaAutosize } from '@mui/material'
import React, { useEffect, useMemo, useState } from 'react'
import { SSE } from 'sse.js'

import SimpleCodeEditor from '@/components/base/molecules/SimpleCodeEditor'
import { SelectedRetrieverType } from '@/types/retrieverTypes'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import notify from '@/components/base/molecules/Notify'
import Button from '@/components/base/atoms/Button'
import NoCollections from '../NoCollections'
import { notifyError } from '@/utils/error'
import {
  CollectionQueryDto,
  SourceDocs,
  baseQAFoundryPath,
  useCreateApplicationMutation,
  useGetAllEnabledChatModelsQuery,
  useGetCollectionNamesQuery,
  useGetOpenapiSpecsQuery,
  useQueryCollectionMutation,
} from '@/stores/qafoundry'
import {
  Option,
  ApplicationModal,
  Form,
  NoAnswer,
  ErrorAnswer,
  Answer,
} from './partials'

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

const DocsQA = () => {
  const [selectedQueryModel, setSelectedQueryModel] = React.useState('')
  const [selectedCollection, setSelectedCollection] = useState('')
  const [selectedQueryController, setSelectedQueryController] = useState('')
  const [selectedRetriever, setSelectedRetriever] = useState<
    SelectedRetrieverType | undefined
  >()
  const [prompt, setPrompt] = useState('')
  const [isRunningPrompt, setIsRunningPrompt] = useState(false)
  const [answer, setAnswer] = useState('')
  const [sourceDocs, setSourceDocs] = useState<SourceDocs[]>([])
  const [errorMessage, setErrorMessage] = useState(false)
  const [modelConfig, setModelConfig] = useState(defaultModelConfig)
  const [retrieverConfig, setRetrieverConfig] = useState(defaultRetrieverConfig)
  const [promptTemplate, setPromptTemplate] = useState(defaultPrompt)

  const [isInternetSearchEnabled, setIsInternetSearchEnabled] = useState(false)
  const [isCreateApplicationModalOpen, setIsCreateApplicationModalOpen] =
    useState(false)

  const { data: collections, isLoading: isCollectionsLoading } =
    useGetCollectionNamesQuery()
  const { data: allEnabledModels } = useGetAllEnabledChatModelsQuery()
  const { data: openapiSpecs } = useGetOpenapiSpecsQuery()
  const [searchAnswer] = useQueryCollectionMutation()
  const [createApplication, { isLoading: isCreateApplicationLoading }] =
    useCreateApplicationMutation()

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
            setAnswer((prevAnswer) => prevAnswer + parsed.content)
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

  const createChatApplication = async (
    applicationName: string,
    questions: [],
    setApplicationName: (name: string) => void,
  ) => {
    if (!applicationName) {
      return notify('error', 'Application name is required')
    }
    const selectedModel = allEnabledModels.find(
      (model: any) => model.name == selectedQueryModel,
    )

    try {
      await createApplication({
        name: `${applicationName}-rag-app`,
        config: {
          collection_name: selectedCollection,
          model_configuration: {
            name: selectedModel.name,
            provider: selectedModel.provider,
            ...JSON.parse(modelConfig),
          },
          retriever_name: selectedRetriever?.name ?? '',
          retriever_config: JSON.parse(retrieverConfig),
          prompt_template: promptTemplate,
          query_controller: selectedQueryController,
        },
        questions,
      }).unwrap()
      setApplicationName('')
      setIsCreateApplicationModalOpen(false)
      notify('success', 'Application created successfully')
    } catch (err: any) {
      notify('error', 'Failed to create application', err?.data?.detail)
    }
  }

  const resetQA = () => {
    setAnswer('')
    setErrorMessage(false)
    setPrompt('')
  }

  useEffect(() => {
    if (collections && collections.length) {
      setSelectedCollection(collections[0])
    }
    if (allQueryControllers && allQueryControllers.length) {
      setSelectedQueryController(allQueryControllers[0])
    }
    if (allEnabledModels && allEnabledModels.length) {
      setSelectedQueryModel(allEnabledModels[0].name)
    }
    if (allRetrieverOptions && allRetrieverOptions.length) {
      setSelectedRetriever(allRetrieverOptions[0])
      setPromptTemplate(allRetrieverOptions[0].promptTemplate)
    }
    if (selectedRetriever) {
      setRetrieverConfig(JSON.stringify(selectedRetriever.config, null, 2))
    }
  }, [
    collections,
    allQueryControllers,
    allEnabledModels,
    allRetrieverOptions,
    selectedRetriever,
  ])

  return (
    <>
      {isCreateApplicationModalOpen && (
        <ApplicationModal
          createChatApplication={createChatApplication}
          isCreateApplicationLoading={isCreateApplicationLoading}
          isCreateApplicationModalOpen={isCreateApplicationModalOpen}
          setIsCreateApplicationModalOpen={setIsCreateApplicationModalOpen}
        />
      )}
      <div className="flex gap-5 h-[calc(100vh-6.5rem)] w-full">
        {isCollectionsLoading ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : selectedCollection ? (
          <>
            <div className="h-full border rounded-lg border-[#CEE0F8] w-[23.75rem] bg-white p-4 overflow-auto">
              <div className="flex flex-col gap-3">
                <Option
                  title="Collection"
                  placeholder="Select Collection..."
                  initialValue={selectedCollection}
                  data={collections}
                  handleOnChange={(e) => {
                    resetQA()
                    setSelectedCollection(e.target.value)
                  }}
                />
                <Option
                  title="Query Controller"
                  placeholder="Select Query Controller..."
                  initialValue={selectedQueryController}
                  data={allQueryControllers}
                  handleOnChange={(e) => {
                    resetQA()
                    setSelectedQueryController(e.target.value)
                  }}
                />
                <Option
                  title="Model"
                  placeholder="Select Model..."
                  initialValue={selectedQueryModel}
                  data={allEnabledModels}
                  handleOnChange={(e) => {
                    resetQA()
                    setSelectedQueryModel(e.target.value)
                  }}
                />
              </div>

              <div className="mb-1 mt-3 text-sm">Model Configuration:</div>
              <SimpleCodeEditor
                language="json"
                height={130}
                defaultValue={defaultModelConfig}
                onChange={(updatedConfig) =>
                  setModelConfig(updatedConfig ?? '')
                }
              />
              {allRetrieverOptions && selectedRetriever?.key && (
                <Option
                  title="Retriever"
                  placeholder="Select Retriever..."
                  initialValue={selectedRetriever?.key}
                  data={allRetrieverOptions}
                  handleOnChange={(e) => {
                    const retriever = allRetrieverOptions.find(
                      (retriever) => retriever.key === e.target.value,
                    )
                    setSelectedRetriever(retriever)
                    setPromptTemplate(retriever?.promptTemplate)
                  }}
                />
              )}
              <div className="mb-1 mt-3 text-sm">Retrievers Configuration:</div>
              <SimpleCodeEditor
                language="json"
                height={140}
                value={retrieverConfig}
                onChange={(updatedConfig) =>
                  setRetrieverConfig(updatedConfig ?? '')
                }
              />

              <div className="flex justify-between items-center mt-1.5">
                <div className="text-sm">Internet Search</div>
                <Switch
                  checked={isInternetSearchEnabled}
                  onChange={(e) => setIsInternetSearchEnabled(e.target.checked)}
                />
              </div>

              <div className="mb-1 mt-2 text-sm">Prompt Template:</div>
              <TextareaAutosize
                className="w-full h-20 bg-[#f0f7ff] border border-[#CEE0F8] rounded-lg p-2 text-sm"
                placeholder="Enter Prompt Template..."
                minRows={3}
                value={promptTemplate}
                onChange={(e) => setPromptTemplate(e.target.value)}
              />
              <Button
                text="Create Application"
                className="w-full btn-sm mt-4"
                onClick={() => setIsCreateApplicationModalOpen(true)}
              />
            </div>
            <div className="h-full border rounded-lg border-[#CEE0F8] w-[calc(100%-25rem)] bg-white p-4">
              <Form
                setPrompt={setPrompt}
                handlePromptSubmit={handlePromptSubmit}
                isRunningPrompt={isRunningPrompt}
                prompt={prompt}
                selectedQueryModel={selectedQueryModel}
              />
              {answer ? (
                <Answer answer={answer} sourceDocs={sourceDocs} />
              ) : isRunningPrompt ? (
                <div className="overflow-y-auto flex flex-col justify-center items-center gap-2 h-[calc(100%-4.375rem)]">
                  <Spinner center medium />
                  <div className="text-center">Fetching Answer...</div>
                </div>
              ) : errorMessage ? (
                <ErrorAnswer />
              ) : (
                <NoAnswer />
              )}
            </div>
          </>
        ) : (
          <NoCollections fullWidth />
        )}
      </div>
    </>
  )
}

export default DocsQA
