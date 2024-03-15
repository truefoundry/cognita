import DocsDataPng from '@/assets/img/dgpt-docs.svg'
import SearchIcon from '@/assets/img/dgpt-search.svg'
import Button from '@/components/base/atoms/Button'
import React from 'react'
import { useNavigate } from 'react-router-dom'

const NoCollections = ({ notSelected }: { notSelected?: boolean }) => {
  const navigate = useNavigate()

  return (
    <div className="h-full border rounded-lg border-[#CEE0F8] w-[calc(100%-300px)] bg-white flex items-center justify-center">
      <div className="flex flex-col items-center">
        <p className="font-semibold text-[24px]">Welcome to DocsQA</p>
        {notSelected ? (
          <p className="text-center max-w-[450px] mt-2">
            Select a collection from sidebar
            <br /> and start asking Questions
          </p>
        ) : (
          <>
            <p className="text-center max-w-[450px] mt-2">
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
        )}
        <p className="text-center font-[700] text-xl mt-[50px] mb-4">
          How it works?
        </p>
        <div className="flex justify-center items-center">
          <div className="h-[160px] w-[160px] rounded-xl border border-gray-250 flex justify-center items-center flex-col pt-6">
            <img src={DocsDataPng} className="w-[73px]" />
            <p className="text-center font-[700] font-lab mt-4 mb-4">
              Your Data
            </p>
          </div>
          <div className="flex items-center">
            <div className="w-[40px] h-[1px] bg-black"></div>
            <div className="border w-0 h-0 border-t border-t-[transparent] border-t-[4px] border-b border-b-[transparent] border-b-[4px] border-l border-l-[6px] border-l-black"></div>
          </div>
          <div className="h-[160px] w-[160px] rounded-xl border border-gray-250 flex justify-end items-center flex-col pt-6">
            <img src={SearchIcon} className="h-[71px]" />
            <p className="text-center font-[700] font-lab mt-4 mb-4">DocsQA</p>
          </div>
          <div className="flex items-center">
            <div className="w-[40px] h-[1px] bg-black"></div>
            <div className="border w-0 h-0 border-t border-t-[transparent] border-t-[4px] border-b border-b-[transparent] border-b-[4px] border-l border-l-[6px] border-l-black"></div>
          </div>
          <div className="h-[160px] w-[160px] rounded-xl border border-gray-250 flex justify-end items-center flex-col pt-6">
            <div>
              <div className="w-[92px] py-1 rounded border border-gray-500 text-gray-600 text-center text-sm">
                Query
              </div>
              <div className="flex flex-col justify-center items-center">
                <div className="h-[10px] w-[1px] bg-black"></div>
                <div className="border w-0 h-0 border-l border-l-[transparent] border-l-[4px] border-r border-r-[transparent] border-r-[4px] border-t border-t-[6px] border-t-black"></div>
              </div>
              <div className="w-[92px] py-2 rounded border border-gray-500 text-center text-white text-sm bg-indigo-500">
                Response
              </div>
            </div>
            <p className="text-center font-[700] font-lab mt-2 mb-4">App</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NoCollections
