import IconProvider from '@/components/assets/IconProvider'
import classnames from 'classnames'
import React from 'react'

export interface BadgeProps extends React.AllHTMLAttributes<HTMLDivElement> {
  text?: React.ReactNode | JSX.Element | string
  className?: string
  textClasses?: string
  type?: BadgeType
  customPadding?: string
  isLoading?: boolean
  onClick?: () => void
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>((props, ref) => {
  const {
    text,
    type = 'default',
    className: additionalClasses = '',
    textClasses,
    customPadding = 'py-0.5 px-1',
    isLoading,
    onClick,
    ...nativeProps
  } = props
  const classes = classnames(
    'font-sans badge badge-ghost rounded text-xs gap-1 whitespace-nowrap',
    customPadding,
    {
      'bg-indigo-100 text-indigo-600 dark:bg-indigo-700 dark:text-indigo-300':
        type === 'default',
      'bg-blue-150 text-blue-800 dark:bg-blue-700 dark:text-blue-300':
        type === 'primary',
      'bg-rose-100 text-rose-800 dark:bg-rose-700 dark:text-rose-300':
        type === 'danger',
      'bg-emerald-100 text-emerald-800 dark:bg-emerald-700 dark:text-emerald-300':
        type === 'success',
      'bg-yellow-100 text-yellow-800 dark:bg-yellow-700 dark:text-yellow-300':
        type === 'warning',
      'bg-gray-150 text-gray-800 dark:bg-gray-700 dark:text-gray-300':
        type === 'gray',
      'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-300':
        type === 'light-gray',
      'bg-white text-gray-600 dark:bg-gray-700 dark:text-gray-300':
        type === 'white',
      [additionalClasses]: additionalClasses,
    }
  )
  const iconProviderClasses = classnames({
    'text-rose-400': type === 'danger',
    'text-emerald-400': type === 'success',
  })

  return (
    <div {...nativeProps} className={classes} onClick={onClick} ref={ref}>
      {isLoading && <IconProvider icon="spinner" className="fa-spin p-1" />}
      {text && <span className={textClasses}>{text}</span>}
    </div>
  )
})

export default Badge
