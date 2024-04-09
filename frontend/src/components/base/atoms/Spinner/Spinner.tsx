import React from 'react'
import classnames from 'classnames'
import SpinnerDots from './components/SpinnerDots'

export interface SpinnerProps {
  className?: string
  small?: boolean
  big?: boolean
  medium?: boolean
  center?: boolean
  type?: 'normal'
}
const Spinner: React.FC<SpinnerProps> = ({
  className,
  small,
  big,
  medium,
  center,
  type = 'normal',
}) => {
  const isDefault = () => type === 'normal'

  const classes = classnames({
    'animate-spin ease-linear rounded-full overflow-hidden': true,
    'border-gray-200 btop': isDefault(),
    'border-4 border-t-4 h-8 w-8': isDefault() && !small && !medium && !big,
    'h-4 w-4': small,
    'border-2 border-t-2': isDefault() && small,
    'h-12 w-12': medium,
    'border-4 border-t-4': isDefault() && medium,
    'h-20 w-20': big,
    'border-8 border-t-8 ': isDefault() && big,
    'm-auto': center,
    [`${className}`]: className,
  })

  switch (type) {
    default:
      return (
        <div className={classes} role="status">
          <span className="invisible">Loading...</span>
        </div>
      )
  }
}

export default Spinner
