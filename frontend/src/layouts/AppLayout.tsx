import React, { Suspense } from 'react'
import { Outlet } from 'react-router-dom'

import Spinner from '@/components/base/atoms/Spinner'

const AppLayout = () => {
  return (
    <div className="flex h-screen bg-app overflow-hidden relative">
      <Suspense
        fallback={
          <div className="w-full grid place-items-center">
            <Spinner big />
          </div>
        }
      >
        <div className="p-4 grow h-full overflow-y-auto custom-scrollbar">
          <Outlet />
        </div>
      </Suspense>
    </div>
  )
}

export default AppLayout
