import {
  BaseQueryFn,
  fetchBaseQuery,
  FetchBaseQueryError,
  FetchArgs,
} from '@reduxjs/toolkit/query'
import type { FetchBaseQueryArgs } from '@reduxjs/toolkit/dist/query/fetchBaseQuery'
import { Mutex } from 'async-mutex'

const reauthMutex = new Mutex()

export function createBaseQuery(baseQueryArgs: FetchBaseQueryArgs) {
  const baseQuery = fetchBaseQuery({
    prepareHeaders: (headers, { getState }) => {
      return headers
    },
    ...baseQueryArgs,
  })

  const baseQueryWithReauth: BaseQueryFn<
    string | FetchArgs,
    unknown,
    FetchBaseQueryError
  > = async (args, api, extraOptions) => {
    await reauthMutex.waitForUnlock()
    let result = await baseQuery(args, api, extraOptions)
    if (result.error) {
      if (result.error.status === 401) {
        await reauthMutex.waitForUnlock()
        result = await baseQuery(args, api, extraOptions)
      }
    }
    return result
  }

  return baseQueryWithReauth
}
