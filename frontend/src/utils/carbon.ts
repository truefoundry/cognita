import { customerId } from '@/stores/qafoundry';
import { CARBON_API_KEY } from "@/stores/constants"
import axios from "axios"
import { Integration, IntegrationName } from "carbon-connect"
import file from "carbon-connect"

export type CarbonToken = {
  access_token: string
  refresh_token: string
}

export const tokenFetcher = async (customerId: string): Promise<CarbonToken> => {
  const carbonAccessToken = window.sessionStorage.getItem(
    'carbon_access_token'
  )
  if (carbonAccessToken) return JSON.parse(carbonAccessToken) as CarbonToken
  const response = await axios.get<CarbonToken>(
    'https://api.carbon.ai/auth/v1/access_token',
    {
      headers: {
        'Content-Type': 'application/json',
        'customer-id': customerId,
        authorization: `Bearer ${CARBON_API_KEY}`,
      },
    }
  )
  window.sessionStorage.setItem('carbon_access_token', JSON.stringify(response.data))
  return response.data
}

const COMMON_CONFIG: Partial<Integration> = {
  chunkSize: 1500,
  overlapSize: 20,
  skipEmbeddingGeneration: true,
}

type CustomIntegration = Integration & {
  useCarbonFilePicker?: boolean
}

export const ENABLED_INTEGRATIONS: CustomIntegration[] = [
  // {
  //   id: IntegrationName.LOCAL_FILES,
  //   ...COMMON_CONFIG
  // },
  // {
  //   id: IntegrationName.WEB_SCRAPER,
  //   htmlTagsToSkip: ['script', 'style', 'noscript'],
  //   ...COMMON_CONFIG,
  // },
  {
    id: IntegrationName.ZENDESK,
    ...COMMON_CONFIG
  },
  {
    id: IntegrationName.S3,
    ...COMMON_CONFIG
  },
  {
    id: IntegrationName.SHAREPOINT,
    ...COMMON_CONFIG
  },
  {
    id: IntegrationName.GOOGLE_DRIVE,
    chunkSize: 1000,
    overlapSize: 20,
  },
  {
    id: IntegrationName.NOTION,
    ...COMMON_CONFIG
  },
  {
    id: IntegrationName.DROPBOX,
    ...COMMON_CONFIG
  },
  {
    id: IntegrationName.ONEDRIVE,
    ...COMMON_CONFIG
  },
  {
    id: IntegrationName.CONFLUENCE,
    useCarbonFilePicker: true,
    syncSourceItems: true,
    ...COMMON_CONFIG
  },
]

export type FileMeta = {
  presigned_url: string;
  external_url: string;
  name: string;
  file_statistics?: {
    file_format: string;
    mime_type: string;
  }
}

export async function getFileInfo(customerId: string, externalFileId: string): Promise<FileMeta | undefined> {
  const file = await axios<{
    results: FileMeta[]
  }>(
    {
      method: 'post',
      url: 'https://api.carbon.ai/user_files_v2',
      headers: {
        Authorization: `Bearer ${CARBON_API_KEY}`,
        'customer-id': customerId,
      },
      data: {
        filters: {
          external_file_ids: [externalFileId],
        },
        include_raw_file: true
      }
    }
  )

  return file?.data?.results?.[0]
}
