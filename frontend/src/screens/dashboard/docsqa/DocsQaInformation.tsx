import DocsDataPng from '@/assets/img/dgpt-docs.svg'
import SearchIcon from '@/assets/img/dgpt-search.svg'
import React from 'react'

interface DocsQaInformationProps {
  header: JSX.Element | string
  subHeader: JSX.Element | string
}

const DocsQaInformation = ({ header, subHeader }: DocsQaInformationProps) => {
  return (
    <div className="flex flex-col items-center">
      <p className="font-semibold text-[1.5rem]">{header}</p>
      {subHeader}
      <p className="text-center font-[700] text-xl mt-[3.125rem] mb-4">
        How it works?
      </p>
      <div className="flex justify-center items-center">
        <div className="h-[10rem] w-[10rem] rounded-xl border border-gray-250 flex justify-center items-center flex-col pt-6">
          <img src={DocsDataPng} className="w-[4.5625rem]" />
          <p className="text-center font-[700] font-inter mt-4 mb-4">
            Your Data
          </p>
        </div>
        <div className="flex items-center">
          <div className="w-[2.5rem] h-[0.0625rem] bg-black"></div>
          <div className="border w-0 h-0 border-t-[transparent] border-t-[0.25rem] border-b-[transparent] border-b-[0.25rem] border-l-[0.375rem] border-l-black"></div>
        </div>
        <div className="h-[10rem] w-[10rem] rounded-xl border border-gray-250 flex justify-end items-center flex-col pt-6">
          <img src={SearchIcon} className="h-[70.0625rem]" />
          <p className="text-center font-[700] font-inter mt-4 mb-4">DocsQA</p>
        </div>
        <div className="flex items-center">
          <div className="w-[2.5rem] h-[0.0625rem] bg-black"></div>
          <div className="border w-0 h-0 border-t-[transparent] border-t-[0.25rem] border-b-[transparent] border-b-[0.25rem] border-l-[0.375rem] border-l-black"></div>
        </div>
        <div className="h-[10rem] w-[10rem] rounded-xl border border-gray-250 flex justify-end items-center flex-col pt-6">
          <div>
            <div className="w-[5.75rem] py-1 rounded border border-gray-500 text-gray-600 text-center text-sm">
              Query
            </div>
            <div className="flex flex-col justify-center items-center">
              <div className="h-[0.625rem] w-[0.0625rem] bg-black"></div>
              <div className="border w-0 h-0 border-l-[transparent] border-l-[0.25rem] border-r-[transparent] border-r-[0.25rem] border-t-[0.375rem] border-t-black"></div>
            </div>
            <div className="w-[5.75rem] py-2 rounded border border-gray-500 text-center text-white text-sm bg-indigo-500">
              Response
            </div>
          </div>
          <p className="text-center font-[700] font-inter mt-2 mb-4">App</p>
        </div>
      </div>
    </div>
  )
}

export default DocsQaInformation
