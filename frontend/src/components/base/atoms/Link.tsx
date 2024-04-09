import React from 'react'
import classnames from 'classnames'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import type { FontAwesomeIconProps } from '@fortawesome/react-fontawesome'

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  icon?: FontAwesomeIconProps['icon']
  text?: React.ReactNode | JSX.Element | string
  style?: object
  rounded?: boolean
  iconClasses?: string
}

const Link: React.FC<LinkProps> = (props) => {
  const { text, icon, rounded, iconClasses, className, ...nativeProps } = props
  const classes = classnames(
    'btn gap-2 font-inter normal-case flex-nowrap whitespace-nowrap',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:text-white/100 dark:bg-blue-purple',
    {
      'rounded-md': rounded,
      [`${className}`]: className,
    }
  )
  return (
    <a {...nativeProps} className={classes}>
      {icon && <FontAwesomeIcon icon={icon} className={`${iconClasses}`} />}
      {text}
    </a>
  )
}

export default Link
