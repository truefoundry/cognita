import React, { useState } from 'react'

import Spinner from '@/components/base/atoms/Spinner/Spinner'
import ApplicationModal from './components/ApplicationModal'
import NoCollections from '../NoCollections'
import { useDocsQAContext } from './context'
import ConfigSidebar from './components/ConfigSidebar'
import Chat from './components/Chat'

const DocsQA = () => {
  const { selectedCollection, isCollectionsLoading } = useDocsQAContext()

  const [isCreateApplicationModalOpen, setIsCreateApplicationModalOpen] =
    useState(false)

  return (
    <>
      {isCreateApplicationModalOpen && (
        <ApplicationModal
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
            <ConfigSidebar
              setIsCreateApplicationModalOpen={setIsCreateApplicationModalOpen}
            />
            <Chat />
          </>
        ) : (
          <NoCollections fullWidth />
        )}
      </div>
    </>
  )
}

export default DocsQA
