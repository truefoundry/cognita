import React, { useMemo } from 'react'
import axios from 'axios'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import Button from '@/components/base/atoms/Button'
import Table from '@/components/base/molecules/Table'
import {
  useDeleteDataSourceMutation,
  useGetDataSourcesQuery,
} from '@/stores/qafoundry'
import CopyField from '@/components/base/atoms/CopyField'
import notify from '@/components/base/molecules/Notify'
import { CARBON_API_KEY, IS_LOCAL_DEVELOPMENT } from '@/stores/constants'
import NewDataSource from '../NewDataSource'

const DeleteDataSource = ({ fqn }: { fqn: string }) => {
  const [deleteDataSource, { isLoading }] = useDeleteDataSourceMutation()

  const handleSubmit = async () => {
    try {
      await deleteDataSource({ data_source_fqn: fqn }).unwrap()
      notify('success', 'Data Source is successfully deleted!')
    } catch (e) {
      notify(
        'error',
        'Something went wrong!',
        e?.data?.detail ??
          'The data source deletion failed. Please try again later.'
      )
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
    ...(IS_LOCAL_DEVELOPMENT
      ? [
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
      : []),
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

  const tokenFetcher = async () => {
    const response = await axios.get(
      'https://api.carbon.ai/auth/v1/access_token',
      {
        headers: {
          'Content-Type': 'application/json',
          'customer-id': 'test_cognita',
          authorization: `Bearer ${CARBON_API_KEY}`,
        },
      }
    )
    return response.data
  }

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
