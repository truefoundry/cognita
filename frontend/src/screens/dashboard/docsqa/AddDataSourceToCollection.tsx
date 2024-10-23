import Badge from '@/components/base/atoms/Badge'
import Button from '@/components/base/atoms/Button'
import CustomDrawer from '@/components/base/atoms/CustomDrawer'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import notify from '@/components/base/molecules/Notify'
import SimpleCodeEditor from '@/components/base/molecules/SimpleCodeEditor'
import {
  Collection,
  useAddDocsToCollectionMutation,
  useGetDataSourcesQuery,
  useIngestDataSourceMutation,
} from '@/stores/qafoundry'
import { notifyError } from '@/utils/error'
import { MenuItem, Select } from '@mui/material'
import React, { useState } from 'react'

export const defaultParserConfigs = `{
  ".pdf": {
    "name": "MultiModalParser",
    "parameters": {
      "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o-mini"
      },
      "prompt": "Given an image containing one or more charts/graphs, and texts, provide a detailed analysis of the data represented in the charts. Your task is to analyze the image and provide insights based on the data it represents. Specifically, the information should include but not limited to: - Title of the Image: Provide a title from the charts or image if any. - Type of Chart: Determine the type of each chart (e.g., bar chart, line chart, pie chart, scatter plot, etc.) and its key features (e.g., labels, legends, data points). - Data Trends: Describe any notable trends or patterns visible in the data. This may include increasing/decreasing trends, seasonality, outliers, etc. - Key Insights: Extract key insights or observations from the charts. What do the charts reveal about the underlying data? Are there any significant findings that stand out? - Data Points: Identify specific data points or values represented in the charts, especially those that contribute to the overall analysis or insights. - Comparisons: Compare different charts within the same image or compare data points within a single chart. Highlight similarities, differences, or correlations between datasets. - Conclude with a summary of the key findings from your analysis and any recommendations based on those findings."
    }
  }
}`

interface NewCollectionProps {
  collectionName: string
  open: boolean
  onClose: () => void
}

const AddDataSourceToCollection = ({
  collectionName,
  open,
  onClose,
}: NewCollectionProps) => {
  const [isSaving, setIsSaving] = useState(false)
  const [selectedDataSource, setSelectedDataSource] = useState('none')
  const [parserConfigs, setParserConfigs] = useState(defaultParserConfigs)
  const { data: dataSources } = useGetDataSourcesQuery()

  const [addDocsToCollection] = useAddDocsToCollectionMutation()
  const [ingestDataSource] = useIngestDataSourceMutation()

  const resetForm = () => {
    setSelectedDataSource('none')
    setIsSaving(false)
  }

  const handleSubmit = async () => {
    setIsSaving(true)
    try {
      const addDocsParams = {
        data_source_fqn: selectedDataSource,
        collection_name: collectionName,
        parser_config: JSON.parse(parserConfigs),
      }

      await addDocsToCollection(addDocsParams).unwrap()
      await ingestDataSource({
        collection_name: collectionName,
        data_source_fqn: selectedDataSource,
        data_ingestion_mode: 'INCREMENTAL',
        raise_error_on_failure: true,
        run_as_job: true,
      })

      onClose()
      resetForm()
      notify(
        'success',
        'Data Source is successfully added!',
        'Updated collection will be available to use after 3-5 minutes.',
      )
    } catch (err: any) {
      notifyError(
        'Failed to add documents to collection!',
        err,
        'There was an error while adding documents to collection',
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
            <div className="font-bold font-inter text-2xl py-2 border-b border-gray-200 px-4 flex gap-1 items-center">
              Add data source to collection{' '}
              <Badge
                text={collectionName}
                className="text-xl bg-gray-150 border font-semibold border-gray-200 mx-1"
                style={{ color: '#010202' }}
                customPadding="py-[0.75rem]"
              />
            </div>
            <div className="h-[calc(100vh-124px)] overflow-y-auto p-4">
              <div className="bg-yellow-100 p-2 mb-2 text-xs rounded">
                Documents that are uploaded will be accessible to the public.
                Please do not upload any confidential or sensitive data.
              </div>
              <div className="mb-4 w-full"></div>
              <div>
                <div className="mb-2">
                  <label>
                    <div className="label-text font-inter mb-1">
                      Select Data Source
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
                          <span>{source.fqn}</span>
                        </MenuItem>
                      ))}
                    </Select>
                  </label>
                </div>
                {selectedDataSource !== 'none' && (
                  <div className="mb-5">
                    <div className="flex text-xs mb-1">
                      <div>Type :</div>
                      &nbsp;
                      <div>
                        {
                          dataSources?.filter(
                            (source) => source.fqn === selectedDataSource,
                          )[0].type
                        }
                      </div>
                    </div>
                    <div className="flex text-xs">
                      <div>URI :</div>
                      &nbsp;
                      <div>
                        {
                          dataSources?.filter(
                            (source) => source.fqn === selectedDataSource,
                          )[0].uri
                        }
                      </div>
                    </div>
                  </div>
                )}
                <div className="mb-4">
                  <div className="label-text font-inter mb-1">
                    Parser Configs
                  </div>
                  <SimpleCodeEditor
                    language="json"
                    height={200}
                    value={parserConfigs}
                    onChange={(value) => setParserConfigs(value ?? '')}
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end items-center gap-2 h-[3.625rem] border-t border-gray-200 px-4">
              <Button
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
                className="gap-1 btn-sm font-normal btn-neutral"
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
