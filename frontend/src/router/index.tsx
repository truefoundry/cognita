import { Box } from '@mui/material'
import React from 'react'
import ReactDOM from 'react-dom'
import { usePromiseTracker } from 'react-promise-tracker'
import { useRoutes } from 'react-router-dom'
import type { BreadcrumbsRoute } from 'use-react-router-breadcrumbs'

import Spinner from '@/components/base/atoms/Spinner'
import docsQARoutes from './DocsQA'
import { NotFound } from './Error'

export const routes = (): BreadcrumbsRoute[] => [
  ...docsQARoutes(),
  {
    path: '*',
    element: <NotFound />,
  },
]

const PromiseLoading = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        zIndex: '1000',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'fixed',
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0,0,0,0.3)',
      }}
    >
      <Spinner big />
    </Box>
  )
}

const RouteComponent: React.FC = () => {
  const { promiseInProgress } = usePromiseTracker()
  const Routes = useRoutes(routes())

  const promiseLoadingView = document.getElementById('promise-loading')

  return (
    <>
      {promiseInProgress &&
        promiseLoadingView &&
        ReactDOM.createPortal(<PromiseLoading />, promiseLoadingView)}
      {Routes}
    </>
  )
}

export default RouteComponent
