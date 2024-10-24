import Button from '@/components/base/atoms/Button'
import Table from '@/components/base/molecules/Table'
import {
  useDeleteDataSourceMutation,
  useGetDataSourcesQuery,
} from '@/stores/qafoundry'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import React, { useMemo } from 'react'
import NewDataSource from './NewDataSource'
import CopyField from '@/components/base/atoms/CopyField'
import { IS_LOCAL_DEVELOPMENT } from '@/stores/constants'
import notify from '@/components/base/molecules/Notify'
import { notifyError } from '@/utils/error'

const DeleteDataSource = ({ fqn }: { fqn: string }) => {
  const [deleteDataSource, { isLoading }] = useDeleteDataSourceMutation()

  const handleSubmit = async () => {
    try {
      await deleteDataSource({ data_source_fqn: fqn }).unwrap()
      notify('success', 'Data Source is successfully deleted!')
    } catch (e) {
      notifyError('Data source deletion failed. Please try again later', e)
    }
  }

  return (
    <Button
      outline
      icon="trash-can"
      iconClasses="text-xs text-red-400"
      className="border-red-200 shadow bg-base-100 btn-sm font-normal px-2.5 mr-1"
      loading={isLoading}
      onClick={handleSubmit}
    />
  )
}

const DataHub = () => {
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
    {
      field: 'actions',
      headerName: '',
      width: 80,
      renderCell: (params: GridRenderCellParams) => (
        <div className="w-full flex justify-center">
          <DeleteDataSource fqn={params.row.fqn as string} />
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
    [dataSources],
  )

  return (
    <>
      <div className="h-full">
        <div className="w-full flex justify-end items-center gap-4 mb-4">
          <NewDataSource
            onClose={() => {
              refetch()
            }}
          />
        </div>
        <div className="h-[calc(100%-50px)] overflow-auto bg-white">
          <Table rows={rows} columns={columns} isLoading={isLoading} />
        </div>
      </div>
    </>
  )
}

export default DataHub
