import { createApi } from '@reduxjs/toolkit/query/react'

// import * as T from './types'
import { createBaseQuery } from '../utils'

export interface ModelConfig {
  name: string
  parameters: {
    temperature?: number
    maximum_length?: number
    top_p?: number
    top_k?: number
    repetition_penalty?: number
    frequency_penalty?: number
    presence_penalty?: number
    stop_sequences?: string[]
  }
}

export interface CollectionQueryDto {
  collection_name: string
  retriever_config: {
    search_type: string
    k: number
    fetch_k?: number
  }
  query: string
  model_configuration: ModelConfig
}

interface DataSource {
  type: string
  uri?: string
  metadata?: object
  fqn: string
}

export interface AssociatedDataSource {
  data_source_fqn: string
  parser_config: {
    chunk_size: number
    chunk_overlap: number
    parser_map: {
      [key: string]: string
    }
  }
  data_source: DataSource
}

interface EmbedderConfig {
  description?: string
  provider?: string
  config?: {
    model: string
  }
}

export interface Collection {
  name: string
  description?: string
  embedder_config: EmbedderConfig
  associated_data_sources: {
    [key: string]: AssociatedDataSource
  }
  chunk_size?: number
}

interface AddDataSourcePayload {
  type: string
  uri: string
  metadata?: object
}

interface DataIngestionRun {
  collection_name: string
  data_source_fqn: string
  parser_config?: {
    chunk_size?: number
    chunk_overlap?: number
    parser_map?: {
      [key: string]: string
    }
  }
  data_ingestion_mode: string
  raise_error_on_failure: boolean
  name: string
  status: string
}

const baseQAFoundryPath = import.meta.env.VITE_QA_FOUNDRY_URL

export const qafoundryApi = createApi({
  reducerPath: 'qafoundry',
  baseQuery: createBaseQuery({
    baseUrl: baseQAFoundryPath,
  }),
  tagTypes: ['Collections', 'DataSources'],
  endpoints: (builder) => ({
    // * Queries
    getCollections: builder.query<Collection[], void>({
      query: () => ({
        url: '/v1/collections/',
        responseHandler: (response) =>
          response
            .json()
            .then((data: { collections: Collection[] }) => data.collections),
      }),
      providesTags: ['Collections'],
    }),
    getCollectionStatus: builder.query({
      query: (payload: { collectionName: string }) => ({
        url: `/v1/collections/data_ingestion_run/${payload.collectionName}/status`,
        method: 'GET',
      }),
    }),
    getDataLoaders: builder.query<any, void>({
      query: () => ({
        url: '/v1/components/dataloaders',
        method: 'GET',
      }),
    }),
    getAllEnabledChatModels: builder.query<any, void>({
      query: () => ({
        url: '/v1/internal/models?model_type=chat',
        method: 'GET',
        responseHandler: (response) =>
          response.json().then((data: { models: object[] }) => data.models),
      }),
    }),
    getAllEnabledEmbeddingModels: builder.query<any, void>({
      query: () => ({
        url: '/v1/internal/models?model_type=embedding',
        method: 'GET',
        responseHandler: (response) =>
          response.json().then((data: { models: object[] }) => data.models),
      }),
    }),
    getDataSources: builder.query<DataSource[], void>({
      query: () => ({
        url: '/v1/data_source/',
        method: 'GET',
        providesTags: ['DataSources'],
        responseHandler: (response) =>
          response
            .json()
            .then((data: { data_sources: DataSource[] }) => data.data_sources),
      }),
    }),
    getDataIngestionRuns: builder.query<DataIngestionRun[], any>({
      query: (payload: {
        collection_name: string
        data_source_fqn: string
      }) => ({
        url: '/v1/collections/data_ingestion_runs/list',
        body: payload,
        method: 'POST',
        responseHandler: (response) =>
          response
            .json()
            .then(
              (data: { data_ingestion_runs: DataIngestionRun[] }) =>
                data.data_ingestion_runs
            ),
      }),
    }),
    getOpenapiSpecs: builder.query<any, void>({
      query: () => ({
        url: '/openapi.json',
        method: 'GET',
      }),
    }),

    // * Mutations
    uploadDataToDataDirectory: builder.mutation({
      query: (payload: { collection_name: string; filepaths: string[] }) => ({
        url: '/v1/internal/upload-to-data-directory',
        body: payload,
        method: 'POST',
      }),
    }),
    createCollection: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/collections/',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: (_result, _opts) => [{ type: 'Collections' }],
    }),
    addDocsToCollection: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/collections/associate_data_source',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['Collections'],
    }),
    unassociateDataSource: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/collections/unassociate_data_source',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['Collections'],
    }),
    deleteCollection: builder.mutation({
      query: (payload: { collectionName: string }) => ({
        url: `/v1/collections/${payload.collectionName}`,
        body: payload,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _opts) => [{ type: 'Collections' }],
    }),
    queryCollection: builder.mutation({
      query: (payload: CollectionQueryDto & { queryController: string }) => ({
        url: `/retrievers/${payload.queryController}/answer`,
        body: payload,
        method: 'POST',
      }),
    }),
    addDataSource: builder.mutation({
      query: (payload: AddDataSourcePayload) => ({
        url: '/v1/data_source/',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: (_result, _opts) => [{ type: 'DataSources' }],
    }),
    ingestDataSource: builder.mutation({
      query: (payload: {
        collection_name: string
        data_source_fqn: string
        data_ingestion_mode: string
        raise_error_on_failure: boolean
        run_as_job: boolean
      }) => ({
        url: '/v1/collections/ingest',
        body: payload,
        method: 'POST',
      }),
    }),
  }),
})

export const {
  // queries
  useGetCollectionsQuery,
  useGetCollectionStatusQuery,
  useGetAllEnabledChatModelsQuery,
  useGetAllEnabledEmbeddingModelsQuery,
  useGetDataLoadersQuery,
  useGetDataSourcesQuery,
  useGetDataIngestionRunsQuery,
  useGetOpenapiSpecsQuery,

  // mutations
  useUploadDataToDataDirectoryMutation,
  useCreateCollectionMutation,
  useAddDocsToCollectionMutation,
  useUnassociateDataSourceMutation,
  useDeleteCollectionMutation,
  useQueryCollectionMutation,
  useAddDataSourceMutation,
  useIngestDataSourceMutation,
} = qafoundryApi
