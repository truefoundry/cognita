import classnames from 'classnames'
import React from 'react'

import IconProvider from '@/components/assets/IconProvider'
import type { FontAwesomeIconProps } from '@fortawesome/react-fontawesome'
import Spinner from './Spinner'

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: FontAwesomeIconProps['icon']
  text?: React.ReactNode | JSX.Element | string
  style?: object
  rounded?: boolean
  outline?: boolean
  disabled?: boolean
  loading?: boolean
  showTextWithLoader?: boolean
  iconClasses?: string
  white?: boolean
  iconToRight?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (props, ref) => {
    const {
      text,
      icon,
      disabled = false,
      outline,
      rounded = true,
      iconClasses,
      className,
      loading = false,
      showTextWithLoader = false,
      white,
      iconToRight,
      ...nativeProps
    } = props
    const classes = classnames(
      'btn gap-2 font-lab normal-case flex-nowrap whitespace-nowrap outline-none',
      'disabled:cursor-not-allowed disabled:bg-[#F0F7FF] disabled:text-gray-500 dark:bg-blue-purple',
      {
        'cursor-not-allowed border-gray-300': loading || disabled,
        'btn-outline': outline,
        'rounded-md': rounded,
        'btn-xs btn-ghost border border-gray-200 hover:border-gray-500 shadow-sm':
          white,
        [`${className}`]: className,
      }
    )

    const iconClass = classnames({
      'text-[#A8C3E8]': loading || disabled,
      [`${iconClasses}`]: iconClasses,
    })
    return (
      <button
        {...nativeProps}
        className={classes}
        disabled={loading || disabled}
        ref={ref}
      >
        {icon && !loading && !iconToRight && (
          <IconProvider icon={icon} className={`${iconClass}`} />
        )}
        {loading && !showTextWithLoader ? <Spinner small /> : text}
        {loading && showTextWithLoader && <Spinner small />}
        {icon && !loading && iconToRight && (
          <IconProvider icon={icon} className={`${iconClass}`} />
        )}
      </button>
    )
  }
)

export default Button
