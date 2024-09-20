import { IconProp } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import React, { forwardRef } from 'react'
import classNames from 'classnames'
import paperPlaneIcon from '@/assets/img/paper-plane-top.svg'
import xTwitterIcon from '@/assets/img/logos/x_twitter.png'

export const EXT_ICONS_MAP: { readonly [key: string]: any } = {
  'paper-plane-top': paperPlaneIcon,
  'x-twitter': xTwitterIcon,
}

interface IconProps {
  icon: string | IconProp
  color?: string
  className?: string
  onClick?: (e: React.MouseEvent) => void
  size?: number
  forwardedRef?: React.Ref<HTMLElement>
}

const IconProvider = ({
  icon,
  color,
  size = 0.75,
  className,
  onClick,
}: IconProps, forwardedRef) => {
  return EXT_ICONS_MAP[icon as string] ? (
    <img
      ref={forwardedRef}
      src={EXT_ICONS_MAP[icon as string]}
      style={{ height: `${size}rem`, width: 'auto' }}
      className={classNames(className)}
    />
  ) : (
    <FontAwesomeIcon
      ref={forwardedRef}
      icon={icon as IconProp}
      style={{ color, fontSize: `${size}rem` }}
      className={classNames('text-xs', className)}
      onClick={onClick}
    />
  )
}

export default React.memo(
  forwardRef<HTMLElement, IconProps>(IconProvider)
)
