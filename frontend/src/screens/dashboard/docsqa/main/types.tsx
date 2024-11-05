export interface SelectedRetrieverType {
  key: string
  name: string
  summary: string
  config: any
}

export interface DocsQAContextType {
  selectedQueryModel: string
  selectedCollection: string
  selectedQueryController: string
  selectedRetriever: SelectedRetrieverType | undefined
  prompt: string
  answer: string
  sourceDocs: any[]
  errorMessage: boolean
  modelConfig: string
  retrieverConfig: string
  promptTemplate: string
  isInternetSearchEnabled: boolean
  collections: any[] | undefined
  isCollectionsLoading: boolean
  allEnabledModels: any
  allQueryControllers: string[]
  allRetrieverOptions: SelectedRetrieverType[]

  setSelectedQueryModel: React.Dispatch<React.SetStateAction<string>>
  setSelectedCollection: React.Dispatch<React.SetStateAction<string>>
  setSelectedQueryController: React.Dispatch<React.SetStateAction<string>>
  setSelectedRetriever: React.Dispatch<
    React.SetStateAction<SelectedRetrieverType | undefined>
  >
  setAnswer: React.Dispatch<React.SetStateAction<string>>
  setPrompt: React.Dispatch<React.SetStateAction<string>>
  setSourceDocs: React.Dispatch<React.SetStateAction<any[]>>
  setErrorMessage: React.Dispatch<React.SetStateAction<boolean>>
  setModelConfig: React.Dispatch<React.SetStateAction<string>>
  setRetrieverConfig: React.Dispatch<React.SetStateAction<string>>
  setPromptTemplate: React.Dispatch<React.SetStateAction<string>>
  setIsInternetSearchEnabled: React.Dispatch<React.SetStateAction<boolean>>
  resetQA: () => void
}
