import IconProvider from '@/components/assets/IconProvider';
import { CARBON_API_KEY } from '@/stores/constants';
import { customerId } from '@/stores/qafoundry';
import axios from 'axios';
import classNames from 'classnames';
import React from 'react'
import { PreviewResource } from './types';
import { getFileInfo } from '@/utils/carbon';

type DocLinkProps = {
  pageNumber?: number;
  fqn: string;
  fileFormat?: string;
  loadPreview?: (resourse: PreviewResource) => void;
};

const DocLink = ({ pageNumber, fqn, fileFormat, loadPreview }: DocLinkProps) => {
  const splittedFqn = fqn.split('::');

  const isUrlHandlerSupport = ['carbon'].includes(splittedFqn[0].toLowerCase())
  const clickHandler = async () => {
    if (splittedFqn[0].toLowerCase() === 'carbon') {
      const fileData = await getFileInfo(customerId, splittedFqn[3]);
      fileData && loadPreview && loadPreview({
        presignedUrl: fileData.presigned_url,
        externalUrl: fileData.external_url,
        fileFormat,
        name: fileData.name
      });
    }
  }

  return (
    <a
      className={
        classNames("text-sm text-indigo-600 mt-1 flex gap-1 items-center", {
          'cursor-pointer': isUrlHandlerSupport
        })
      }
      onClick={clickHandler}
    >
      Source: {splittedFqn?.[splittedFqn.length - 1]}
      {pageNumber && `, Page No.: ${pageNumber}`}
      {isUrlHandlerSupport && <IconProvider icon="up-right-from-square" />}
    </a>
  );
}

export default DocLink
