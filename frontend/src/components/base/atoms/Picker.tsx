import { MenuItem, Select, type SelectProps } from '@mui/material'
import React from 'react'

type PickerProps = {
  options: string[]
}

const Picker = React.forwardRef<typeof Select, PickerProps & SelectProps<string>>((props, ref) => {
  return (
    <Select
      ref={ref}
      {...props}
      placeholder="Select Model..."
      sx={{
        background: 'white',
        height: '2rem',
        width: '13.1875rem',
        border: '1px solid #CEE0F8 !important',
        outline: 'none !important',
        '& fieldset': {
          border: 'none !important',
        },
      }}
    >
      {props.options.map((option: string) => (
        <MenuItem value={option} key={option}>
          {option}
        </MenuItem>
      ))}
    </Select>
  );
})

export default Picker;
