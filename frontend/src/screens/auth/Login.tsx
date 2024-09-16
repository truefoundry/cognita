import Button from '@/components/base/atoms/Button'
import React from 'react'
import { baseQAFoundryPath } from '@/stores/qafoundry'

type Props = {}

const Login = (props: Props) => {
  const handleClick = async () => {
    window.location.href = `${baseQAFoundryPath}/v1/auth/login`
  }
  return (
    <div className='grid items-center h-full'>
      <div className='p-6 bg-gray-100 mx-auto flex flex-col rounded'>
        <h1 className='text-2xl font-bold text-center mb-4 text-left'>Login</h1>
        <Button
          icon="fa-brands fa-google"
          text="Login With Google"
          onClick={handleClick}
          className="border-gray-500 gap-1 btn-sm font-normal"
        />
      </div>
    </div>
  )
}

export default Login
