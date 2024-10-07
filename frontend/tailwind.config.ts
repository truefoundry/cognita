import typography from '@tailwindcss/typography'
import forms from '@tailwindcss/forms'
import lineClamp from '@tailwindcss/line-clamp'
import daisyui from 'daisyui'
import plugin from 'tailwindcss/plugin'
import daisyuiThemes from 'daisyui/src/theming/themes'
// @ts-ignore
import scrollbar from './src/utils/tailwindScrollbar'

const config = {
  content: ['./index.html', './src/**/*.{vue,js,jsx,tsx}'],
  darkMode: 'class', // or 'media' or 'class'
  theme: {
    boxShadow: {
      sm: '0 1px 2px 0 rgba(0, 3, 15, 0.05)',
      DEFAULT:
        '0 1px 3px 0 rgba(0, 3, 15, 0.1), 0 1px 2px 0 rgba(0,3,15, 0.06)',
      md: '0 4px 6px -1px rgba(0, 3, 15, 0.1), 0 2px 4px -1px rgba(0,3,15, 0.06)',
      lg: '0 10px 15px -3px rgba(0, 3, 15, 0.1), 0 4px 6px -2px rgba(0,3,15, 0.05)',
      xl: '0 20px 25px -5px rgba(0, 3, 15, 0.1), 0 10px 10px -5px rgba(0,3,15, 0.04)',
      '2xl': '0 25px 50px -12px rgba(0, 3, 15, 0.25)',
      '3xl': '0 35px 60px -15px rgba(0, 3, 15, 0.3)',
      inner: 'inset 0 2px 4px 0 rgba(0, 3, 15, 0.06)',
      none: 'none',
    },
    extend: {
      fontSize: {
        'base-lg': '1.065rem',
        'sm-base': '0.935rem',
        '2xs': '0.563rem',
        '3xs': '0.2rem',
      },
      screens: {
        '2xl': '1536px',
        '3xl': '1936px',
        '4xl': '2436px',
        '5xl': '3236px',
      },
      borderWidth: {
        DEFAULT: '0.0625rem',
        '1': '0.0625rem',
      },
      colors: {
        gray: {
          25: '#F5FAFF',
          50: '#fafcff',
          100: '#F0F7FF',
          150: '#E8F2FE',
          200: '#E0ECFD',
          225: '#CAD4E3',
          250: '#CEE0F8',
          300: '#A8C3E8',
          350: '#95B2DD',
          400: '#82A0CE',
          450: '#6F8EBD',
          500: '#5E7BAA',
          550: '#4D6896',
          600: '#3E5680',
          650: '#31456A',
          700: '#263755',
          750: '#1C2A42',
          800: '#0E1623',
          850: '#090F17',
          900: '#05090E',
          950: '#030407',
          1000: '#010202',
          disabled: '#f2f2f2',
        },
        yellow: {
          100: '#FEF3C7',
          500: '#F59E0B',
        },
        skyblue: '#F5FAFF',
        blue: {
          primary: '#481DF1',
          secondary: '#93C5FD',
          purple: '#5501E1',
          'purple-2': '#0047ff',
          'purple-3': '#2900CE',
          500: '#BBD2F1',
        },
        green: {
          600: '#059669',
        },
      },
      dropShadow: {
        xl: [
          'px 2px 6px rgba(0, 52, 102, 0.06)',
          '0px 8px 20px rgba(0, 52 ,102, 0.1)',
        ],
      },
      backgroundImage: {
        main: 'url(@/assets/img/main-background.svg)',
      },
      backgroundColor: {
        app: '#fafcff',
        'ui-schema': 'rgba(240, 247, 255, 0.3)',
      },
      zIndex: {
        '-1': '-1',
      },
      flexGrow: {
        5: '5',
      },
      minHeight: {
        100: '100px',
        150: '150px',
        200: '200px',
      },
      height: {
        'screen-50': '50vh',
        'screen-60': '60vh',
        'screen-70': '70vh',
        'screen-75': '75vh',
      },
      maxHeight: {
        'screen-menu': 'calc(100vh - 3.5rem)',
        modal: 'calc(100vh - 10rem)',
      },
      transitionProperty: {
        position: 'right, left, top, bottom, margin, padding',
        textColor: 'color',
      },
      keyframes: {
        fadeOut: {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
          dotAnimation: {
          '0%, 80%, 100%': { transform: 'scale(0)' },
          '40%': { transform: 'scale(1)' },
        },

      },
      animation: {
        fadeOut: 'fadeOut 250ms ease-in-out',
        fadeIn: 'fadeIn 250ms ease-in-out',
        'dot-1': 'dotAnimation 1.4s infinite ease-in-out both',
        'dot-2': 'dotAnimation 1.4s infinite ease-in-out both -0.16s',
        'dot-3': 'dotAnimation 1.4s infinite ease-in-out both -0.32s',
      },
    },
    fontFamily: {
      sans: [
        'Work Sans',
        'system-ui',
        '-apple-system',
        'BlinkMacSystemFont',
        'Segoe UI',
        'Roboto',
        'Helvetica Neue',
        'Arial',
        'Noto Sans',
        'sans-serif',
        'Apple Color Emoji',
        'Segoe UI Emoji',
        'Segoe UI Symbol',
        'Noto Color Emoji',
      ],
      mono: [
        'SF Mono',
        'SFMono-Regular',
        'ui-monospace',
        'DejaVu Sans Mono',
        'Menlo',
        'Consolas',
        'monospace',
      ],
      inter: ['Inter', 'system-ui'],
    },
  },
  plugins: [
    plugin(function ({ addUtilities }) {
      addUtilities({
        '.scrollbar-hide': {
          /* IE and Edge */
          '-ms-overflow-style': 'none',

          /* Firefox */
          'scrollbar-width': 'none',

          /* Safari and Chrome */
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        },
      })
    }),
    typography,
    forms,
    lineClamp,
    scrollbar,
    daisyui,
  ],
  daisyui: {
    themes: [
      {
        foundry: {
          ...daisyuiThemes['[data-theme=light]'],
          primary: '#5429FF',
          neutral: '#000000'
        },
      },
    ],
  },
}

export default config