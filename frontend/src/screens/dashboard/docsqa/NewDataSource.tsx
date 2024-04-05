import { uploadArtifactFileWithSignedURI } from '@/api/mlfoundry'
import IconProvider from '@/components/assets/IconProvider'
import Badge from '@/components/base/atoms/Badge'
import Button from '@/components/base/atoms/Button'
import CustomDrawer from '@/components/base/atoms/CustomDrawer'
import Spinner from '@/components/base/atoms/Spinner'
import { DarkTooltip } from '@/components/base/atoms/Tooltip'
import notify from '@/components/base/molecules/Notify'
import { DOCS_QA_MAX_UPLOAD_SIZE_MB } from '@/stores/constants'
import {
  useAddDataSourceMutation,
  useGetDataLoadersQuery,
  useUploadDataToDataDirectoryMutation,
} from '@/stores/qafoundry'
import { getFilePath, getUniqueFiles } from '@/utils/artifacts'
import classNames from '@/utils/classNames'
import { MenuItem, Select } from '@mui/material'
import React, { useEffect, useState } from 'react'

const parseFileSize = (size: number) => {
  const units = ['B', 'Ki', 'Mi', 'Gi']
  let i = 0
  while (size >= 1024) {
    size /= 1024
    ++i
  }
  const hasDecimal = size % 1 !== 0
  return `${hasDecimal ? size.toFixed(2) : size} ${units[i]}`
}

type FileObject = {
  id: string
  file: File
}

interface NewDataSourceProps {
  open: boolean
  onClose: () => void
}

const NewDataSource = ({ open, onClose }: NewDataSourceProps) => {
  const [isSaving, setIsSaving] = useState(false)
  const [selectedDataSourceType, setSelectedDataSourceType] = useState('')
  const [dataSourceUri, setDataSourceUri] = useState('')
  const [uploadedFileIds, setUploadedFileIds] = React.useState<string[]>([])
  const [uploadSizeMb, setUploadSizeMb] = React.useState(0)
  const [files, setFiles] = React.useState<{ id: string; file: File }[]>([])
  const { data: dataLoaders, isLoading } = useGetDataLoadersQuery()

  const [uploadDataToDataDirectory] = useUploadDataToDataDirectoryMutation()
  const [addDataSource] = useAddDataSourceMutation()

  useEffect(() => {
    let size = 0
    files.forEach((f) => (size += f.file.size))
    size = size / (1024 * 1024)
    setUploadSizeMb(size)
  }, [files])

  useEffect(() => {
    if (dataLoaders && !selectedDataSourceType)
      setSelectedDataSourceType(dataLoaders[0]?.type)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataLoaders])

  const uploadDocs = async () => {
    try {
      const entries: any = files.map((fileObj: FileObject) => [
        getFilePath(fileObj.file),
        fileObj,
      ])
      const pathToFileMap = Object.fromEntries(entries)
      const paths = Object.keys(pathToFileMap)

      let dataDirectoryFqn = ''
      for (let i = 0; i < files.length; i += 50) {
        const response = await uploadDataToDataDirectory({
          collection_name: '',
          filepaths: paths.slice(i, i + 50),
        }).unwrap()
        dataDirectoryFqn = response.data_directory_fqn

        await Promise.all(
          response.data.map(({ path, url }: any) =>
            uploadArtifactFileWithSignedURI(url, pathToFileMap[path].file).then(
              () =>
                setUploadedFileIds((prev) =>
                  pathToFileMap[path].id
                    ? [...prev, pathToFileMap[path].id]
                    : prev
                )
            )
          )
        )
      }
      return dataDirectoryFqn
    } catch (err) {
      throw err
    }
  }

  const handleDrop = (e: any) => {
    e.stopPropagation()
    e.preventDefault()
    setFiles([...files, ...getUniqueFiles(e.dataTransfer.files)])
  }

  const resetForm = () => {
    setFiles([])
    setDataSourceUri('')
    setSelectedDataSourceType('none')
    setIsSaving(false)
  }

  const handleSubmit = async () => {
    setIsSaving(true)
    try {
      if (selectedDataSourceType === 'localdir' && !files.length) {
        setIsSaving(false)
        return notify(
          'error',
          'Files are required!',
          'Please upload files to process'
        )
      }

      let fqn
      if (selectedDataSourceType === 'localdir') {
        const ddFqn = await uploadDocs()
        const res = await addDataSource({
          type: 'mlfoundry',
          uri: ddFqn,
          metadata: {},
        }).unwrap()
        fqn = res.data_source?.fqn
      } else {
        const res = await addDataSource({
          type: selectedDataSourceType,
          uri: dataSourceUri,
          metadata: {},
        }).unwrap()
        fqn = res.data_source?.fqn
      }

      onClose()
      resetForm()
      notify(
        'success',
        'Document is successfully added!',
        'Updated collection will be available to use after 3-5 minutes.'
      )
    } catch (err: any) {
      notify(
        'error',
        'Failed to add documents to collection!',
        err?.error ||
          err?.details?.msg ||
          err?.message ||
          'There was an error while adding documents to collection.'
      )
    }
    setIsSaving(false)
  }

  return (
    <CustomDrawer
      anchor={'right'}
      open={open}
      onClose={() => {
        onClose()
        resetForm()
      }}
      bodyClassName="p-0"
      width="w-[65vw]"
    >
      <div className="relative w-full">
        {isSaving && (
          <div className="absolute w-full h-full bg-gray-50 z-10 flex flex-col justify-center items-center">
            <div>
              <Spinner center big />
            </div>
            <p className="mt-4">Data Source is being created...</p>
          </div>
        )}
        <div className="font-bold font-inter text-2xl py-2 border-b border-gray-200 px-4">
          Create New Data Source
        </div>
        <div className="h-[calc(100vh-124px)] overflow-y-auto p-4">
          <div className="bg-yellow-100 p-2 mb-2 text-xs rounded">
            Documents that are uploaded will be accessible to the public. Please
            do not upload any confidential or sensitive data.
          </div>
          <div className="mb-4 w-full"></div>
          <div>
            <div className="mb-2">
              <label>
                <div className="label-text font-inter mb-1">
                  Data Source Type
                </div>
                <Select
                  id="data_sources"
                  value={selectedDataSourceType}
                  onChange={(e) => {
                    setDataSourceUri('')
                    setFiles([])
                    setSelectedDataSourceType(e.target.value)
                  }}
                  placeholder="Select Data Source FQN"
                  sx={{
                    background: 'white',
                    height: '42px',
                    width: '100%',
                    border: '1px solid #CEE0F8 !important',
                    outline: 'none !important',
                    '& fieldset': {
                      border: 'none !important',
                    },
                  }}
                >
                  {dataLoaders?.map((source: any) => (
                    <MenuItem value={source.type} key={source.type}>
                      <div className="capitalize flex items-center gap-1.5">
                        {source.type}
                        {source.description && (
                          <div className="text-sm text-gray-500">
                            ({source.description})
                          </div>
                        )}
                      </div>
                    </MenuItem>
                  ))}
                </Select>
              </label>
            </div>
            {selectedDataSourceType === 'localdir' ? (
              <label
                onDragOver={
                  isSaving
                    ? undefined
                    : (e) => {
                        e.stopPropagation()
                        e.preventDefault()
                      }
                }
                onDrop={isSaving ? undefined : handleDrop}
              >
                <span className="label-text font-inter mb-1">
                  Choose files or a zip to upload
                </span>
                <div
                  className={classNames(
                    'flex flex-col flex-1 justify-center items-center w-full h-full bg-white p-4 rounded-lg border-1 border-gray-200 border-dashed',
                    {
                      'hover:bg-gray-100 cursor-pointer': !isSaving,
                      'cursor-default': isSaving,
                    }
                  )}
                >
                  <div className="text-gray-600 flex flex-col justify-center items-center p-3 gap-2">
                    <IconProvider icon="cloud-arrow-up" size={2} />
                    <p className="text-sm leading-5 mb-2 text-center">
                      <span className="font-[500]">
                        Click or Drag &amp; Drop to upload files
                      </span>
                      <span className="block">
                        Limit {DOCS_QA_MAX_UPLOAD_SIZE_MB}MB in total • zip,
                        txt, md
                      </span>
                    </p>
                  </div>
                  <input
                    disabled={isSaving}
                    className="hidden"
                    id="dropzone-file"
                    type="file"
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setFiles([...files, ...getUniqueFiles(e.target.files)])
                    }
                    multiple
                  />
                </div>
              </label>
            ) : (
              <>
                <label htmlFor="collection-name-input">
                  <span className="label-text font-inter mb-1">
                    {selectedDataSourceType === 'github'
                      ? 'GitHub Repo URL'
                      : selectedDataSourceType === 'mlfoundry'
                      ? 'Data Directory FQN'
                      : selectedDataSourceType === 'truefoundry'
                      ? 'Data Source FQN'
                      : selectedDataSourceType === 'artifact'
                      ? 'Artifact Version FQN'
                      : 'URL'}
                  </span>
                </label>
                <input
                  className="block w-full border border-gray-250 outline-none text-md p-2 rounded"
                  id="collection-name-input"
                  placeholder={`${
                    selectedDataSourceType === 'github'
                      ? 'Enter GitHub Repo URL'
                      : selectedDataSourceType === 'mlfoundry'
                      ? 'Enter Data Directory FQN'
                      : selectedDataSourceType === 'truefoundry'
                      ? 'Enter Data Source FQN'
                      : selectedDataSourceType === 'artifact'
                      ? 'Enter Artifact Version FQN'
                      : 'Enter Web URL'
                  }`}
                  value={dataSourceUri}
                  onChange={(e) => setDataSourceUri(e.target.value)}
                />
              </>
            )}
            {!!files.length && selectedDataSourceType === 'localdir' && (
              <div
                className={classNames(
                  'flex flex-col gap-2 p-2 bg-white border rounded-md mt-2',
                  'max-h-[calc(100vh-30.625rem)]'
                )}
              >
                <span className="text-sm flex justify-between">
                  Selected Files ({files.length}){' '}
                  {uploadSizeMb > DOCS_QA_MAX_UPLOAD_SIZE_MB && (
                    <span className="text-xs text-red-700">
                      Selected files total size cannot be more than{' '}
                      {DOCS_QA_MAX_UPLOAD_SIZE_MB}
                      MB
                    </span>
                  )}
                </span>

                <ul
                  className={classNames(
                    'overflow-y-auto',
                    'max-h-[calc(100vh-33.5rem)]'
                  )}
                >
                  {files.map(({ id, file }, idx) => (
                    <li
                      key={id}
                      className="flex flex-row gap-2 p-2 bg-white shadow rounded-lg border mb-2 justify-between items-center"
                    >
                      <div className="flex items-center gap-2">
                        {idx + 1}.
                        <div className="flex flex-col gap-1">
                          <div className="font-inter text-sm leading-4">
                            {file.name}
                          </div>
                          <DarkTooltip title={`${file.size} bytes`}>
                            <Badge
                              text={parseFileSize(file.size)}
                              type="gray"
                              className="cursor-default"
                            />
                          </DarkTooltip>
                        </div>
                      </div>

                      {isSaving ? (
                        <div
                          className={classNames(
                            'w-5 h-5 rounded-full flex items-center justify-center',
                            {
                              'bg-emerald-100 text-emerald-800':
                                uploadedFileIds.includes(id),
                            }
                          )}
                        >
                          {uploadedFileIds.includes(id) ? (
                            <IconProvider
                              icon={'fa-check'}
                              className="text-emerald-800"
                            />
                          ) : (
                            <Spinner small />
                          )}
                        </div>
                      ) : (
                        <Button
                          type="button"
                          icon="trash-alt"
                          iconClasses="text-xs text-gray-400"
                          className="btn-sm bg-white hover:bg-white hover:border-gray-500"
                          onClick={() =>
                            setFiles(files.filter((f) => f.id !== id))
                          }
                          white
                        />
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
        <div className="flex justify-end items-center gap-2 h-[58px] border-t border-gray-200 px-4">
          <Button
            outline
            text="Cancel"
            onClick={() => {
              onClose()
              resetForm()
            }}
            className="border-gray-500 gap-1 btn-sm font-normal"
            type="button"
          />
          <Button
            text="Submit"
            onClick={handleSubmit}
            className="gap-1 btn-sm font-normal"
            type="button"
            disabled={
              isSaving ||
              (selectedDataSourceType === 'localdir' &&
                (files.length === 0 ||
                  uploadSizeMb > DOCS_QA_MAX_UPLOAD_SIZE_MB)) ||
              (selectedDataSourceType !== 'localdir' && !dataSourceUri)
            }
          />
        </div>
      </div>
    </CustomDrawer>
  )
}

export default NewDataSource
