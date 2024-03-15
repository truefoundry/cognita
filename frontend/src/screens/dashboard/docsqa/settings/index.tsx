import Badge from '@/components/base/atoms/Badge'
import Button from '@/components/base/atoms/Button'
import LinkButton from '@/components/base/atoms/Link'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import { Collection, useGetCollectionsQuery } from '@/stores/qafoundry'
import React, { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import AddDataSourceToCollection from '../AddDataSourceToCollection'
import CollectionCard from '../CollectionCard'
import NewCollection from '../NewCollection'
import NoCollections from '../NoCollections'
import RunsHistoryDrawer from '../RunsHistoryDrawer'
import DataSourcesTable from './DataSourcesTable'

const DocsQASettings = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [newCollectionModalOpen, setNewCollectionModalOpen] = useState(searchParams.get('newCollectionOpen') === 'true')
  const [selectedCollection, setSelectedCollection] = useState<
    Collection | undefined
  >()
  const [openDataSourceLinkForm, setOpenDataSourceLinkForm] = useState(false)
  const [runsHistoryDrawerOpen, setRunsHistoryDrawerOpen] = useState(false)
  const [selectedDataSourceFqn, setSelectedDataSourceFqn] = useState('')

  const { data: collections, isLoading } = useGetCollectionsQuery()

  const associatedDataSourcesRows = useMemo(() => {
    const rows = []
    if (selectedCollection) {
      for (const [key, value] of Object.entries(
        selectedCollection.associated_data_sources
      )) {
        const dataSourceType = key.split(':')[0]
        if (dataSourceType === 'data-dir') {
          rows.push({
            id: key,
            type: 'local',
            source: '-',
            fqn: key,
          })
        } else if (!value?.data_source?.uri) {
          rows.push({
            id: key,
            type: dataSourceType,
            source: '-',
            fqn: key,
          })
        } else {
          rows.push({
            id: key,
            type: dataSourceType,
            source: value.data_source.uri,
            fqn: key,
          })
        }
      }
    }

    return rows
  }, [collections, selectedCollection])

  useEffect(() => {
    if (collections) {
      if (!selectedCollection) {
        setSelectedCollection(collections[0])
      } else  {
        setSelectedCollection(collections.find((c) => c.name === selectedCollection.name))
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collections])

  const openRunsHistoryDrawer = (fqn: string) => {
    setSelectedDataSourceFqn(fqn)
    setRunsHistoryDrawerOpen(true)
  }

  return (
    <>
      <div className="flex gap-5 h-full w-full">
        <div className="h-full bg-[#f0f7ff] rounded-lg py-5 w-[280px] border border-gray-250">
          <LinkButton
            icon="plus"
            iconClasses="fa-xs text-slate-400"
            text={<span className="whitespace-nowrap">New Collection</span>}
            rounded
            className="bg-black btn-sm flex-nowrap w-[calc(100%-32px)] mx-4 mb-4"
            onClick={() => setNewCollectionModalOpen(true)}
          />
          <div
            className="h-[calc(100vh-202px)] overflow-y-auto custom-scrollbar"
            style={{
              paddingRight: '0rem',
            }}
          >
            {isLoading && <Spinner center />}
            {collections?.map((collection, index) => (
              <CollectionCard
                key={index}
                collectionName={collection.name}
                embedderConfig={collection.embedder_config}
                isSelectedCollection={
                  selectedCollection?.name === collection.name
                }
                enableErrorSelection
                onClick={() => {
                  setSelectedCollection(collection)
                }}
              />
            ))}
          </div>
        </div>
        {selectedCollection ? (
          <div className="h-full border rounded-lg border-[#CEE0F8] w-[calc(100%-300px)] bg-white p-4">
            <div className="flex justify-between mb-3">
              <div>
                <div className="text-base font-medium mb-1">
                  Data Sources for{' '}
                  <Badge
                    text={selectedCollection.name}
                    type="white"
                    textClasses="text-base"
                  />{' '}
                  collection
                </div>
                <div className="text-sm">
                  Embedder Used :{' '}
                  {selectedCollection?.embedder_config?.config?.model}
                </div>
              </div>
              <Button
                white
                icon={'plus'}
                iconClasses="text-gray-400"
                text={'Link Data Source'}
                className="btn-sm text-sm bg-white"
                onClick={() => setOpenDataSourceLinkForm(true)}
              />
            </div>
            <div className='bg-[#f7fbff] h-[calc(100%-70px)] p-4'>
              <DataSourcesTable
                collectionName={selectedCollection.name}
                rows={associatedDataSourcesRows}
                openRunsHistoryDrawer={openRunsHistoryDrawer}
              />
            </div>
          </div>
        ) : isLoading ? (
          <Spinner center medium />
        ) : (
          <NoCollections />
        )}
      </div>
      {newCollectionModalOpen && (
        <NewCollection
          open={newCollectionModalOpen}
          onClose={() => {
            if (searchParams.has('newCollectionOpen')) {
              searchParams.delete('newCollectionOpen')
              setSearchParams(searchParams)
            }
            setNewCollectionModalOpen(false)
          }}
        />
      )}
      {selectedCollection && openDataSourceLinkForm && (
        <AddDataSourceToCollection
          open={openDataSourceLinkForm}
          onClose={() => {
            setOpenDataSourceLinkForm(false)
          }}
          collection={selectedCollection}
        />
      )}
      {runsHistoryDrawerOpen && selectedCollection && selectedDataSourceFqn && (
        <RunsHistoryDrawer
          open={runsHistoryDrawerOpen}
          onClose={() => setRunsHistoryDrawerOpen(false)}
          collectionName={selectedCollection.name}
          selectedDataSource={selectedDataSourceFqn}
        />
      )}
    </>
  )
}

export default DocsQASettings
