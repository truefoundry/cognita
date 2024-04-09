/* eslint-disable @typescript-eslint/no-explicit-any */
import plugin from 'tailwindcss/plugin'

export default plugin(function ({ addUtilities, matchUtilities, theme }) {
  const scrollbarTrackColorValue = (value: string) => ({
    '--scrollbar-track': value,
    '&::-webkit-scrollbar-track': {
      'background-color': value,
    },
  })

  const scrollbarTrackRoundedValue = (value: any) => ({
    '&::-webkit-scrollbar-track': {
      'border-radius': value,
    },
  })

  const scrollbarThumbColorValue = (value: string) => ({
    '--scrollbar-thumb': value,
    '&::-webkit-scrollbar-thumb': {
      'background-color': value,
    },
  })

  const scrollbarThumbRoundedValue = (value: any) => ({
    '&::-webkit-scrollbar-thumb': {
      'border-radius': value,
    },
  })

  addUtilities({
    '.scrollbar': {
      '--scrollbar-thumb': '#cdcdcd',
      '--scrollbar-track': '#f0f0f0',
      '--scrollbar-width': '17px',
      'scrollbar-color': 'var(--scrollbar-thumb) var(--scrollbar-track)',
      '&::-webkit-scrollbar': {
        width: 'var(--scrollbar-width)',
        height: 'var(--scrollbar-width)',
      },
    },
    '.scrollbar-thin': {
      '--scrollbar-width': '0.5rem',
      'scrollbar-width': 'thin',
    },
  })

  Object.entries(theme('colors')).forEach(([colorName, color]) => {
    switch (typeof color) {
      case 'object':
        matchUtilities(
          {
            [`scrollbar-track-${colorName}`]: (value: any) =>
              scrollbarTrackColorValue(value),
            [`scrollbar-thumb-${colorName}`]: (value: any) =>
              scrollbarThumbColorValue(value),
          },
          {
            values: color,
          }
        )
        break
      case 'function':
        addUtilities({
          [`.scrollbar-track-${colorName}`]: scrollbarTrackColorValue(
            color({})
          ),
          [`.scrollbar-thumb-${colorName}`]: scrollbarThumbColorValue(
            color({})
          ),
        })
        break
      case 'string':
        addUtilities({
          [`.scrollbar-track-${colorName}`]: scrollbarTrackColorValue(color),
          [`.scrollbar-thumb-${colorName}`]: scrollbarThumbColorValue(color),
        })
        break
    }
  })

  matchUtilities(
    {
      'scrollbar-track-rounded': (value: any) =>
        scrollbarTrackRoundedValue(value),
      'scrollbar-thumb-rounded': (value: any) =>
        scrollbarThumbRoundedValue(value),
    },
    {
      values: theme('borderRadius'),
    }
  )
})
