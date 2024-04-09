import Button from '@/components/base/atoms/Button'
import Table from '@/components/base/molecules/Table'
import { useGetDataSourcesQuery } from '@/stores/qafoundry'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import React, { useMemo } from 'react'
import NewDataSource from '../NewDataSource'
import CopyField from '@/components/base/atoms/CopyField'

const DataHub = () => {
  const [isNewDataSourceDrawerOpen, setIsNewDataSourceDrawerOpen] =
    React.useState(false)
  const { data: dataSources, isLoading, refetch } = useGetDataSourcesQuery()

  const columns: GridColDef[] = [
    {
      field: 'type',
      headerName: 'Type',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <div className="capitalize">{params?.value}</div>
      ),
    },
    {
      field: 'source',
      headerName: 'Source',
      flex: 1,
      renderCell: (params: GridRenderCellParams) => (
        <div className="flex gap-2 items-center w-full truncate">
          <div className="truncate">{params?.value}</div>
          <CopyField rawValue={params?.value} />
        </div>
      ),
    },
    {
      field: 'fqn',
      headerName: 'FQN',
      flex: 1,
      renderCell: (params: GridRenderCellParams) => (
        <div className="flex gap-2 items-center w-full truncate">
          <div className="truncate">{params?.value}</div>
          <CopyField rawValue={params?.value} />
        </div>
      ),
    },
  ]
  const rows = useMemo(
    () =>
      dataSources
        ? dataSources?.map((source) => ({
            id: source.fqn,
            type: source.type,
            source: source.uri,
            fqn: source.fqn,
          }))
        : [],
    [dataSources]
  )

  return (
    <>
      <div className="h-full">
        <div className="w-full flex justify-end items-center mb-4">
          <Button
            icon={'plus'}
            iconClasses="text-gray-400"
            text={'New Data Source'}
            className="btn-sm text-sm bg-black"
            onClick={() => setIsNewDataSourceDrawerOpen(true)}
          />
        </div>
        <div className="h-[calc(100%-50px)] overflow-auto bg-white">
          <Table rows={rows} columns={columns} isLoading={isLoading} />
        </div>
      </div>
      {isNewDataSourceDrawerOpen && (
        <NewDataSource
          open={isNewDataSourceDrawerOpen}
          onClose={() => {
            refetch()
            setIsNewDataSourceDrawerOpen(false)
          }}
        />
      )}
    </>
  )
}

export default DataHub
