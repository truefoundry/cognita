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
import { notifyError } from '@/utils/error'
import { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import React, { useEffect, useMemo, useState } from 'react'

const DeleteApplication = ({ appName }: { appName: string }) => {
  const [deleteApplication, { isLoading }] = useDeleteApplicationMutation()

  const handleSubmit = async () => {
    try {
      await deleteApplication({ app_name: appName }).unwrap()
      notify('success', 'RAG Application is successfully deleted!')
    } catch (e) {
      notifyError(
        'The RAG Application deletion failed. Please try again later.',
        e,
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
  const [showCurl, setShowCurl] = useState(false)
  const [curlCommand, setCurlCommand] = useState('')

  const { data: applicationData, isLoading: isApplicationDataLoading } =
    useGetApplicationDetailsByNameQuery(selectedApplication ?? '', {
      skip: !selectedApplication,
    })

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'Name',
      flex: 0.5,
      renderCell: (params: GridRenderCellParams) => <div>{params?.value}</div>,
    },
    {
      field: 'url',
      headerName: 'Application URL',
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
    [applicationNames],
  )

  useEffect(() => {
    if (applicationData) {
      const config = applicationData.config

      const modelConfiguration = JSON.stringify(
        config.model_configuration,
        null,
        2,
      )
      const retrieverConfig = JSON.stringify(config.retriever_config, null, 2)

      const curlCommand = `curl -X POST http://localhost:8000/retrievers/${config.query_controller}/answer \\
-H "Content-Type: application/json" \\
-d '{
  "collection_name": "${config.collection_name}",
  "query": "Explain in detail about this pdf",
  "model_configuration": ${modelConfiguration},
  "prompt_template": "You are an AI assistant specialising in information retrieval and analysis. Answer the following question based only on the given context:\\nContext: {context} \\nQuestion: {question}",
  "retriever_name": "${config.retriever_name}",
  "retriever_config": ${retrieverConfig}
}'`
      setCurlCommand(curlCommand)
    }
  }, [applicationData])

  const embedCode = `<embed src="${window.location.origin}/embed/${selectedApplication}" style="width: 400px; height: 500px">`

  return (
    <>
      <div className="h-[calc(100%-50px)] overflow-auto bg-white">
        <Table rows={rows} columns={columns} isLoading={isLoading} />
      </div>
      <Modal
        open={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div className="relative modal-box py-6 pb-12 overflow-hidden border-2 max-w-[40rem]">
          {isApplicationDataLoading ? (
            <Spinner center medium />
          ) : (
            <div className="max-h-[70vh] overflow-scroll">
              <div className="h-full overflow-scroll mb-2">
                <div className="mb-2 text-sm">Config:</div>
                <SimpleCodeEditor
                  language="json"
                  height={350}
                  value={JSON.stringify(applicationData?.config, null, 2)}
                  readOnly
                />
                {!!applicationData?.questions?.length && (
                  <>
                    <div className="mt-3 text-sm mb-1">Questions:</div>
                    <ul className="list-disc ml-4">
                      {applicationData?.questions?.map(
                        (question: string, index: number) => (
                          <li className="text-sm font-medium" key={index}>
                            {question}
                          </li>
                        ),
                      )}
                    </ul>
                  </>
                )}

                <button
                  onClick={() => setShowCurl(!showCurl)}
                  className="mb-2 mt-4 text-sm p-2 bg-indigo-500 text-white rounded"
                >
                  {showCurl ? 'Hide' : 'Show'} cURL Command
                </button>

                {showCurl && (
                  <div className="flex flex-col gap-2 mt-2 mb-4 relative">
                    <h1>cURL Request Example : </h1>
                    <pre className="group overflow-scroll rounded-md p-4 bg-slate-900 text-white">
                      <CopyField
                        rawValue={curlCommand}
                        className="hidden group-hover:block absolute top-11 right-3"
                      />
                      <code className="text-xs">{curlCommand}</code>
                    </pre>
                  </div>
                )}

                <div className="mt-2">
                  <div className="mb-1">
                    Use the below code to embed this application:
                  </div>
                  <div className="relative text-sm bg-gray-100 p-2 rounded font-medium italic group">
                    {embedCode}
                    <CopyField
                      rawValue={embedCode}
                      className="hidden group-hover:block absolute top-1 right-1"
                    />
                  </div>
                </div>
              </div>
              <div className="absolute bottom-2 right-6 flex justify-end">
                <Button
                  text="Close"
                  className="bg-white border-1 btn-sm mt-4"
                  onClick={() => setIsConfigModalOpen(false)}
                />
              </div>
            </div>
          )}
        </div>
      </Modal>
    </>
  )
}

export default Applications
