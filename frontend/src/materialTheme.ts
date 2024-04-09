import { createTheme } from '@mui/material/styles'

import tailwindConfigModule from '../tailwind.config.js'

export default createTheme({
  typography: {
    fontFamily: tailwindConfigModule.theme.fontFamily.sans.join(', '),
  },
  components: {
    MuiPopover: {
      styleOverrides: {
        paper: {
          borderRadius: '0.5rem',
        },
      },
    },
  },
})
