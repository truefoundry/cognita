import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { Drawer } from '@mui/material'
import classNames from 'classnames'
import React, { useEffect, useMemo, useRef, useState } from 'react'
import Alert from '../molecules/modals/Alert'

type ContextType = {
  isPreventEscape?: boolean
  confirmOnClose?: boolean
  onEscape?: () => void
  updateDrawerContext?: (_?: ContextType, clearState?: boolean) => void
}

export const CustomDrawerContext = React.createContext<ContextType>({})

interface DrawerProps {
  children: React.ReactNode | JSX.Element | string
  anchor?: 'right' | 'left' | 'top' | 'bottom' | undefined
  open: boolean
  inner?: boolean
  size?: 'small' | 'medium' | 'large' | 'xlarge'
  width?: string
  bodyClassName?: string
  className?: string
  confirmOnClose?: boolean
  confirmOnCloseMessage?: string
  onClose: () => void
}

const CustomDrawer: React.FC<DrawerProps> = ({
  anchor = 'right',
  children,
  open,
  inner,
  size = 'medium',
  width,
  bodyClassName,
  className = '',
  confirmOnClose,
  confirmOnCloseMessage,
  onClose,
}) => {
  const [isCloseConfirmationOpen, setIsCloseConfirmationOpen] = useState(false)
  const [shouldConfirmOnClose, setShouldConfirmOnClose] =
    useState(confirmOnClose)

  const contextRef = useRef<ContextType>({})
  const contextValue = useMemo<ContextType>(
    () => ({
      updateDrawerContext: (state?: ContextType, clearState?: boolean) => {
        contextRef.current = clearState
          ? {}
          : { ...(contextRef.current ?? {}), ...state }
        if (state?.confirmOnClose !== shouldConfirmOnClose) {
          setShouldConfirmOnClose(state?.confirmOnClose)
        }
      },
    }),
    [shouldConfirmOnClose]
  )

  useEffect(() => {
    setShouldConfirmOnClose(confirmOnClose)
    if (!open) {
      setIsCloseConfirmationOpen(false)
    }
  }, [confirmOnClose, open])

  return (
    <>
      <Drawer
        anchor={anchor}
        open={open}
        onClose={
          inner
            ? shouldConfirmOnClose
              ? () => setIsCloseConfirmationOpen(true)
              : onClose
            : undefined
        }
        className={`feature-importance custom-drawer ${className}`}
        onKeyDown={(e) => {
          const { isPreventEscape, onEscape } = contextRef.current || {}
          if (e.key === 'Escape') {
            if (!isPreventEscape) {
              // TODO: Fix this, do not close drawer when escape is pressed
              // onClose()
            } else {
              onEscape?.()
            }
          }
        }}
        onClick={(e) => {
          e.stopPropagation()
        }}
      >
        <div className="flex overflow-hidden">
          <div className="flex-none h-[100vh] p-3 cursor-pointer ">
            {!inner && (
              <FontAwesomeIcon
                icon="close"
                className="text-3xl text-white bg-transparent"
                onClick={
                  shouldConfirmOnClose
                    ? () => setIsCloseConfirmationOpen(true)
                    : onClose
                }
              />
            )}
          </div>
          <div
            className={classNames(
              'flex-1 bg-gray-50 min-h-[100vh] feature-content',
              width ?? {
                'w-[46vw]': size === 'medium' && inner,
                'w-[52vw]': size === 'medium' && !inner,
                'w-[30vw]': size === 'small' && inner,
                'w-[35vw]': size === 'small' && !inner,
                'w-[65vw]': size === 'large' && inner,
                'w-[70vw]': size === 'large' && !inner,
                'w-[80vw]': size === 'xlarge' && inner,
                'w-[85vw]': size === 'xlarge' && !inner,
              },
            )}
          >
            {open && (
              <div
                className={classNames(
                  'h-full',
                  bodyClassName ?? 'my-3 mx-5 mb-1.5'
                )}
              >
                <CustomDrawerContext.Provider value={contextValue}>
                  {children}
                </CustomDrawerContext.Provider>
              </div>
            )}
          </div>
        </div>
      </Drawer>
      {shouldConfirmOnClose && (
        <Alert
          title="Warning"
          message={
            confirmOnCloseMessage ||
            'Closing this drawer will discard all changes. Are you sure you want to close it?'
          }
          onConfirm={async () => {
            setIsCloseConfirmationOpen(false)
          }}
          onClose={() => setIsCloseConfirmationOpen(false)}
          onCloseAfterConfirm={onClose}
          confirmButtonText="Yes"
          open={isCloseConfirmationOpen}
        />
      )}
    </>
  )
}

export default CustomDrawer
