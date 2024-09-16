import jsCookie from 'js-cookie'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import history from '@/router/history'

export interface AuthState {
  accessToken?: string
  customerId?: string
}

const initialState: AuthState = {
  accessToken: jsCookie.get('accessToken'),
  customerId: jsCookie.get('customerId'),
}

export const removeAuthCookies = () => {
  jsCookie.remove('accessToken')
  jsCookie.remove('customerId')
}

export const UserInfoSlice = createSlice({
  name: 'userInfo',
  initialState,
  reducers: {
    login: (state, action: PayloadAction<{
      accessToken: string,
      customerId: string
    }>) => {
      state.accessToken = action.payload.accessToken
      state.customerId = action.payload.customerId
      jsCookie.set('accessToken', action.payload.accessToken, { expires: 1 })
      jsCookie.set('customerId', action.payload.customerId, { expires: 1 })
      // Redirect to the dashboard
      history.push('/');
    },
    logout: () => {
      removeAuthCookies()
    },
  },
})

export const { login, logout } = UserInfoSlice.actions


export default UserInfoSlice.reducer
