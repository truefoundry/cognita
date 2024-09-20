import React, { useState, useEffect } from 'react'
import { CarbonConnect, EmbeddingGenerators } from 'carbon-connect'
import type { OnSuccessData } from 'carbon-connect'
import axios from 'axios'

import {
  useAddDataSourceMutation,
  useGetDataSourcesQuery,
} from '@/stores/qafoundry'

import Button from '@/components/base/atoms/Button'
import notify from '@/components/base/molecules/Notify'
import Logo from '@/assets/img/logos/logo.svg'
import { ENABLED_INTEGRATIONS, tokenFetcher } from '@/utils/carbon'


const TAGS = {
  tag1: 'cognita',
  tag2: 'gdrive',
}

const MAX_FILE_SIZE = 10000000

const CarbonIntegration: React.FC<{
  customerId: string
}> = ({ customerId }) => {
  const [isOpen, setIsOpen] = useState(false)

  const [addDataSource] = useAddDataSourceMutation()
  const { data: dataSources } = useGetDataSourcesQuery()

  const successHandler = (data: OnSuccessData) => {
    if (data?.action === 'ADD') {
      const externalId = data?.data?.data_source_external_id
      if (!externalId) return
      getDataSources(externalId)
    }
  }

  const getDataSources = async (dataSourceExternalId: string) => {
    const carbonAccessToken = await tokenFetcher(customerId)
    const response = await axios.get<{
      active_integrations: {
        id: string
        data_source_external_id: string
      }[]
    }>(
      // Undocumented API?
      'https://api.carbon.ai/integrations/?include_files=false',
      {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `token ${carbonAccessToken.access_token}`,
        },
      }
    )
    let newDataSourceId = undefined

    newDataSourceId = response.data.active_integrations.findLast(res => res.data_source_external_id === dataSourceExternalId)?.id

    if (newDataSourceId === undefined) return

    return syncCarbon(dataSourceExternalId, newDataSourceId)
  }

  const syncCarbon = async (externalId: string, internalId: string) => {
    if (dataSources) {
      const existingDataSource = dataSources.find(
        (ds: any) => ds.uri === externalId
      )
      if (existingDataSource) {
        return
      }

      return addDataSource({
        type: 'carbon',
        uri: externalId,
        metadata: {
          internalId,
          customerId,
        },
      }).unwrap().catch((err) => {
        notify(
          'error',
          'Failed to add documents to collection!',
          err?.error ||
            err?.details?.msg ||
            err?.message ||
            'There was an error while adding documents to collection.'
        )
      })
    }
  }

  useEffect(() => {
    tokenFetcher(customerId)
      .catch((err) => {})
  }, [])

  return (
    <>
      <CarbonConnect
        orgName="Cognita"
        brandIcon={Logo}
        embeddingModel={EmbeddingGenerators.OPENAI_ADA_LARGE_1024}
        tokenFetcher={() => tokenFetcher(customerId)}
        tags={TAGS}
        maxFileSize={MAX_FILE_SIZE}
        enabledIntegrations={ENABLED_INTEGRATIONS}
        onSuccess={successHandler}
        useRequestIds
        theme='light'
        open={isOpen}
        setOpen={setIsOpen}
        chunkSize={1500}
        zIndex={1500}
      />
      <Button
        text="Connect Carbon"
        className="btn-sm text-sm bg-black text-white hover:bg-gray-700"
        onClick={() => setIsOpen(true)}
      />
    </>
  )
}

export default CarbonIntegration
