import { instance } from './utils'

export async function uploadArtifactFileWithSignedURI(
  uri: string,
  file: any,
  onUploadProgress?: (progressEvent: any) => void
) {
  const headers = {}
  if (uri.includes('blob.core.windows.net')) {
    headers['x-ms-blob-type'] = 'BlockBlob'
  }
  const res = await instance.put(uri, file, {
    headers,
    onUploadProgress,
  })
  return res
}
