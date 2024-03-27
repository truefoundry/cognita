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
      <p className="font-semibold text-[24px]">{header}</p>
      {subHeader}
      <p className="text-center font-[700] text-xl mt-[50px] mb-4">
        How it works?
      </p>
      <div className="flex justify-center items-center">
        <div className="h-[160px] w-[160px] rounded-xl border border-gray-250 flex justify-center items-center flex-col pt-6">
          <img src={DocsDataPng} className="w-[73px]" />
          <p className="text-center font-[700] font-inter mt-4 mb-4">
            Your Data
          </p>
        </div>
        <div className="flex items-center">
          <div className="w-[40px] h-[1px] bg-black"></div>
          <div className="border w-0 h-0 border-t border-t-[transparent] border-t-[4px] border-b border-b-[transparent] border-b-[4px] border-l border-l-[6px] border-l-black"></div>
        </div>
        <div className="h-[160px] w-[160px] rounded-xl border border-gray-250 flex justify-end items-center flex-col pt-6">
          <img src={SearchIcon} className="h-[71px]" />
          <p className="text-center font-[700] font-inter mt-4 mb-4">DocsQA</p>
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
          <p className="text-center font-[700] font-inter mt-2 mb-4">App</p>
        </div>
      </div>
    </div>
  )
}

export default DocsQaInformation