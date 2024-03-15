import React from 'react'

export type ErrorPageProps = {
  statusCode: number
  message: string
  help: JSX.Element
  image: JSX.Element
}

const ErrorPage: React.FC<ErrorPageProps> = ({
  image,
  statusCode,
  message,
  help,
}) => {
  return (
    <div className="w-full h-screen grid place-items-center">
      <div className="flex flex-col sm:flex-row gap-4 items-center sm:pb-72">
        {image}
        <div className="divider sm:divider-horizontal" />
        <div className="flex flex-col gap-2">
          <h2 className="font-lab font-black text-8xl">
            {statusCode} <span className="text-6xl">Error</span>
          </h2>
          <p className="font-semibold">
            {message}
            <br />
            {help}
          </p>
        </div>
      </div>
    </div>
  )
}

export default ErrorPage
