import Button from '@/components/base/atoms/Button'
import CopyField from '@/components/base/atoms/CopyField'
import Modal from '@/components/base/atoms/Modal'
import Spinner from '@/components/base/atoms/Spinner'
import notify from '@/components/base/molecules/Notify'
import SimpleCodeEditor from '@/components/base/molecules/SimpleCodeEditor'
import Table from '@/components/base/molecules/Table'
import {
  useDeleteApplicationMutation,
  useGetApplicationDetailsByNameQuery,
  useGetApplicationsQuery,
} from '@/stores/qafoundry'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import React, { useMemo } from 'react'

const DeleteApplication = ({ appName }: { appName: string }) => {
  const [deleteApplication, { isLoading }] = useDeleteApplicationMutation()

  const handleSubmit = async () => {
    try {
      await deleteApplication({ app_name: appName }).unwrap()
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

const Applications = () => {
  const { data: applicationNames, isLoading } = useGetApplicationsQuery()
  const [selectedApplication, setSelectedApplication] = React.useState<
    string | null
  >(null)
  const [isConfigModalOpen, setIsConfigModalOpen] = React.useState(false)

  const { data: applicationData, isLoading: isApplicationDataLoading } =
    useGetApplicationDetailsByNameQuery(selectedApplication ?? '', {
      skip: !selectedApplication,
    })

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      flex: 1,
      renderCell: (params: GridRenderCellParams) => <div>{params?.value}</div>,
    },
    {
      field: 'url',
      headerName: 'Embedding URL',
      flex: 1,
      renderCell: (params: GridRenderCellParams) => (
        <div className="flex gap-2 items-center w-full truncate">
          <div className="truncate">{params?.value}</div>
          <CopyField rawValue={params?.value} />
        </div>
      ),
    },
    {
      field: 'config',
      headerName: 'Config',
      width: 200,
      renderCell: (params: GridRenderCellParams) => (
        <div className="flex gap-2 items-center w-full truncate">
          <div
            className="text-blue-700 cursor-pointer"
            onClick={() => {
              setIsConfigModalOpen(true)
              setSelectedApplication(params.row.name)
            }}
          >
            See Config
          </div>
        </div>
      ),
    },
    {
      field: 'actions',
      headerName: '',
      width: 80,
      renderCell: (params: GridRenderCellParams) => (
        <div className="w-full flex justify-center">
          <DeleteApplication appName={params.row.name} />
        </div>
      ),
    },
  ]
  const rows = useMemo(
    () =>
      applicationNames
        ? applicationNames?.map((name) => ({
            id: name,
            name,
            url: `${window.location.origin}/embed/${name}`,
          }))
        : [],
    [applicationNames]
  )
  return (
    <div className="h-[calc(100%-50px)] overflow-auto bg-white">
      <Modal
        open={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
      >
        <div className="modal-box">
          {isApplicationDataLoading ? (
            <Spinner center medium />
          ) : (
            <>
              <SimpleCodeEditor
                language="json"
                height={400}
                value={JSON.stringify(applicationData?.config, null, 2)}
                readOnly
              />
              <div className="flex justify-end">
                <Button
                  text="Close"
                  className="btn-sm mt-4"
                  onClick={() => setIsConfigModalOpen(false)}
                />
              </div>
            </>
          )}
        </div>
      </Modal>
      <Table rows={rows} columns={columns} isLoading={isLoading} />
    </div>
  )
}

export default Applications
