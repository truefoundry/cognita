import { MenuItem, Switch, TextareaAutosize } from '@mui/material'
import React from 'react'

import SimpleCodeEditor from '@/components/base/molecules/SimpleCodeEditor'
import ConfigSelector from './ConfigSelector'
import Button from '@/components/base/atoms/Button'
import { useDocsQAContext } from '../context'

const defaultModelConfig = `{
  "parameters": {
    "temperature": 0.1
  }
}`

const Left = () => {
  const {
    selectedCollection,
    selectedQueryController,
    selectedQueryModel,
    selectedRetriever,
    retrieverConfig,
    promptTemplate,
    isInternetSearchEnabled,
    collections,
    allQueryControllers,
    allEnabledModels,
    allRetrieverOptions,
    setSelectedQueryModel,
    setIsInternetSearchEnabled,
    setSelectedCollection,
    setSelectedQueryController,
    setSelectedRetriever,
    setModelConfig,
    setRetrieverConfig,
    setPromptTemplate,
    setIsCreateApplicationModalOpen,
    resetQA,
  } = useDocsQAContext()

  return (
    <div className="h-full border rounded-lg border-[#CEE0F8] w-[23.75rem] bg-white p-4 overflow-auto">
      <div className="flex flex-col gap-3">
        <ConfigSelector
          title="Collection"
          placeholder="Select Collection..."
          initialValue={selectedCollection}
          data={collections}
          handleOnChange={(e) => {
            resetQA()
            setSelectedCollection(e.target.value)
          }}
        />
        <ConfigSelector
          title="Query Controller"
          placeholder="Select Query Controller..."
          initialValue={selectedQueryController}
          data={allQueryControllers}
          handleOnChange={(e) => {
            resetQA()
            setSelectedQueryController(e.target.value)
          }}
        />
        <ConfigSelector
          title="Model"
          placeholder="Select Model..."
          initialValue={selectedQueryModel}
          data={allEnabledModels}
          handleOnChange={(e) => {
            resetQA()
            setSelectedQueryModel(e.target.value)
          }}
          renderItem={(item) => (
            <MenuItem key={item.name} value={item.name}>
              {item.name}
            </MenuItem>
          )}
        />
      </div>

      <div className="mb-1 mt-3 text-sm">Model Configuration:</div>
      <SimpleCodeEditor
        language="json"
        height={130}
        defaultValue={defaultModelConfig}
        onChange={(updatedConfig) => setModelConfig(updatedConfig ?? '')}
      />
      {allRetrieverOptions && selectedRetriever?.key && (
        <ConfigSelector
          title="Retriever"
          placeholder="Select Retriever..."
          initialValue={selectedRetriever?.summary}
          data={allRetrieverOptions}
          className="mt-4"
          handleOnChange={(e) => {
            const retriever = allRetrieverOptions.find(
              (retriever) => retriever.key === e.target.value,
            )
            setSelectedRetriever(retriever)
            setPromptTemplate(retriever?.promptTemplate)
          }}
          renderItem={(item) => (
            <MenuItem key={item.key} value={item.summary}>
              {item.summary}
            </MenuItem>
          )}
        />
      )}
      <div className="mb-1 mt-3 text-sm">Retrievers Configuration:</div>
      <SimpleCodeEditor
        language="json"
        height={140}
        value={retrieverConfig}
        onChange={(updatedConfig) => setRetrieverConfig(updatedConfig ?? '')}
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
  )
}

export default Left
