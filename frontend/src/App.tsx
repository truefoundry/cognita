import React, { Suspense, useEffect } from 'react'
// This is currently unstable but may change in the future, see https://reactrouter.com/docs/en/v6/routers/history-router for more info
import { unstable_HistoryRouter as HistoryRouter } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import { ThemeProvider } from '@mui/material/styles'

import './fontawesome'

import AppRoutes from '@/router'
import theme from './materialTheme'
import Fallback from './components/base/molecules/ScreenFallbackLoader'
import history from './router/history'
import { DOCS_QA_STANDALONE_PATH, GTAG_ID } from './stores/constants'
import Head from './Head'

const getBaseName = () => {
  return DOCS_QA_STANDALONE_PATH ? '/' + DOCS_QA_STANDALONE_PATH : undefined
}

function App() {
  // disable scroll on number inputs
  useEffect(() => {
    const onWheel = () => {
      const ele = document.activeElement as any
      if (ele?.type === 'number') {
        ele?.blur()
      }
    }
    document.addEventListener('wheel', onWheel)
    return () => {
      document.removeEventListener('wheel', onWheel)
    }
  }, [])

  return (
    <ThemeProvider theme={theme}>
      {GTAG_ID && <Head />}
      <Suspense fallback={<Fallback />}>
        <HistoryRouter history={history} basename={getBaseName()}>
          <AppRoutes />
        </HistoryRouter>
      </Suspense>
      <ToastContainer
        position="bottom-center"
        autoClose={2000}
        hideProgressBar={true}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable={false}
        pauseOnHover
        icon={false}
      />
    </ThemeProvider>
  )
}

export default App
