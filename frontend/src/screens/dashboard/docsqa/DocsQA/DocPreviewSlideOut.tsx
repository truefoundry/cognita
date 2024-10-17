import React, { useEffect, useMemo, useState } from "react"
import DocViewer from "@cyntler/react-doc-viewer";
import "@cyntler/react-doc-viewer/dist/index.css";
import "./CustomPreview.css";

import CustomDrawer from "@/components/base/atoms/CustomDrawer"
import IconProvider from "@/components/assets/IconProvider";
import type { PreviewResource } from "./types";
import { getFileFromS3 } from "@/utils/file";
import { WEB_SOURCE_NAME } from "@/stores/constants";

type Props = {
  onClose: () => void
  previewResource: PreviewResource
}

const PreviewHandler: React.FC<{ name: string, fileFormat: string, previewUrl?: string }> = ({ previewUrl, fileFormat, name }) => {
  const classes = "border-2 border-gray-300 grow w-full overflow-auto"

  if (!previewUrl) {
    return <div className={classes}>No preview available</div>
  }

  if (fileFormat === WEB_SOURCE_NAME) {
    return <iframe src={previewUrl} className={classes} />
  }

  const [document, setDocument] = useState<File | null>(null)

  useEffect(() => {
    getFileFromS3(name, previewUrl, fileFormat)
      .then(setDocument)
  }, [])

  return <>
    {
      document
        ? <DocViewer documents={[{uri: window.URL.createObjectURL(document), fileName: name}]} className={classes} />
        : <span>Loading...</span>
    }
  </>
}

const DocPreviewSlideOut: React.FC<Props> = ({ onClose, previewResource }) => {
  const toolboxButtonClasses = "btn btn-sm bg-black text-white flex gap-2";

  return (
    <CustomDrawer
      anchor={'right'}
      open={true}
      onClose={onClose}
      bodyClassName="z-2 flex flex-col gap-2 p-4"
      width="w-[65vw]"
    >
      <h2 className="text-3xl font-bold">Document Preview</h2>
      <p className="bg-yellow-100 p-2 my-4 text-xs rounded">
        The preview is may not be an accurate representation of the document. Please download the document or view it from the source.
      </p>
      <div className="flex justify-end gap-2">
        {previewResource.externalUrl &&
          <a className={toolboxButtonClasses} href={previewResource.externalUrl} target="_blank" rel="noopener">
            <IconProvider icon="up-right-from-square" className="" />
            Open source
          </a>
        }
        {previewResource.presignedUrl &&
          <a className={toolboxButtonClasses} href={previewResource.presignedUrl} target="_blank" rel="noopener">
            <IconProvider icon="download" className="" />
            Download
          </a>
        }
      </div>
      {
        previewResource.fileFormat
          ? <PreviewHandler previewUrl={previewResource.presignedUrl || previewResource.externalUrl} name={previewResource.name} fileFormat={previewResource.fileFormat} />
          : <span>
            No Preview available as file format unknown.
          </span>
      }
    </CustomDrawer>
  )
}

export default DocPreviewSlideOut
