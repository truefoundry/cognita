import { DataGrid, GridColDef } from '@mui/x-data-grid'
import React from 'react'

const Table = ({
  rows,
  columns,
  isLoading,
  Wrapper = React.Fragment
}: {
  rows: any[],
  columns: GridColDef[],
  isLoading?: boolean,
  Wrapper?: React.FC
}) => {

  return (
    <Wrapper>
      <DataGrid
        rows={rows}
        columns={columns}
        loading={isLoading}
        hideFooterPagination
        hideFooter
        autoHeight={false}
        disableColumnMenu
        rowHeight={52}
        classes={{
          row: 'border-b group',
          'row--lastVisible': 'border-b-0',
          virtualScroller: 'table-scrollbar',
        }}
        sx={{
          fontFamily:
            '"Work Sans", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
          fontWeight: 500,
          color: '#010202',
          letterSpacing: 0,
          border: '1px solid #E0ECFD',
          '& .MuiDataGrid-window': { maxHeight: 'none' },
          '& .MuiDataGrid-withBorder': {
            borderRight: '0px',
          },
          '& .MuiDataGrid-row:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.025)',
          },
          '& .MuiDataGrid-columnHeader': {
            cursor: 'grab',
          },
          '& .MuiDataGrid-columnHeadersInner.MuiDataGrid-columnHeaderDropZone .MuiDataGrid-columnHeaderDraggableContainer':
            {
              cursor: 'grab',
            },
          '& .header__theme--metrics': {
            backgroundColor: 'rgba(254, 243, 199, 1)',
          },
          '& .header__theme--params': {
            backgroundColor: 'rgba(221, 214, 254, 1)',
          },
          '& .header__theme--tags': {
            backgroundColor: 'rgba(186, 230, 253, 1)',
            minHeight: '1.75rem',
          },
          '& .header__theme--feature': {
            backgroundColor: 'rgba(221, 214, 254, 1)',
          },
          '& .header__theme--predictions': {
            backgroundColor: 'rgba(186, 230, 253, 1)',
          },
          '& .MuiDataGrid-columnHeaders': {
            borderBottomColor: '#E0ECFD',
            minHeight: '40px !important',
            height: '40px',
          },
          '& .MuiDataGrid-cell': {
            borderBottomColor: 'transparent',
          },
        }}
      />
    </Wrapper>
  )
}

export default Table
