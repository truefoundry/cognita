import React from 'react'

import { MenuItem, Select } from '@mui/material'

interface ConfigProps {
  title: string
  placeholder: string
  initialValue: string
  data: any[] | undefined
  handleOnChange: (e: any) => void
}

const Option = (props: ConfigProps) => {
  const { title, placeholder, initialValue, data, handleOnChange } = props

  return (
    <div className={`flex justify-between items-center`}>
      <div className="text-sm">{title}:</div>
      <Select
        value={initialValue}
        onChange={(e) => handleOnChange(e)}
        placeholder={placeholder + '...'}
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
        {data?.map((item: any) =>
          typeof item === 'object' ? (
            <MenuItem value={item.name | item.key} key={item.name | item.key}>
              {item.name | item.summary}
            </MenuItem>
          ) : (
            <MenuItem value={item} key={item}>
              {item}
            </MenuItem>
          ),
        )}
      </Select>
    </div>
  )
}

export default Option
