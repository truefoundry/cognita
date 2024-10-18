import IconProvider from '@/components/assets/IconProvider';
import { customerId } from '@/stores/qafoundry';
import classNames from 'classnames';
import React, { MouseEventHandler } from 'react'
import { PreviewResource } from './types';
import { WEB_SOURCE_NAME } from '@/stores/constants';

type DocLinkProps = {
  pageNumber?: number;
  fqn: string;
  fileFormat?: string;
  loadPreview?: (resourse: PreviewResource) => void;
};

const LINK_RENDERING_SUPPORTED: string[] = [WEB_SOURCE_NAME]

const DocLink = ({ pageNumber, fqn, fileFormat, loadPreview }: DocLinkProps) => {
  const splittedFqn = fqn.split('::');

  const isUrlHandlerSupport = LINK_RENDERING_SUPPORTED.includes(splittedFqn[0].toLowerCase())

  const isDirectLink = splittedFqn[0] === WEB_SOURCE_NAME

  const clickHandler: MouseEventHandler = async (e) => {
    if (isDirectLink) {
      return
    }
    e.preventDefault();
    switch(splittedFqn[0].toLowerCase()) {
      default:
        break;
    }
  }

  return (
    <a
      className={
        classNames("text-sm text-indigo-600 mt-1 flex gap-1 items-center", {
          'cursor-pointer': isUrlHandlerSupport || isDirectLink
        })
      }
      href={isDirectLink ? `https://${splittedFqn[2]}` : '#'}
      referrerPolicy='no-referrer'
      target='_blank'
      onClick={clickHandler}
    >
      Source: {splittedFqn?.[splittedFqn.length - 1]}
      {pageNumber && `, Page No.: ${pageNumber}`}
      {isUrlHandlerSupport && <IconProvider icon="up-right-from-square" />}
    </a>
  );
}

export default DocLink
