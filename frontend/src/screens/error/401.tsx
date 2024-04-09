import React from 'react'

import icon from '@/assets/img/errors/401.svg'
import ErrorPage from '@/components/base/molecules/ErrorPage'
import { useNavigate } from 'react-router-dom'

const Unauthorized = () => {
  const navigate = useNavigate()

  const url = localStorage.getItem('path_before_signin')
  if (!url) {
    navigate('/', { replace: true })
    return <></>
  }

  const handleClick: React.MouseEventHandler = async (e) => {
    e.preventDefault()
    navigate('/signin', { replace: true })
  }

  return (
    <ErrorPage
      statusCode={401}
      message="You do not have permission to access this page."
      help={
        <a className="link text-primary" href="/signin" onClick={handleClick}>
          Try logging in again.
        </a>
      }
      image={<img src={icon} />}
    />
  )
}

export default Unauthorized
