import React from 'react'

import Spinner from '@/components/base/atoms/Spinner/Spinner'
import ApplicationModal from './components/ApplicationModal'
import NoCollections from '../NoCollections'
import { useDocsQAContext } from './context'
import Left from './components/Left'
import Right from './components/Right'

const DocsQA = () => {
  const {
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
  } = useDocsQAContext()

  return (
    <>
      <ApplicationModal />
      <div className="flex gap-5 h-[calc(100vh-6.5rem)] w-full">
        {isCollectionsLoading ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : selectedCollection ? (
          <>
            <Left />
            <Right />
          </>
        ) : (
          <NoCollections fullWidth />
        )}
      </div>
    </>
  )
}

export default DocsQA
