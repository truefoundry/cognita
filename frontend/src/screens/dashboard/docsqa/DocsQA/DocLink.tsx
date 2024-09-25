import IconProvider from '@/components/assets/IconProvider';
import { customerId } from '@/stores/qafoundry';
import classNames from 'classnames';
import React from 'react'
import { PreviewResource } from './types';

type DocLinkProps = {
  pageNumber?: number;
  fqn: string;
  fileFormat?: string;
  loadPreview?: (resourse: PreviewResource) => void;
};

const LINK_RENDERING_SUPPORTED: string[] = []

const DocLink = ({ pageNumber, fqn, fileFormat, loadPreview }: DocLinkProps) => {
  const splittedFqn = fqn.split('::');

  const isUrlHandlerSupport = LINK_RENDERING_SUPPORTED.includes(splittedFqn[0].toLowerCase())
  const clickHandler = async () => {
    switch(splittedFqn[0].toLowerCase()) {
      default:
        break;
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
