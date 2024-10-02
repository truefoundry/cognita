import React, { useState } from 'react'

import type {
  SourceDocs,
} from '@/stores/qafoundry'
import DocLink from './DocLink';
import DocPreviewSlideOut from './DocPreviewSlideOut';
import type { PreviewResource } from './types';

interface SourceDocsProps {
  sourceDocs: SourceDocs[];
}

const ExpandableText = ({
  text,
  maxLength,
}: {
  text: string
  maxLength: number
}) => {
  const [showAll, setShowAll] = useState(false)
  const displayText = showAll ? text : text.slice(0, maxLength)

  return (
    <p className="whitespace-pre-line inline">
      "{displayText}
      {displayText.length < text.length && !showAll && '...'}"
      {text.length > maxLength && (
        <a
          onClick={() => setShowAll((prev) => !prev)}
          className="text-blue-600 focus:outline-none ml-3 cursor-pointer"
        >
          {showAll ? 'Show less' : 'Show more'}
        </a>
      )}
    </p>
  )
}

const DocPreview: React.FC<{ doc: SourceDocs, index: number, loadPreview?: (resource: PreviewResource) => void }> = ({ doc, index, loadPreview }) => {
  const fqn = doc?.metadata?._data_point_fqn
  const pageNumber = doc?.metadata?.page_number || doc?.metadata?.page_num
  const relevanceScore = doc?.metadata?.relevance_score
  const fileFormat = doc?.metadata?.file_format
  return (
    <div className="mb-3">
      <div className="text-sm">
        {index + 1}.{' '}
        <ExpandableText
          text={doc.page_content}
          maxLength={250}
        />
      </div>
      {relevanceScore && (
        <div className="text-sm text-indigo-600 mt-1">
          Relevance Score: {relevanceScore}
        </div>
      )}
      {fqn &&
        <DocLink
          pageNumber={pageNumber}
          fqn={fqn}
          loadPreview={loadPreview}
          fileFormat={fileFormat}
        />
      }
    </div>
  )
}

const SourceDocsPreview: React.FC<SourceDocsProps> = ({ sourceDocs }: SourceDocsProps) => {
  const [previewResource, setPreviewResource] = useState<PreviewResource | null>(null)
  return (
    <div className="bg-gray-100 rounded-md w-full p-4 py-3 h-full overflow-y-auto border border-blue-500">
      <div className="font-semibold mb-3.5">
        Source Documents:
      </div>
      {
        sourceDocs?.map(
          (doc, index) => <DocPreview doc={doc} index={index} key={index} loadPreview={setPreviewResource} />)
        }
      {previewResource && <DocPreviewSlideOut onClose={() => setPreviewResource(null)} previewResource={previewResource} />}
    </div>
  );
}

export default SourceDocsPreview;
