import React from 'react'

import icon from '@/assets/img/errors/500.svg'
import ErrorPage from '@/components/base/molecules/ErrorPage'

const Failure = () => {
  return (
    <ErrorPage
      statusCode={500}
      message="Looks like something went wrong!"
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

export default Failure
