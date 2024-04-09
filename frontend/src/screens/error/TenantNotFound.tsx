import React from 'react'
import icon from '@/assets/img/errors/404.svg'

const TenantNotFound = () => {
  return (
    <div className="w-full h-screen grid place-items-center">
      <div className="flex flex-col sm:flex-row gap-4 items-center sm:pb-72">
        <img src={icon} />
        <div className="divider sm:divider-horizontal" />
        <div className="flex flex-col gap-2">
          <h2 className="font-inter font-black text-6xl">Page unavailable</h2>
          <p className="font-semibold">
            Your Truefoundry site is currently unavailable.
            <br />
            If you think this is a mistake then please contact our support team.
            <br />
            <a
              className="link text-primary"
              href="mailto:support@truefoundry.com"
            >
              support@truefoundry.com
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default TenantNotFound
