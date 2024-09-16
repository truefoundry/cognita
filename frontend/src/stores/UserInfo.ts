import jsCookie from 'js-cookie'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import history from '@/router/history'

export interface AuthState {
  accessToken?: string
  customerId?: string
}

const initialState: AuthState = {}

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
