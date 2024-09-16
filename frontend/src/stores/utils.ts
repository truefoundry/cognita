import {
  BaseQueryFn,
  fetchBaseQuery,
  FetchBaseQueryError,
  FetchArgs,
} from '@reduxjs/toolkit/query'
import type { FetchBaseQueryArgs } from '@reduxjs/toolkit/dist/query/fetchBaseQuery'
import { logout } from './UserInfo'

import history from '../router/history'
import { RootState } from './index'

export function setAuthHeaderFromState(
  headers: Headers,
  state: RootState
): Headers {
  const token = state?.userInfo?.accessToken
  if (token) {
    headers.set('authorization', `Bearer ${token}`)
  }
  return headers
}

export function createBaseQuery(baseQueryArgs: FetchBaseQueryArgs) {
  const baseQuery = fetchBaseQuery({
    prepareHeaders: (headers, { getState }) => {
      return setAuthHeaderFromState(headers, getState() as RootState)
    },
    ...baseQueryArgs,
  })

  const baseQueryWithReauth: BaseQueryFn<
    string | FetchArgs,
    unknown,
    FetchBaseQueryError
  > = async (args, api, extraOptions) => {
    let result = await baseQuery(args, api, extraOptions)
    if (result.error?.status === 401) {
      api.dispatch(logout())
      history.replace("/login")
    }
    return result
  }

  return baseQueryWithReauth
}
