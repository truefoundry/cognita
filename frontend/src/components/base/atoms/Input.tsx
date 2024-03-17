import IconProvider from '@/components/assets/IconProvider'
import { mergeRefs } from '@/utils'
import useId from '@mui/material/utils/useId'
import classNames from 'classnames'
import React, { useEffect, useRef, useState } from 'react'
import { DarkTooltip } from './Tooltip'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  text?: string | JSX.Element
  wrapperClasses?: string
  labelClasses?: string
}

const ErrorTooltip: React.FC<{ errMessage: string }> = ({ errMessage }) => {
  const [forceShowTooltip, setForceShowTooltip] = useState(false)

  useEffect(() => {
    setForceShowTooltip(true)
    const timer = setTimeout(() => {
      setForceShowTooltip(false)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <DarkTooltip
      title={errMessage}
      placement="bottom"
      key={forceShowTooltip ? 'force-show' : 'hover-show'}
      open={forceShowTooltip || undefined}
      componentsProps={{
        tooltip: {
          sx: {
            '&&&': {
              marginTop: '0.5rem',
              color: 'pink',
            },
          },
        },
      }}
    >
      <span
        className={classNames(
          'text-xs font-medium text-rose-600',
          'absolute top-0 right-0 h-8 w-8',
          'inline-flex items-center justify-center'
        )}
      >
        <IconProvider
          icon={'fa-warning'}
          className="px-1 pt-0.5 text-rose-500"
        />
      </span>
    </DarkTooltip>
  )
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      text,
      className,
      wrapperClasses = '',
      labelClasses = '',
      placeholder,
      readOnly,
      onChange,
      ...nativeProps
    },
    ref
  ) => {
    const inputRef = useRef<HTMLInputElement>(null)
    const fallbackId = useId()
    const id = nativeProps.id || fallbackId

    const inputClasses = classNames(
      'input border-blue-500 dark:bg-neutral border w-full bg-gray-100 focus:outline-none',
      'dark:placeholder:text-gray-300 font-500 leading-4 font-lab p-3 placeholder-gray-450',
      {
        'hover:cursor-text': readOnly,
      },
      className
    )

    return (
      <div
        className={classNames(
          'form-control text-gray-700 dark:text-white',
          wrapperClasses,
        )}
      >
        {text && (
          <label
            className="label font-weight-600 dark:text-gray-400"
            htmlFor={id}
          >
            {text && (
              <span className={'label-text ' + labelClasses}>{text}</span>
            )}
          </label>
        )}

        <input
          {...nativeProps}
          ref={mergeRefs(inputRef, ref)}
          id={id}
          placeholder={placeholder || ' '}
          className={inputClasses}
          onChange={(e) => {
            if (onChange) onChange(e)
          }}
          readOnly={readOnly}
        />
      </div>
    )
  }
)

export default Input
