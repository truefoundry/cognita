import React, { useState } from 'react'
import Modal, { ModalProps } from '../../atoms/Modal'
import Button, { ButtonProps } from '../../atoms/Button'
import classNames from 'classnames'
import Input from '../../atoms/Input'

export type AlertProps = Omit<ModalProps, 'children'> & {
  title: string
  message: string | JSX.Element | React.ReactNode
  onConfirm: () => Promise<void>
  onError?: (e: any) => void
  onCloseAfterConfirm?: () => void
  confirmButtonText?: string
  confirmString?: string
  confirmStringMessage?: string | JSX.Element
  confirmStringEntity?: string
  confirmButtonIcon?: ButtonProps['icon']
  confirmButtonClasses?: string
  confirmButtonDisabled?: boolean
  messageClasses?: string
  titleClasses?: string
  hideCancel?: boolean
  formClasses?: string
  onClose: (forced: boolean) => void
}

const Alert: React.FC<AlertProps> = ({
  title,
  message,
  onConfirm,
  onClose,
  onError,
  onCloseAfterConfirm,
  confirmString,
  confirmStringMessage,
  confirmStringEntity,
  confirmButtonText,
  confirmButtonIcon,
  confirmButtonClasses,
  confirmButtonDisabled,
  messageClasses,
  titleClasses,
  formClasses,
  hideCancel = false,
  ...rest
}) => {
  const [loading, setLoading] = useState(false)
  const [confirmInput, setConfirmInput] = useState('')
  const shouldDisable = confirmString ? confirmString !== confirmInput : false
  const onConfirmClick = async () => {
    if (shouldDisable) {
      return
    }
    setLoading(true)
    try {
      await onConfirm()
    } catch (e) {
      onError?.(e)
      setLoading(false)
      return
    }
    setLoading(false)
    onClose(false)
    onCloseAfterConfirm?.()
  }

  return (
    <Modal
      {...rest}
      onClose={() => {
        if (!loading) {
          onClose(false)
        }
      }}
    >
      <form
        className={classNames('modal-box p-4 rounded-lg', formClasses)}
        onSubmit={(e) => {
          e.stopPropagation()
          e.preventDefault()
          onConfirmClick()
        }}
      >
        <h3 className={classNames('font-bold text-xl', titleClasses)}>
          {title}
        </h3>
        {typeof message === 'string' ? (
          <div className={classNames('py-3 text-sm', messageClasses)}>
            {message}
          </div>
        ) : (
          message
        )}
        {confirmString && (
          <Input
            text={
              confirmStringMessage || (
                <>
                  Type{' '}
                  <span className="font-bold">
                    {confirmStringEntity || confirmString}
                  </span>{' '}
                  to continue:
                </>
              )
            }
            name="confirm-string"
            value={confirmInput}
            className="input-sm py-2"
            wrapperClasses="mt-1"
            onChange={(e) => setConfirmInput(e.target.value)}
          />
        )}
        <div className="modal-action mt-3">
          {!hideCancel && (
            <Button
              type="reset"
              outline
              text="Cancel"
              onClick={() => {
                onClose(true)
              }}
              disabled={loading}
              className="border-gray-500 gap-1 btn-sm font-normal"
            />
          )}
          <Button
            text={confirmButtonText || 'Yes'}
            icon={confirmButtonIcon}
            loading={loading}
            showTextWithLoader
            className={classNames('btn-sm', confirmButtonClasses)}
            disabled={shouldDisable || confirmButtonDisabled}
          />
        </div>
      </form>
    </Modal>
  )
}

export default Alert
