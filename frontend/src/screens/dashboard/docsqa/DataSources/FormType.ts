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
    use_sitemap: boolean
  }
}
