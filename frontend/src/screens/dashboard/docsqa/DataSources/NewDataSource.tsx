import React, { useEffect, useState } from 'react'
import { useForm, SubmitHandler, Controller, FormProvider } from "react-hook-form"
import { startCase } from 'lodash'
import { uploadArtifactFileWithSignedURI } from '@/api/truefoundry'
import Button from '@/components/base/atoms/Button'
import CustomDrawer from '@/components/base/atoms/CustomDrawer'
import Spinner from '@/components/base/atoms/Spinner'
import notify from '@/components/base/molecules/Notify'
import {
  IS_LOCAL_DEVELOPMENT,
  LOCAL_SOURCE_NAME,
  TFY_SOURCE_NAME,
  WEB_SOURCE_NAME,
} from '@/stores/constants'
import {
  customerId,
  useAddDataSourceMutation,
  useGetDataLoadersQuery,
  useUploadDataToDataDirectoryMutation,
  useUploadDataToLocalDirectoryMutation,
} from '@/stores/qafoundry'
import classNames from '@/utils/classNames'
import axios from 'axios'
import WebDataSource from './WebDataSource'
import { FormInputData } from './FormType'
import FileUpload from './FileUpload'
import { getFilePath } from '@/utils/artifacts'
import { data } from 'autoprefixer'


type FileObject = {
  id: string
  file: File
}

interface NewDataSourceProps {
  onClose: () => void
}

const NewDataSource: React.FC<NewDataSourceProps> = ({ onClose }) => {
  const [isNewDataSourceDrawerOpen, setIsNewDataSourceDrawerOpen] =
    React.useState(false)

  const [localUploadedFileIds, setLocalUploadedFileIds] = useState<string[]>([])

  const { data: dataLoaders } = useGetDataLoadersQuery()


  const [uploadDataToDataDirectory] = useUploadDataToDataDirectoryMutation()
  const [uploadDataToLocalDirectory] = useUploadDataToLocalDirectoryMutation()
  const [addDataSource] = useAddDataSourceMutation()


  const close = () => {
    setIsNewDataSourceDrawerOpen(false)
    onClose()
  }

  const uploadDocs = async (uploadName: string, files: FormInputData['localdir']['files']) => {
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
          upload_name: uploadName,
        }).unwrap()
        dataDirectoryFqn = response.data_directory_fqn

        // Upload files to data directory and collect file ids
        const uploadedFileIds = await Promise.all(
          response.data.map(async ({ path, signed_url }: any) => {
            try {
              await uploadArtifactFileWithSignedURI(signed_url, pathToFileMap[path].file);
              return pathToFileMap[path].id;
            } catch (error) {
              console.error(`Failed to upload file: ${path}`, error);
              return null;
            }
          })
        );

        // Update the uploaded file ids state, filtering out null values
        setLocalUploadedFileIds(
          [...localUploadedFileIds, ...uploadedFileIds.filter(Boolean)]
        );
      }
      return dataDirectoryFqn
    } catch (err) {
      throw err
    }
  }


  const methods = useForm<FormInputData>({ mode: 'onChange'})

  const selectedDataSourceType = methods.watch('dataSourceType')

  const onSubmit: SubmitHandler<FormInputData> = async (data) => {
    try {
      if (!methods.formState.isValid) {
        return notify(
          'error',
          'Invalid Form!',
          Object.values(methods.formState?.errors || {})
            .map((e) => e.message).join(', ')
            || 'Please fill all required fields'
        )
      }
      if (data.dataSourceType === 'localdir' && !data.localdir) {
        return notify(
          'error',
          'Files are required!',
          'Please upload files to process'
        )
      }
      let fqn
      let res: { data_source: { fqn: string } }
      switch (data.dataSourceType) {
        case LOCAL_SOURCE_NAME:
          if (IS_LOCAL_DEVELOPMENT) {
            res = await uploadDataToLocalDirectory({
              files: data.localdir.files.map((f) => f.file),
              upload_name: data.localdir.name,
            }).unwrap()
          } else {
            const ddFqn = await uploadDocs(data.localdir.name, data.localdir.files)
            res = await addDataSource({
              type: TFY_SOURCE_NAME,
              uri: ddFqn
            }).unwrap()
          }
          break;
        case TFY_SOURCE_NAME:
          res = await addDataSource({
            type: selectedDataSourceType,
            uri: data.dataSourceUri,
            metadata: {
              customerId: customerId,
            },
          }).unwrap()
          break;
        case WEB_SOURCE_NAME:
          res = await addDataSource({
            type: WEB_SOURCE_NAME,
            uri: data.dataSourceUri,
            metadata: {
              use_sitemap: data.webConfig.use_sitemap,
            },
          }).unwrap()
          break;
        default:
          throw new Error('Invalid data source type')
      }

      fqn = res.data_source?.fqn

      close()
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
  }

  useEffect(() => {
    resetForm()
  }, [dataLoaders])

  const resetForm = () => {
    if (dataLoaders?.[0]?.type) {
      methods.reset({
        dataSourceType: dataLoaders[0].type,
      })
      setLocalUploadedFileIds([])
    }
  }

  return (
    <>
      <Button
          icon={'plus'}
          iconClasses="text-gray-400"
          text={'New Data Source'}
          className="btn-sm text-sm bg-black text-white hover:bg-gray-700"
          onClick={() => setIsNewDataSourceDrawerOpen(true)}
        />
      <CustomDrawer
        anchor={'right'}
        open={isNewDataSourceDrawerOpen}
        onClose={() => {
          close()
          resetForm()
        }}
        bodyClassName="z-2"
        width="w-[65vw]"
      >
        <FormProvider {...methods}>
          <form className="relative w-full" onSubmit={methods.handleSubmit(onSubmit)}>
            {methods.formState.isSubmitting && (
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
            <div className="h-[calc(100vh-124px)] p-4 overflow-auto">
              <div className="bg-yellow-100 p-2 my-4 text-xs rounded">
                Documents that are uploaded will be accessible to the public.
                Please do not upload any confidential or sensitive data.
              </div>
              <div>
                <div className="mb-2">
                  <div className="label-text font-inter mb-1">
                    Data Source Type
                  </div>
                  {dataLoaders && <Controller
                    name="dataSourceType"
                    control={methods.control}
                    defaultValue={dataLoaders[0].type}
                    render={({ field }) => <div className='grid grid-cols-2 gap-2'>
                        {dataLoaders.map((source: any) => (
                          <button
                            key={source.type}
                            className={classNames(
                              'flex p-4 rounded-lg border border-gray-200 active:scale-95 transition-all',
                              {
                                'bg-gray-700 text-white': field.value === source.type,
                                'hover:bg-gray-100': field.value !== source.type,
                              }
                            )}
                            onClick={() => {
                              methods.reset({
                                dataSourceType: source.type,
                              })
                            }}
                            type='button'
                          >
                            <div className="capitalize">
                              <h5 className='text-lg font-semibold text-left'>{startCase(source.type)}</h5>
                              {source.description && (
                                <div className="text-sm text-gray-500">
                                  ({source.description})
                                </div>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    }
                  />}

                </div>
                <div className="my-4 flex flex-col gap-2">
                  {selectedDataSourceType === WEB_SOURCE_NAME && (
                    <WebDataSource />
                  )}
                  {selectedDataSourceType === LOCAL_SOURCE_NAME && (
                    <FileUpload
                      uploadedFileIds={localUploadedFileIds}
                    />
                  )}
                  {[TFY_SOURCE_NAME].includes(selectedDataSourceType) && (
                    <label className="form-control">
                      <div className='label'>
                        <span className="label-text font-inter">
                          {selectedDataSourceType === 'truefoundry'
                            ? 'Data Source FQN *'
                            : 'Artifact Version FQN *'}
                        </span>
                      </div>
                      <input
                        className="block w-full border border-gray-250 outline-none text-md p-2 rounded"
                        {...methods.register("dataSourceUri", { required: true })}
                        placeholder={`${
                          selectedDataSourceType === 'truefoundry'
                            ? 'Enter Data Source FQN'
                            : 'Enter Artifact Version FQN'
                        }`}
                      />
                    </label>
                  )}
                </div>

              </div>
            </div>
            <div className="flex justify-end items-center gap-2 h-[58px] border-t border-gray-200 px-4">
              <Button
                text="Cancel"
                onClick={() => {
                  onClose()
                }}
                className="border-gray-500 gap-1 btn-sm font-normal"
                type="reset"
              />
              <Button
                text="Submit"
                className="gap-1 btn-sm font-normal btn-neutral"
                type="submit"
                disabled={
                  methods.formState.isSubmitting ||
                  !methods.formState.isValid
                }
              />
            </div>
          </form>
        </FormProvider>
      </CustomDrawer>
    </>
  )
}

export default NewDataSource
