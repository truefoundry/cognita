import React from 'react'
import { toast } from 'react-toastify'
import { Toast } from '@/components/base/atoms/Notification'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'

export default function notify(
  type: 'info' | 'success' | 'error',
  title: string,
  message?: string | JSX.Element,
  toastId?: string | number
) {
  let icon
  switch (type) {
    case 'info':
      icon = (
        <FontAwesomeIcon
          icon="info"
          className="text-purple-600 text-2xl mr-4 mt-0.5"
        />
      )
      toast.info(<Toast title={title} msg={message} icon={icon} />, { toastId })
      break
    case 'success':
      icon = (
        <FontAwesomeIcon
          icon="check"
          className="text-blue-600 text-2xl mr-4 mt-0.5"
        />
      )
      toast.success(<Toast title={title} msg={message} icon={icon} />, {
        toastId,
      })
      break
    case 'error':
      icon = (
        <FontAwesomeIcon
          icon="close"
          className="text-red-600 text-2xl mr-4 mt-0.5"
        />
      )
      toast.error(<Toast title={title} msg={message} icon={icon} />, {
        toastId,
      })
      break
    default:
      toast(<Toast title={title} msg={message} icon={icon} />, { toastId })
      break
  }
}
