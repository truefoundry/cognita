import IconProvider from '@/components/assets/IconProvider'
import Button from '@/components/base/atoms/Button'
import Input from '@/components/base/atoms/Input'
import Markdown from '@/components/base/atoms/Markdown'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
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
import { MenuItem, Select, Switch, TextareaAutosize } from '@mui/material'
import React, { useEffect, useMemo, useState } from 'react'
import NoCollections from './NoCollections'
import SimpleCodeEditor from '@/components/base/molecules/SimpleCodeEditor'
import DocsQaInformation from './DocsQaInformation'
import Modal from '@/components/base/atoms/Modal'
import notify from '@/components/base/molecules/Notify'
import { SSE } from 'sse.js'

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

const ExpandableText = ({
  text,
  maxLength,
}: {
  text: string
  maxLength: number
}) => {
  const [showAll, setShowAll] = useState(false)
  const displayText = showAll ? text : text.slice(0, maxLength)

  return (
    <p className="whitespace-pre-line inline">
      "{displayText}
      {displayText.length < text.length && !showAll && '...'}"
      {text.length > maxLength && (
        <span
          onClick={() => setShowAll((prev) => !prev)}
          className="text-blue-600 focus:outline-none ml-3 cursor-pointer"
        >
          {showAll ? 'Show less' : 'Show more'}
        </span>
      )}
    </p>
  )
}

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
  const [isStreamEnabled, setIsStreamEnabled] = useState(true)
  const [isCreateApplicationModalOpen, setIsCreateApplicationModalOpen] =
    useState(false)
  const [applicationName, setApplicationName] = useState('')

  const pattern = /^[a-z][a-z0-9-]*$/
  const isValidApplicationName = pattern.test(applicationName)

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
        },
        {}
      )
      if (!isStreamEnabled) {
        const res: any = await searchAnswer({
          ...params,
          stream: false,
          queryController: selectedQueryController,
        })
        if (res?.error) {
          setErrorMessage(true)
        } else {
          setAnswer(res.data.answer)
          setSourceDocs(res.data.docs ?? [])
        }
        setIsRunningPrompt(false)
      } else {
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
          }
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
          } catch (err) {}
        })

        sseRequest.addEventListener('end', (event: any) => {
          sseRequest.close()
        })
      }
    } catch (err: any) {
      setErrorMessage(true)
    }
  }

  const createChatApplication = async () => {
    const selectedModel = allEnabledModels.find(
      (model: any) => model.name == selectedQueryModel
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
      }).unwrap()
      setApplicationName('')
      setIsCreateApplicationModalOpen(false)
      notify('success', 'Application created successfully')
    } catch (err) {
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
      {isCreateApplicationModalOpen && (
        <Modal
          open={isCreateApplicationModalOpen}
          onClose={() => setIsCreateApplicationModalOpen(false)}
        >
          <div className="modal-box">
            <div className="text-center font-medium text-xl mb-2">
              Create Application
            </div>
            <div>
              <div className="text-sm">Enter the name of the application</div>
              <Input
                value={applicationName}
                onChange={(e) => setApplicationName(e.target.value)}
                className="py-1 input-sm mt-1"
                placeholder="E.g. query-bot"
              />
              {applicationName && !isValidApplicationName ? (
                <div className="text-sm text-error mt-1">
                  Application name should start with a lowercase letter and can
                  only contain lowercase letters, numbers and hyphens
                </div>
              ) : applicationName ? (
                <div className="text-sm mt-1">
                  The application name will be generated as{' '}
                  <span className="font-medium">
                    "{applicationName}-rag-app"
                  </span>
                </div>
              ) : (
                <></>
              )}
            </div>
            <div className="flex justify-end w-full mt-4 gap-2">
              <Button
                text="Create"
                className="btn-sm"
                loading={isCreateApplicationLoading}
                onClick={createChatApplication}
              />
              <Button
                text="Cancel"
                className="btn-sm bg-red-600 hover:bg-red-700 border-0"
                onClick={() => setIsCreateApplicationModalOpen(false)}
              />
            </div>
          </div>
        </Modal>
      )}
      <div className="flex gap-5 h-[calc(100vh-6.5rem)] w-full">
        {isCollectionsLoading ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : selectedCollection ? (
          <>
            <div className="h-full border rounded-lg border-[#CEE0F8] w-[23.75rem] bg-white p-4 overflow-auto">
              <div className="flex justify-between items-center mb-1">
                <div className="text-sm">Collection:</div>
                <Select
                  value={selectedCollection}
                  onChange={(e) => {
                    resetQA()
                    setSelectedCollection(e.target.value)
                  }}
                  placeholder="Select Collection..."
                  sx={{
                    background: 'white',
                    height: '2rem',
                    width: '13.1875rem',
                    border: '1px solid #CEE0F8 !important',
                    outline: 'none !important',
                    '& fieldset': {
                      border: 'none !important',
                    },
                  }}
                >
                  {collections?.map((collection: any) => (
                    <MenuItem value={collection} key={collection}>
                      {collection}
                    </MenuItem>
                  ))}
                </Select>
              </div>
              <div className="flex justify-between items-center mb-1 mt-3">
                <div className="text-sm">Query Controller:</div>
                <Select
                  value={selectedQueryController}
                  onChange={(e) => {
                    setSelectedQueryController(e.target.value)
                  }}
                  placeholder="Select Query Controller..."
                  sx={{
                    background: 'white',
                    height: '2rem',
                    width: '13.1875rem',
                    border: '1px solid #CEE0F8 !important',
                    outline: 'none !important',
                    '& fieldset': {
                      border: 'none !important',
                    },
                  }}
                >
                  {allQueryControllers?.map((retriever: any) => (
                    <MenuItem value={retriever} key={retriever}>
                      {retriever}
                    </MenuItem>
                  ))}
                </Select>
              </div>
              <div className="flex justify-between items-center mb-1 mt-3">
                <div className="text-sm">Model:</div>
                <Select
                  value={selectedQueryModel}
                  onChange={(e) => {
                    setSelectedQueryModel(e.target.value)
                  }}
                  placeholder="Select Model..."
                  sx={{
                    background: 'white',
                    height: '2rem',
                    width: '13.1875rem',
                    border: '1px solid #CEE0F8 !important',
                    outline: 'none !important',
                    '& fieldset': {
                      border: 'none !important',
                    },
                  }}
                >
                  {allEnabledModels?.map((model: any) => (
                    <MenuItem value={model.name} key={model.name}>
                      {model.name}
                    </MenuItem>
                  ))}
                </Select>
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
                <div>
                  <div className="mb-1 mt-3 text-sm">Retriever:</div>
                  <Select
                    value={selectedRetriever?.key}
                    onChange={(e) => {
                      const retriever = allRetrieverOptions.find(
                        (retriever) => retriever.key === e.target.value
                      )
                      setSelectedRetriever(retriever)
                      setPromptTemplate(retriever?.promptTemplate)
                    }}
                    placeholder="Select Retriever..."
                    sx={{
                      background: 'white',
                      height: '1.875rem',
                      width: '100%',
                      border: '1px solid #CEE0F8 !important',
                      outline: 'none !important',
                      '& fieldset': {
                        border: 'none !important',
                      },
                      fontSize: '0.875rem',
                    }}
                  >
                    {allRetrieverOptions?.map((retriever: any) => (
                      <MenuItem value={retriever.key} key={retriever.key}>
                        {retriever.summary}
                      </MenuItem>
                    ))}
                  </Select>
                </div>
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
                <div className="text-sm">Stream</div>
                <Switch
                  checked={isStreamEnabled}
                  onChange={(e) => setIsStreamEnabled(e.target.checked)}
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
              <div className="flex gap-4 items-center">
                <div className="w-full relative">
                  <Input
                    className="w-full h-[2.75rem] text-sm pr-14"
                    placeholder="Ask any question related to this document"
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
              {answer ? (
                <div className="overflow-y-auto flex flex-col gap-4 mt-7 h-[calc(100%-70px)]">
                  <div className="max-h-[60%] h-full overflow-y-auto flex gap-4">
                    <div className="bg-indigo-400 w-6 h-6 rounded-full flex items-center justify-center mt-0.5">
                      <IconProvider icon="message" className="text-white" />
                    </div>
                    <div className="w-full font-inter text-base">
                      <div className="font-bold text-lg">Answer:</div>
                      <Markdown>{answer}</Markdown>
                    </div>
                  </div>
                  {sourceDocs && (
                    <div className="bg-gray-100 rounded-md w-full p-4 py-3 h-full overflow-y-auto border border-blue-500">
                      <div className="font-semibold mb-3.5">
                        Source Documents:
                      </div>
                      {sourceDocs?.map((doc, index) => {
                        const splittedFqn =
                          doc?.metadata?._data_point_fqn.split('::')
                        const pageNumber =
                          doc?.metadata?.page_number || doc?.metadata?.page_num
                        const relevanceScore = doc?.metadata?.relevance_score
                        return (
                          <div key={index} className="mb-3">
                            <div className="text-sm">
                              {index + 1}.{' '}
                              <ExpandableText
                                text={doc.page_content}
                                maxLength={250}
                              />
                            </div>
                            {relevanceScore && (
                              <div className="text-sm text-indigo-600 mt-1">
                                Relevance Score: {relevanceScore}
                              </div>
                            )}
                            <div className="text-sm text-indigo-600 mt-1">
                              Source: {splittedFqn?.[splittedFqn.length - 1]}
                              {pageNumber && `, Page No.: ${pageNumber}`}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              ) : isRunningPrompt ? (
                <div className="overflow-y-auto flex flex-col justify-center items-center gap-2 h-[calc(100%-4.375rem)]">
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
                  <div className="min-h-[23rem]">
                    <DocsQaInformation
                      header={'Welcome to DocsQA'}
                      subHeader={
                        <>
                          <p className="text-center max-w-[28.125rem] mt-2">
                            Select a collection from sidebar,
                            <br /> review all the settings and start asking
                            Questions
                          </p>
                        </>
                      }
                    />
                  </div>
                </div>
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
