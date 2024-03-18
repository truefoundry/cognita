import Button from '@/components/base/atoms/Button'
import CustomDrawer from '@/components/base/atoms/CustomDrawer'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import notify from '@/components/base/molecules/Notify'
import {
  Collection,
  useAddDocsToCollectionMutation,
  useGetDataSourcesQuery,
} from '@/stores/qafoundry'
import { MenuItem, Select } from '@mui/material'
import React, { useState } from 'react'

interface NewCollectionProps {
  collection: Collection
  open: boolean
  onClose: () => void
}

const AddDataSourceToCollection = ({
  collection,
  open,
  onClose,
}: NewCollectionProps) => {
  const [isSaving, setIsSaving] = useState(false)
  const [selectedDataSource, setSelectedDataSource] = useState('none')
  const { data: dataSources } = useGetDataSourcesQuery()

  const [addDocsToCollection] = useAddDocsToCollectionMutation()

  const resetForm = () => {
    setSelectedDataSource('none')
    setIsSaving(false)
  }

  const handleSubmit = async () => {
    setIsSaving(true)
    try {
      const addDocsParams = {
        data_source_fqn: selectedDataSource,
        collection_name: collection.name,
        parser_config: {
          chunk_size: 500,
          chunk_overlap: 0,
          parser_map: {
            '.md': 'MarkdownParser',
            '.pdf': 'PdfParserFast',
            '.txt': 'TextParser',
          },
        },
      }

      await addDocsToCollection(addDocsParams).unwrap()

      onClose()
      resetForm()
      notify(
        'success',
        'Data Source is successfully added!',
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
      {!dataSources ? (
        <div className="flex justify-center items-center w-full h-full">
          <Spinner center medium />
        </div>
      ) : (
        <>
          <div className="relative w-full">
            {isSaving && (
              <div className="absolute w-full h-full bg-gray-50 z-10 flex flex-col justify-center items-center">
                <div>
                  <Spinner center big />
                </div>
                <p className="mt-4">
                  Data Source is being added to the collection
                </p>
              </div>
            )}
            <div className="font-bold font-inter text-2xl py-2 border-b border-gray-200 px-4">
              Add data source to collection
            </div>
            <div className="h-[calc(100vh-124px)] overflow-y-auto p-4">
              <div className="bg-yellow-100 p-2 mb-2 text-xs rounded">
                Documents that are uploaded will be accessible to the public.
                Please do not upload any confidential or sensitive data.
              </div>
              <div className="mb-4 w-full"></div>
              <div>
                <div className="mb-4">
                  <label>
                    <div className="label-text font-inter mb-1">
                      Data Source FQN
                    </div>
                    <Select
                      id="data_sources"
                      value={selectedDataSource}
                      onChange={(e) => {
                        setSelectedDataSource(e.target.value)
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
                      <MenuItem value={'none'} disabled>
                        Select a Data Source FQN
                      </MenuItem>
                      {dataSources?.map((source: any) => (
                        <MenuItem value={source.fqn} key={source.fqn}>
                          <span className="capitalize">{source.fqn}</span>
                        </MenuItem>
                      ))}
                    </Select>
                  </label>
                </div>
                {selectedDataSource !== 'none' && (
                  <>
                    <div className="flex text-sm mb-1">
                      <div>Type :</div>
                      &nbsp;
                      <div className="capitalize">
                        {
                          dataSources?.filter(
                            (source) => source.fqn === selectedDataSource
                          )[0].type
                        }
                      </div>
                    </div>
                    <div className="flex text-sm">
                      <div>URI :</div>
                      &nbsp;
                      <div>
                        {
                          dataSources?.filter(
                            (source) => source.fqn === selectedDataSource
                          )[0].uri
                        }
                      </div>
                    </div>
                  </>
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
                disabled={selectedDataSource === 'none'}
              />
            </div>
          </div>
        </>
      )}
    </CustomDrawer>
  )
}

export default AddDataSourceToCollection
