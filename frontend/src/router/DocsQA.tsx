import React, { Suspense, lazy } from 'react'
import { Outlet } from 'react-router-dom'
import type { BreadcrumbsRoute } from 'use-react-router-breadcrumbs'

import ScreenFallbackLoader from '@/components/base/molecules/ScreenFallbackLoader'
import DataHub from '@/screens/dashboard/docsqa/DataSources'
import NavBar from '@/screens/dashboard/docsqa/Navbar'
const DocsQA = lazy(() => import('@/screens/dashboard/docsqa'))
const DocsQASettings = lazy(() => import('@/screens/dashboard/docsqa/settings'))

const FallBack = () => (
  <div className="flex flex-1">
    <ScreenFallbackLoader />
  </div>
)

export const routes = (): BreadcrumbsRoute[] => [
  {
    path: '/',
    element: (
      <div className="flex flex-col h-full">
        <NavBar />
        <Suspense fallback={<FallBack />}>
          <div className="p-4 bg-[#fafcff] h-full">
            <Outlet />
          </div>
        </Suspense>
      </div>
    ),
    children: [
      {
        path: '/collections',
        children: [{ index: true, element: <DocsQASettings /> }],
      },
      {
        path: '/data-hub',
        children: [{ index: true, element: <DataHub /> }],
      },
      {
        path: '*',
        children: [{ index: true, element: <DocsQA /> }],
      },
    ],
  },
]

export default routes
