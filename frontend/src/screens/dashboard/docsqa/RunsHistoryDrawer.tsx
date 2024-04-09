import Badge from '@/components/base/atoms/Badge'
import CustomDrawer from '@/components/base/atoms/CustomDrawer'
import Table from '@/components/base/molecules/Table'
import { useGetDataIngestionRunsQuery } from '@/stores/qafoundry'
import classNames from '@/utils/classNames'
import { GridColDef } from '@mui/x-data-grid'
import React, { useMemo } from 'react'

interface RunHistoryDrawerProps {
  open: boolean
  collectionName: string
  selectedDataSource: string
  onClose: () => void
}

const RunsHistoryDrawer = ({
  open,
  collectionName,
  selectedDataSource,
  onClose
}: RunHistoryDrawerProps) => {
  const { data: runs, isLoading } = useGetDataIngestionRunsQuery({
    collection_name: collectionName,
    data_source_fqn: selectedDataSource,
  })

  const rows = useMemo(() => {
    if (!runs) return []

    return runs?.map((run) => ({
        id: run.name,
        name: run.name,
        status: run.status,
    }))
  }, [runs])

  const columns: GridColDef[] = useMemo(() => {
    return [
      {
        field: 'name',
        headerName: 'Run Name',
        flex: 1,
      },
      {
        field: 'status',
        headerName: 'Status',
        flex: 1,
      },
    ]
  }
  , [])

  return (
    <CustomDrawer open={open} onClose={onClose} width="w-[46vw]" className='min-w-[300px]' bodyClassName="p-0">
      <>
        <h3
          className={classNames(
            'flex flex-wrap items-center font-medium text-lg bg-white border-b-1 py-2 px-4 leading-8'
          )}
        >
          <span>Runs history for</span>
          <Badge
            text={selectedDataSource}
            className="text-sm bg-gray-150 border font-semibold border-gray-200 mx-1"
            style={{ color: '#010202' }}
            customPadding="py-[0.7rem]"
          />
        </h3>
        <div className='m-4 bg-white h-[calc(100%-80px)]'>
          <Table
            rows={rows}
            columns={columns}
            isLoading={isLoading}
          />
        </div>
      </>
    </CustomDrawer>
  )
}

export default RunsHistoryDrawer
