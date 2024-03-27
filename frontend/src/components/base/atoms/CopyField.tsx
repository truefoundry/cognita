import classNames from 'classnames'
import React, { useState } from 'react'
import notify from '../molecules/Notify'
import Button from './Button'
import { DarkTooltip } from './Tooltip'

interface CopyFieldProps {
  children?: string | JSX.Element
  errorMessage?: string
  rawValue?: string
  className?: string
  btnClass?: string
  btnTextClass?: string
  iconClass?: string
  initialText?: string
  bgClass?: string
  tooltipTitle?: string | JSX.Element
}

const CopyField: React.FC<CopyFieldProps> = ({
  errorMessage = 'Could not copy...',
  children,
  rawValue,
  className = '',
  btnClass = '',
  btnTextClass = '',
  iconClass = '',
  initialText,
  tooltipTitle = '',
  bgClass = 'bg-base-100',
}) => {
  const [hasCopied, setHasCopied] = useState(false)

  const containerClasses = classNames('flex gap-1 items-center', {
    [className]: className,
  })

  const buttonClasses = classNames('font-normal outline-none mr-1', {
    'text-sm': !btnClass,
    'text-gray-400 hover:text-white': !btnTextClass,
    'w-6 h-6': !initialText,
    [btnClass]: btnClass,
    [bgClass]: bgClass,
  })

  async function handleCopy(e: any) {
    e.stopPropagation()
    try {
      let val = rawValue
      if (navigator.clipboard) {
        const text = (
          !val && typeof children === 'string' ? children : val
        ) as string

        await navigator.clipboard.writeText(text)

        setHasCopied(true)
        setTimeout(() => setHasCopied(false), 3000)
      }
    } catch {
      notify('error', 'Unexpected error', errorMessage)
    }
  }

  const renderCopyButton = (
    <DarkTooltip title={tooltipTitle}>
      <Button
        type="button"
        icon={hasCopied ? 'check' : 'clone'}
        iconClasses={iconClass}
        className={buttonClasses}
        onClick={handleCopy}
        white
        outline
        text={initialText}
      />
    </DarkTooltip>
  )

  return (
    <div className={containerClasses}>
      {renderCopyButton}
      {children}
    </div>
  )
}

export default CopyField
