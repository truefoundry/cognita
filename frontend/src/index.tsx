import dayjs from 'dayjs/esm'
import duration from 'dayjs/esm/plugin/duration'
import LocalizedFormat from 'dayjs/esm/plugin/localizedFormat'
import relativeTime from 'dayjs/esm/plugin/relativeTime'
import React, { lazy, Suspense } from 'react'
import ReactDOM from 'react-dom'
import { ErrorBoundary } from 'react-error-boundary'
import { HelmetProvider } from 'react-helmet-async'
import { Provider } from 'react-redux'

import App from './App'
import './index.scss'
import reportWebVitals from './reportWebVitals'
import { store } from './stores'

import Spinner from './components/base/atoms/Spinner'

const Failure = lazy(() => import('@/screens/error/500'))

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.extend(LocalizedFormat)

const helmetContext = {}

const renderFallback = () => (
  <Suspense
    fallback={
      <div className="grid w-screen h-screen place-items-center">
        <Spinner big />
      </div>
    }
  >
    <Failure />
  </Suspense>
)

ReactDOM.render(
  <React.StrictMode>
    <ErrorBoundary fallback={renderFallback()}>
      <HelmetProvider context={helmetContext}>
        <Provider store={store}>
          <App />
        </Provider>
      </HelmetProvider>
    </ErrorBoundary>
  </React.StrictMode>,
  document.getElementById('app')
)

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an VITE_ANALYTICS endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals()
