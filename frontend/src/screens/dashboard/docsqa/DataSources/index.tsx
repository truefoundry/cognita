import Button from '@/components/base/atoms/Button'
import Table from '@/components/base/molecules/Table'
import {
  useDeleteDataSourceMutation,
  useGetDataSourcesQuery,
} from '@/stores/qafoundry'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import React, { useMemo } from 'react'
import NewDataSource from '../NewDataSource'
import CopyField from '@/components/base/atoms/CopyField'
import { CARBON_API_KEY, IS_LOCAL_DEVELOPMENT } from '@/stores/constants'
import notify from '@/components/base/molecules/Notify'
import { CarbonConnect } from 'carbon-connect'
import axios from 'axios'

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
        <CarbonConnect
          orgName="Cognita"
          brandIcon="path/to/your/brand/icon"
          // embeddingModel={EmbeddingGenerators.OPENAI_ADA_LARGE_1024}
          tokenFetcher={tokenFetcher}
          tags={{
            tag1: 'tag1_value',
            tag2: 'tag2_value',
            tag3: 'tag3_value',
          }}
          maxFileSize={10000000}
          enabledIntegrations={[
            {
              id: 'LOCAL_FILES',
              chunkSize: 100,
              overlapSize: 10,
              maxFileSize: 20000000,
              allowMultipleFiles: true,
              maxFilesCount: 5,
              allowedFileTypes: [
                {
                  extension: 'csv',
                  chunkSize: 1200,
                  overlapSize: 120,
                  // embeddingModel: 'OPENAI',
                },
                {
                  extension: 'txt',
                  chunkSize: 1599,
                  overlapSize: 210,
                  // embeddingModel: 'AZURE_OPENAI',
                },
                {
                  extension: 'pdf',
                },
              ],
            },
            {
              id: 'NOTION',
              chunkSize: 1500,
              overlapSize: 20,
              embeddingModel: 'OPENAI',
            },
            {
              id: 'WEB_SCRAPER',
              chunkSize: 1500,
              overlapSize: 20,
            },
            {
              id: 'GOOGLE_DRIVE',
              chunkSize: 1000,
              overlapSize: 20,
            },
          ]}
          onSuccess={(data) => console.log('Data on Success: ', data)}
          onError={(error) => console.log('Data on Error: ', error)}
          primaryBackgroundColor="#F2F2F2"
          primaryTextColor="#555555"
          secondaryBackgroundColor="#f2f2f2"
          secondaryTextColor="#000000"
          allowMultipleFiles={true}
          open={true}
          chunkSize={1500}
          overlapSize={20}
          // entryPoint="LOCAL_FILES"
        >
          hey there
        </CarbonConnect>
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
