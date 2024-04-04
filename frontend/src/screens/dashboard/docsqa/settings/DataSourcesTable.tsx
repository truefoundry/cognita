import Button from '@/components/base/atoms/Button'
import { DarkTooltip } from '@/components/base/atoms/Tooltip'
import notify from '@/components/base/molecules/Notify'
import Table from '@/components/base/molecules/Table'
import {
  useGetDataIngestionRunsQuery,
  useIngestDataSourceMutation,
  useUnassociateDataSourceMutation,
} from '@/stores/qafoundry'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import React, { useEffect } from 'react'

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
  setSkipPolling,
}: {
  collectionName: string
  fqn: string
  setSkipPolling: (value: boolean) => void
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
    setSkipPolling(false)
    notify(
      'success',
      'Data indexing has started!',
      <div>
        Please visit <b>Job Runs</b> tab of your application to check the
        status.
      </div>
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

const TERMINAL_STATUSES = [
  'COMPLETED',
  'ERROR',
  'DATA_CLEANUP_FAILED',
  'DATA_INGESTION_FAILED',
  'FETCHING_EXISTING_VECTORS_FAILED',
]

const DataSourceIngestionStatus = ({
  collectionName,
  dataSourceFqn,
  skipPolling,
  lastIngestionStatus,
  setSkipPolling,
  setLastIngestionStatus,
}: {
  collectionName: string
  dataSourceFqn: string
  skipPolling: boolean
  lastIngestionStatus: string
  setSkipPolling: (value: boolean) => void
  setLastIngestionStatus: (value: string) => void
}) => {
  const {
    data: ingestionStatuses,
    isLoading,
    refetch,
  } = useGetDataIngestionRunsQuery(
    {
      collection_name: collectionName,
      data_source_fqn: dataSourceFqn,
    },
    { pollingInterval: 5000, skip: skipPolling, refetchOnReconnect: true }
  )


  useEffect(() => {
    if (ingestionStatuses?.length) {
      const lastRun = ingestionStatuses[0]
      if (TERMINAL_STATUSES.includes(lastRun.status) && !isLoading) {
        setSkipPolling(true)
      }
      const processedStatus = lastRun.status.replaceAll('_', ' ')
      if (processedStatus !== lastIngestionStatus) {
        setLastIngestionStatus(processedStatus)
      }
    }
  }, [ingestionStatuses])

  return (
    <div className={'text-sm'}>
      {isLoading ? 'Loading...' : lastIngestionStatus || 'NOT INGESTED'}
    </div>
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

const DataSourcesTable = ({
  collectionName,
  rows,
  openRunsHistoryDrawer,
}: DataSourcesTableProps) => {
  const [lastIngestionStatus, setLastIngestionStatus] = React.useState<{
    [key: string]: string
  }>({})
  const [skipPolling, setSkipPolling] = React.useState<{
    [key: string]: boolean
  }>({})

  const columns: GridColDef[] = [
    {
      field: 'type',
      headerName: 'Type',
      width: 130,
      renderCell: (params: GridRenderCellParams) => (
        <div className="capitalize">{params?.value}</div>
      ),
    },
    { field: 'fqn', headerName: 'FQN', flex: 1 },
    {
      field: 'status',
      headerName: 'Status',
      flex: 1,
      renderCell: (params: GridRenderCellParams) => {
        const key = collectionName + ':' + params?.row?.fqn
        return (
          <DataSourceIngestionStatus
            collectionName={collectionName}
            dataSourceFqn={params?.row?.fqn}
            skipPolling={skipPolling[key]}
            lastIngestionStatus={lastIngestionStatus[key]}
            setSkipPolling={(value) =>
              setSkipPolling({ ...skipPolling, [key]: value })
            }
            setLastIngestionStatus={(value) =>
              setLastIngestionStatus({
                ...lastIngestionStatus,
                [key]: value,
              })
            }
          />
        )
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      renderCell: (params: GridRenderCellParams) => {
        const key = collectionName + ':' + params?.row?.fqn
        return (
          <div className="flex gap-1">
            <DataSourceSyncButton
              collectionName={collectionName}
              fqn={params?.row?.fqn}
              setSkipPolling={(value) =>
                setSkipPolling({ ...skipPolling, [key]: value })
              }
            />
          </div>
        )
      },
    },
  ]

  return (
    <div className="bg-white h-full">
      <Table rows={rows} columns={columns} />
    </div>
  )
}

export default DataSourcesTable
