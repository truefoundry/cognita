import Button from '@/components/base/atoms/Button'
import { DarkTooltip } from '@/components/base/atoms/Tooltip'
import notify from '@/components/base/molecules/Notify'
import Table from '@/components/base/molecules/Table'
import {
  useIngestDataSourceMutation,
  useUnassociateDataSourceMutation,
} from '@/stores/qafoundry'
import {
  GridColDef,
  GridRenderCellParams
} from '@mui/x-data-grid'
import React from 'react'

const DataSourceDeleteButton = ({
  collectionName,
  fqn,
}: {
  collectionName: string
  fqn: string
}) => {
  const [unassociateDataSource, { isLoading }] =
    useUnassociateDataSourceMutation()

  const handleSubmit = async () => {
    await unassociateDataSource({
      collection_name: collectionName,
      data_source_fqn: fqn,
    })
    notify(
      'success',
      'Data Source is successfully detached from the collection!',
      'Updated collection will be available to use after 3-5 minutes.'
    )
  }

  return (
    <DarkTooltip title="Unlink Data Source">
      <Button
        outline
        icon="link-slash"
        iconClasses="text-xs text-red-400"
        className="border-red-200 shadow bg-base-100 btn-sm font-normal px-2.5 mr-1"
        loading={isLoading}
        onClick={handleSubmit}
      />
    </DarkTooltip>
  )
}

const DataSourceSyncButton = ({
  collectionName,
  fqn,
}: {
  collectionName: string
  fqn: string
}) => {
  const [ingestDataSource, { isLoading }] = useIngestDataSourceMutation()

  const handleSubmit = async () => {
    await ingestDataSource({
      collection_name: collectionName,
      data_source_fqn: fqn,
      data_ingestion_mode: 'INCREMENTAL',
      raise_error_on_failure: true,
      run_as_job: true,
    })
    notify(
      'success',
      'Data Source has started to synchronize!',
      'Updated collection will be available to use after 3-5 minutes.'
    )
  }

  return (
    <DarkTooltip title="Sync">
      <Button
        outline
        icon="sync"
        iconClasses="text-xs text-blue-400"
        className="border-blue-200 shadow bg-base-100 btn-sm font-normal px-2.5 mr-1"
        loading={isLoading}
        onClick={handleSubmit}
      />
    </DarkTooltip>
  )
}

interface DataSourcesTableProps {
  collectionName: string
  rows: {
    id: string
    type: string
    source: string
    fqn: string
  }[]
  openRunsHistoryDrawer: (fqn: string) => void
}

const DataSourcesTable = ({ collectionName, rows, openRunsHistoryDrawer }: DataSourcesTableProps) => {
  const columns: GridColDef[] = [
    {
      field: 'type',
      headerName: 'Type',
      width: 130,
      renderCell: (params: GridRenderCellParams) => (
        <div className="capitalize">{params?.value}</div>
      ),
    },
    { field: 'source', headerName: 'Source', flex: 1 },
    { field: 'fqn', headerName: 'FQN', flex: 1 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <div className="flex gap-1">
          <DataSourceDeleteButton
            collectionName={collectionName}
            fqn={params?.row?.fqn}
          />
          <DataSourceSyncButton
            collectionName={collectionName}
            fqn={params?.row?.fqn}
          />
          <Button
            outline
            text="View Runs"
            className="border-gray-200 shadow bg-base-100 btn-sm font-normal px-2.5"
            onClick={() => openRunsHistoryDrawer(params?.row?.fqn as string)}
          />
        </div>
      ),
    },
  ]

  return (
    <div className='bg-white h-full'>
      <Table
        rows={rows}
        columns={columns}
      />
    </div>
  )
}

export default DataSourcesTable
