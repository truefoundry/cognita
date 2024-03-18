import IconProvider from '@/components/assets/IconProvider'
import Button from '@/components/base/atoms/Button'
import Input from '@/components/base/atoms/Input'
import Markdown from '@/components/base/atoms/Markdown'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import {
  CollectionQueryDto,
  useGetAllEnabledChatModelsQuery,
  useGetCollectionsQuery,
  useQueryCollectionMutation,
} from '@/stores/qafoundry'
import { MenuItem, Select } from '@mui/material'
import React, { useEffect, useState } from 'react'
import CollectionCard from './CollectionCard'
import NoCollections from './NoCollections'

const DocsQA = () => {
  const [selectedQueryModel, setSelectedQueryModel] = React.useState('')
  const [selectedCollection, setSelectedCollection] = useState('')
  const [prompt, setPrompt] = useState('')
  const [isRunningPrompt, setIsRunningPrompt] = useState(false)
  const [answer, setAnswer] = useState('')
  const [errorMessage, setErrorMessage] = useState(false)

  const { data: collections, isLoading } = useGetCollectionsQuery()
  const { data: allEnabledModels } = useGetAllEnabledChatModelsQuery()
  const [searchAnswer] = useQueryCollectionMutation()

  const handlePromptSubmit = async () => {
    setIsRunningPrompt(true)
    setAnswer('')
    setErrorMessage(false)
    try {
      const selectedModel = allEnabledModels.find(
        (model: any) => model.id == selectedQueryModel
      )
      if (!selectedModel) {
        throw new Error('Model not found')
      }
      const name = `${selectedModel?.provider_account_name}/${selectedModel?.name}`
      const params: CollectionQueryDto = Object.assign(
        {
          collection_name: selectedCollection,
          query: prompt,
          model_configuration: {
            name: name,
          },
          retrieval_chain_name: 'CustomRetrievalQA',
          retriever_config: {
            class_name: 'VectorStoreRetriever',
            search_type: 'mmr',
            k: 4,
            fetch_k: 20,
            filter: {},
          },
        },
        {}
      )
      const res: any = await searchAnswer(params)
      if (res?.error) {
        setErrorMessage(true)
      } else {
        setAnswer(res.data.answer)
      }
    } catch (err: any) {
      setErrorMessage(true)
    }
    setIsRunningPrompt(false)
  }

  useEffect(() => {
    if (allEnabledModels && allEnabledModels.length) {
      setSelectedQueryModel(allEnabledModels[0].id)
    }
  }, [allEnabledModels])

  return (
    <>
      <div className="flex gap-5 h-[calc(100vh-104px)] w-full">
        <div className="h-full border rounded-lg border-[#CEE0F8] py-5 pt-3 w-[280px] bg-[#f4f9ff]">
          <div className="font-semibold text-lg mb-1 px-5">Collections</div>
          <hr className="mb-2" />
          <div
            className="h-[calc(100vh-162px)] overflow-y-auto custom-scrollbar"
            style={{
              paddingRight: '0rem',
            }}
          >
            {isLoading && <Spinner center />}
            {collections?.map((collection, index) => (
              <CollectionCard
                key={index}
                collectionName={collection.name}
                enableErrorSelection
                embedderConfig={collection.embedder_config}
                isSelectedCollection={selectedCollection === collection.name}
                onClick={() => {
                  setPrompt('')
                  setAnswer('')
                  setErrorMessage(false)
                  setSelectedCollection(collection.name)
                }}
              />
            ))}
          </div>
        </div>
        {selectedCollection ? (
          <div className="h-full border rounded-lg border-[#CEE0F8] w-[calc(100%-300px)] bg-white p-4">
            <div className="flex gap-4 items-center">
              <div className="w-full relative">
                <Input
                  className="w-[100%] h-[44px] text-sm pr-14"
                  placeholder="Ask any question related to this document"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                />
                <Button
                  icon="paper-plane-top"
                  className="btn-sm absolute right-2 top-[6px]"
                  onClick={handlePromptSubmit}
                  loading={isRunningPrompt}
                  disabled={!prompt || !selectedQueryModel}
                />
              </div>
              <Select
                id="datasets"
                value={selectedQueryModel}
                onChange={(e) => {
                  setSelectedQueryModel(e.target.value)
                }}
                placeholder="Select Model..."
                sx={{
                  background: 'white',
                  height: '42px',
                  width: '12rem',
                  minWidth: '12rem',
                  border: '1px solid #CEE0F8 !important',
                  outline: 'none !important',
                  '& fieldset': {
                    border: 'none !important',
                  },
                }}
              >
                {allEnabledModels?.map((model: any) => (
                  <MenuItem value={model.id} key={model.id}>
                    {model.provider_account_name}/{model.name}
                  </MenuItem>
                ))}
              </Select>
            </div>
            {answer && (
              <div className="overflow-y-auto flex gap-4 mt-7">
                <div className="bg-indigo-400 w-6 h-6 rounded-full flex items-center justify-center mt-0.5">
                  <IconProvider icon="message" className="text-white" />
                </div>
                <div className="w-full font-inter text-base">
                  <div className="font-bold text-lg">Answer</div>
                  <Markdown>{answer}</Markdown>
                </div>
              </div>
            )}
            {errorMessage && (
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
            )}
          </div>
        ) : (!collections && !isLoading) ? (
          <NoCollections />
        ) : (
          <NoCollections notSelected />
        )}
      </div>
    </>
  )
}

export default DocsQA
