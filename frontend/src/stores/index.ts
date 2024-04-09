import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'
import { configureStore, combineReducers } from '@reduxjs/toolkit'
import { setupListeners } from '@reduxjs/toolkit/query'

import { qafoundryApi } from './qafoundry'

const reducer = combineReducers({
  [qafoundryApi.reducerPath]: qafoundryApi.reducer,
})

const rootReducer: typeof reducer = (state, action) => {
  return reducer(state, action)
}

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }).concat([qafoundryApi.middleware]),
  devTools: import.meta.env.MODE !== 'default',
})

setupListeners(store.dispatch)

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
