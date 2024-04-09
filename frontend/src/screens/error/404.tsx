import React from 'react'

import icon from '@/assets/img/errors/404.svg'
import ErrorPage from '@/components/base/molecules/ErrorPage'

const Unauthorized = () => {
  return (
    <ErrorPage
      statusCode={404}
      message="Oops, the page you’re looking for cannot be found."
      help={
        <>
          Try refreshing the page or email us at{' '}
          <a
            className="link text-primary"
            href="mailto:support@truefoundry.com"
          >
            support@truefoundry.com
          </a>
        </>
      }
      image={<img src={icon} />}
    />
  )
}

export default Unauthorized
