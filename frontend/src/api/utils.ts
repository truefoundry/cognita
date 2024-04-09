import axios from 'axios'

export const instance = axios.create()

export function transformAxiosError(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.data?.message) {
    throw new Error(error.response.data.message)
  }
  throw error
}
