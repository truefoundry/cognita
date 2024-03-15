import { uniqueId } from 'lodash'

export const getUniqueFiles = (files: FileList | null) =>
  Array.from<File>(files ?? []).map((file) => ({
    id: uniqueId('file-'),
    file,
    progress: 0,
  }))

export const getFilePath = (f) => `files/${f.name}`
