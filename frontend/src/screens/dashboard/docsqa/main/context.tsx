import React, {
  createContext,
  useState,
  useEffect,
  useMemo,
  ReactNode,
  useContext,
} from 'react'
import { SSE } from 'sse.js'

import {
  CollectionQueryDto,
  SourceDocs,
  baseQAFoundryPath,
  useCreateApplicationMutation,
  useGetAllEnabledChatModelsQuery,
  useGetCollectionNamesQuery,
  useGetOpenapiSpecsQuery,
} from '@/stores/qafoundry'

import { notifyError } from '@/utils/error'
import notify from '@/components/base/molecules/Notify'

import { DocsQAContextType, SelectedRetrieverType } from './types'

interface DocsQAProviderProps {
  children: ReactNode
}

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

const DocsQAContext = createContext<DocsQAContextType | undefined>(undefined)

export const DocsQAProvider: React.FC<DocsQAProviderProps> = ({ children }) => {
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
    if (collections && collections.length) setSelectedCollection(collections[0])

    if (allQueryControllers && allQueryControllers.length)
      setSelectedQueryController(allQueryControllers[0])

    if (allEnabledModels && allEnabledModels.length)
      setSelectedQueryModel(allEnabledModels[0].name)

    if (allRetrieverOptions && allRetrieverOptions.length) {
      setSelectedRetriever(allRetrieverOptions[0])
      setPromptTemplate(allRetrieverOptions[0].promptTemplate)
    }
    if (selectedRetriever)
      setRetrieverConfig(JSON.stringify(selectedRetriever.config, null, 2))
  }, [
    collections,
    allQueryControllers,
    allEnabledModels,
    allRetrieverOptions,
    selectedRetriever,
  ])

  const value = {
    selectedQueryModel,
    setSelectedQueryModel,
    selectedCollection,
    setSelectedCollection,
    selectedQueryController,
    setSelectedQueryController,
    selectedRetriever,
    setSelectedRetriever,
    prompt,
    setPrompt,
    isRunningPrompt,
    setIsRunningPrompt,
    answer,
    setAnswer,
    sourceDocs,
    setSourceDocs,
    errorMessage,
    setErrorMessage,
    modelConfig,
    setModelConfig,
    retrieverConfig,
    setRetrieverConfig,
    promptTemplate,
    setPromptTemplate,
    isInternetSearchEnabled,
    setIsInternetSearchEnabled,
    isCreateApplicationModalOpen,
    setIsCreateApplicationModalOpen,
    collections,
    isCollectionsLoading,
    allEnabledModels,
    allQueryControllers,
    allRetrieverOptions,
    handlePromptSubmit,
    resetQA,
    isCreateApplicationLoading,
    createChatApplication,
  }

  return (
    <DocsQAContext.Provider value={value}>{children}</DocsQAContext.Provider>
  )
}

export const useDocsQAContext = () => {
  const context = useContext(DocsQAContext)
  if (!context) {
    throw new Error('useDocsQAContext must be used within a DocsQAProvider')
  }
  return context
}
