import React, { useState, useEffect, useMemo } from 'react'
import IconProvider from '@/components/assets/IconProvider'
import Button from '@/components/base/atoms/Button'
import { LightTooltip } from '@/components/base/atoms/Tooltip'
import {
  useDeleteCollectionMutation,
  useGetCollectionStatusQuery,
} from '@/stores/qafoundry'

interface CollectionCardProps {
  isSelectedCollection: boolean
  collectionName: string
  embedderConfig: object
  hideInfo?: boolean
  enableErrorSelection?: boolean
  onClick: () => void
}

const CollectionCard = ({
  isSelectedCollection,
  collectionName,
  embedderConfig: embedderConfigRaw,
  hideInfo,
  enableErrorSelection,
  onClick,
}: CollectionCardProps) => {
  const [stopPolling, setStopPolling] = useState(false)
  const [isReady, setIsReady] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [isInfoIconVisible, setIsInfoIconVisible] = useState(false)
  const isDeleteOptionEnabled = import.meta.env.VITE_DOCS_QA_DELETE_COLLECTIONS

  const [deleteCollection, deleteCollectionRes] = useDeleteCollectionMutation()
  const { data, isError } = useGetCollectionStatusQuery(
    {
      collectionName: collectionName,
    },
    {
      pollingInterval: stopPolling ? undefined : 5000,
      skip: !collectionName,
    }
  )

  useEffect(() => {
    if (data?.status === 'COMPLETED') {
      setStopPolling(true)
      setIsReady(true)
      setHasError(false)
    } else if (data?.status === 'FAILED' || isError) {
      setHasError(true)
      setStopPolling(true)
      setIsReady(false)
    } else {
      setStopPolling(false)
      setHasError(false)
      setIsReady(false)
    }
  }, [data, isError])

  const embedderConfig = useMemo(
    () => (embedderConfigRaw ? Object.entries(embedderConfigRaw) : []),
    [embedderConfigRaw]
  )

  return (
    <div
      className={`cursor-pointer mb-1 px-5 hover:bg-gray-150 py-[10px] rounded ${
        !isReady && !enableErrorSelection && 'cursor-not-allowed'
      } ${isSelectedCollection ? 'bg-gray-200 border border-[#818cf8]' : ''}`}
      onClick={() => {
        if (!isReady && !enableErrorSelection) return
        onClick()
      }}
      onMouseEnter={() => setIsInfoIconVisible(true)}
      onMouseLeave={() => setIsInfoIconVisible(false)}
    >
      <div className="flex justify-between items-center">
        <div className="flex gap-2.5 items-center">
          <IconProvider
            icon="fa-regular fa-files"
            size={1}
            className="text-gray-500"
          />
          <div className="text-gray-950 font-[500] text-base">
            {collectionName}
          </div>
        </div>
        {!hideInfo && (
          <LightTooltip
            title={
              <div className="p-2 bg-white text-black cursor-default w-[16rem]">
                {/* {hasError && (
                  <p className="text-error text-xs mb-1">
                    {data?.message || 'Failed to fetch status'}
                  </p>
                )} */}
                <p className="font-[500] text-xs mb-1">Embedder Config:</p>
                <p className="text-gray-600 text-xs mb-2">
                  {!!embedderConfig.length
                    ? embedderConfig.map((e) => {
                        if (e[1]) {
                          return (
                            <span key={e[0]}>
                              {e[0]}:{' '}
                              {typeof e[1] === 'object'
                                ? JSON.stringify(e[1])
                                : e[1]}
                            </span>
                          )
                        }
                        return
                      })
                    : ''}
                </p>
                {!isReady && !hasError && (
                  <p className="text-xs mb-2">{data?.message}</p>
                )}
                {isDeleteOptionEnabled === 'true' && (
                  <div className="flex justify-center">
                    <Button
                      text="Delete Collection"
                      outline
                      disabled={deleteCollectionRes.isLoading}
                      className="border-gray-200 shadow bg-base-100 btn-sm font-normal px-2.5"
                      onClick={() =>
                        deleteCollection({ collectionName: collectionName })
                      }
                    />
                  </div>
                )}
              </div>
            }
          >
            {
              // hasError ? (
              //   <div className="w-[18px] h-[18px] flex justify-center items-center">
              //     <IconProvider
              //       icon="triangle-exclamation"
              //       className="text-error p-1 pr-2"
              //       size={0.8}
              //     />
              //   </div>
              // ) :
              // !isReady ? (
              //   <div className="w-[18px] h-[18px] flex justify-center items-center bg-[#6366F1] rounded-full">
              //     <IconProvider
              //       icon="spinner"
              //       className="text-white fa-spin p-1"
              //       size={0.8}
              //     />
              //   </div>
              // ) :
              <div
                className={`flex items-center gap-1 ${
                  !isInfoIconVisible && !isSelectedCollection && 'hidden'
                }`}
              >
                <IconProvider
                  icon="circle-info"
                  className="text-gray-500 p-1 text-sm"
                  size={1}
                />
              </div>
            }
          </LightTooltip>
        )}
      </div>
    </div>
  )
}

export default CollectionCard
