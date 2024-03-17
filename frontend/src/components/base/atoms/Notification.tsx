import React from 'react'

type toastProps = {
  title?: string
  msg?: string
  icon?: React.ReactNode | JSX.Element | string
}
export const Toast: React.FC<toastProps> = ({ title, msg, icon }) => {
  return (
    <div className="flex">
      {icon}
      <div>
        <h2 className="font-bold text-gray-1000 font-sans text-xl leading-6 mb-2">
          {title}
        </h2>
        <div className="text-xs font-normal text-gray-1000 font-sans text-base leading-5">
          {msg}
        </div>
      </div>
    </div>
  )
}
