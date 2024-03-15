import React, { lazy } from 'react'
import type { BreadcrumbsRoute } from 'use-react-router-breadcrumbs'

import AppLayout from '@/layouts/AppLayout'

const Unauthorized = lazy(() => import('@/screens/error/401'))
export const NotFound = lazy(() => import('@/screens/error/404'))

const routes = (loggedIn: boolean): BreadcrumbsRoute[] => [
  {
    path: '/error',
    element: <AppLayout />,
    children: [
      {
        path: '401',
        element: <Unauthorized />,
      },
      {
        path: '*',
        element: <NotFound />,
      },
    ],
  },
]

export default routes
