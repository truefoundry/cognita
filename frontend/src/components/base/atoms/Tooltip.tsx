import * as React from 'react'
import { styled } from '@mui/material/styles'
import Tooltip, { TooltipProps, tooltipClasses } from '@mui/material/Tooltip'
import classNames from 'classnames'

export type Sizes = 'large' | 'variable' | 'medium' | 'fit'

export type CustomTooltipProps = TooltipProps & {
  size?: Sizes
  border?: boolean
}

const getSize = (size?: Sizes) => {
  let height: string | number = 380
  let width: string | number = 250
  let font = 12
  switch (size) {
    case 'large':
      width = 420
      height = 400
      font = 14
      break
    case 'medium':
      width = 360
      height = 300
      font = 14
      break
    case 'variable':
      width = 'none'
      height = 'none'
    case 'fit':
      width = 'fit-content'
      height = 'none'
  }
  return { height, width, font }
}

export const LightTooltip = React.memo(
  styled(({ className, classes, border, ...props }: CustomTooltipProps) => (
    <Tooltip
      disableFocusListener
      {...props}
      classes={{
        popper: className,
        ...classes,
        tooltip: classNames(classes?.tooltip, 'custom-scrollbar'),
      }}
    />
  ))(({ size, theme, border }) => {
    const { height, width, font } = getSize(size)
    return {
      [`& .${tooltipClasses.tooltip}`]: {
        backgroundColor: '#ffffff',
        color: theme.palette.grey[900],
        fontWeight: 500,
        fontSize: font,
        maxHeight: height,
        minWidth: width,
        width: 'auto',
        boxShadow:
          '0px 2px 6px rgba(0, 52, 102, 0.06), 0px 8px 20px rgba(0, 52, 102, 0.1)',
        borderRadius: '0.375rem',
        overflow: 'auto',
        padding: '0.375rem 0.5rem',
        border: border ? '0.0625rem solid #E0ECFD' : '0px solid',
      },
    }
  })
)

export const DarkTooltip = React.memo(
  styled(({ className, classes, ...props }: CustomTooltipProps) => (
    <Tooltip
      disableFocusListener
      {...props}
      classes={{
        popper: className,
        ...classes,
        tooltip: classNames(classes?.tooltip, 'custom-scrollbar'),
      }}
    />
  ))(({ size, theme }) => {
    const { height, width, font } = getSize(size)
    return {
      [`& .${tooltipClasses.arrow}`]: {
        color: theme.palette.common.black,
      },
      [`& .${tooltipClasses.tooltip}`]: {
        backgroundColor: theme.palette.common.black,
        color: theme.palette.grey[200],
        fontWeight: 500,
        fontSize: font,
        width: 'auto',
        maxWidth: width,
        maxHeight: height,
        boxShadow:
          '0px 2px 6px rgba(0, 52, 102, 0.06), 0px 8px 20px rgba(0, 52, 102, 0.1)',
        borderRadius: '0.375rem',
        overflow: 'auto',
        padding: '0.375rem 0.5rem',
      },
    }
  })
)
