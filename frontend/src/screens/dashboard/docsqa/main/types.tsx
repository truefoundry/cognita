export interface SelectedRetrieverType {
  key: string
  name: string
  summary: string
  config: any
}

export interface DocsQAContextType {
  selectedQueryModel: string
  setSelectedQueryModel: React.Dispatch<React.SetStateAction<string>>
  selectedCollection: string
  setSelectedCollection: React.Dispatch<React.SetStateAction<string>>
  selectedQueryController: string
  setSelectedQueryController: React.Dispatch<React.SetStateAction<string>>
  selectedRetriever: SelectedRetrieverType | undefined
  setSelectedRetriever: React.Dispatch<
    React.SetStateAction<SelectedRetrieverType | undefined>
  >
  prompt: string
  setPrompt: React.Dispatch<React.SetStateAction<string>>
  isRunningPrompt: boolean
  setIsRunningPrompt: React.Dispatch<React.SetStateAction<boolean>>
  answer: string
  setAnswer: React.Dispatch<React.SetStateAction<string>>
  sourceDocs: any[]
  setSourceDocs: React.Dispatch<React.SetStateAction<any[]>>
  errorMessage: boolean
  setErrorMessage: React.Dispatch<React.SetStateAction<boolean>>
  modelConfig: string
  setModelConfig: React.Dispatch<React.SetStateAction<string>>
  retrieverConfig: string
  setRetrieverConfig: React.Dispatch<React.SetStateAction<string>>
  promptTemplate: string
  setPromptTemplate: React.Dispatch<React.SetStateAction<string>>
  isInternetSearchEnabled: boolean
  setIsInternetSearchEnabled: React.Dispatch<React.SetStateAction<boolean>>
  isCreateApplicationModalOpen: boolean
  setIsCreateApplicationModalOpen: React.Dispatch<React.SetStateAction<boolean>>
  collections: any[] | undefined
  isCollectionsLoading: boolean
  allEnabledModels: any
  allQueryControllers: string[]
  allRetrieverOptions: SelectedRetrieverType[]
  handlePromptSubmit: () => Promise<void>
  resetQA: () => void
  isCreateApplicationLoading: boolean
  createChatApplication: any
}
