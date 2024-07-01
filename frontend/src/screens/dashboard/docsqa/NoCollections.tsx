import Button from '@/components/base/atoms/Button'
import React from 'react'
import { useNavigate } from 'react-router-dom'
import DocsQaInformation from './DocsQaInformation'

const NoCollections = ({ fullWidth }: { fullWidth?: boolean }) => {
  const navigate = useNavigate()

  return (
    <div
      className={`h-full border rounded-lg border-[#CEE0F8] ${
        fullWidth ? 'w-full' : 'w-[calc(100%-18.75rem)]'
      } bg-white flex items-center justify-center`}
    >
      <DocsQaInformation
        header={'Welcome to SambaQA'}
        subHeader={
          <>
            <p className="text-center max-w-[28.125rem] mt-2">
              Start building a QnA system on your internal knowledge
              <br /> base. Click “New Collection” button to connect your data
              <br /> and start a chat
            </p>
            <Button
              className="btn-sm text-sm mt-4 bg-black"
              text={'New Collection'}
              icon={'plus'}
              iconClasses="text-gray-400"
              onClick={() => navigate('/collections?newCollectionOpen=true')}
            />
          </>
        }
      />
    </div>
  )
}

export default NoCollections
