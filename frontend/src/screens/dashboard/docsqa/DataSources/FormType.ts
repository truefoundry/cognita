export type FormInputData = {
  dataSourceType: string
  localdir: {
    name: string
    files: {
      id: string
      file: File
    }[]
    uploadedFileIds: string[]
  }
  dataSourceUri: string
  webConfig: {
    parserConfigs?: string
    waitConfigs?: string
    cssSelector?: string
    aiModel?: {
      model_id: string
      prompt: string
    }
  }
}
