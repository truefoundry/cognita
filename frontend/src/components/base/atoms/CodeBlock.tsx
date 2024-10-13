import classNames from "classnames";
import React, { ClassAttributes, HTMLAttributes } from "react";
import { ExtraProps } from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import {okaidia} from 'react-syntax-highlighter/dist/esm/styles/prism'
import Button from "./Button";
import CopyField from "./CopyField";

export type CodeBlockProps = {
  language: string;
  value: string;
};

const CodeBlock: React.FC<ClassAttributes<HTMLElement> & HTMLAttributes<HTMLElement> & ExtraProps> = ({children, className, node, ...rest}) => {
  const match = /language-(\w+)/.exec(className || '')

  return match ? (
    <span className="relative">
      <CopyField rawValue={String(children)} className="absolute top-2 right-2" />
      <SyntaxHighlighter
        {...rest}
        PreTag="div"
        children={String(children).replace(/\n$/, '')}
        language={match[1]}
        style={okaidia}
      />
    </span>
    ) : (
      <code {...rest} className={classNames('p-1 text-sm bg-gray-800 text-white rounded-md', className)}>
        {children}
      </code>
    )
}

export default CodeBlock;
