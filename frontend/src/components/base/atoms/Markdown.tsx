import React from 'react'
import ReactMarkdown from 'react-markdown'
import type { Root } from 'mdast';
import { visit } from 'unist-util-visit';
import rehypeRaw from "rehype-raw";

import classNames from '@/utils/classNames'
import { InfoType } from '@/types/enums'
import CodeBlock from "./CodeBlock";

export type MarkdownProps = React.ComponentProps<typeof ReactMarkdown> & {
  type?: InfoType
}

const Markdown: React.FC<MarkdownProps> = ({ children, className }) => {
  const classes = classNames('markdown-body', className)
  return (
    <ReactMarkdown
      className={classes}
      remarkPlugins={[
        () => (tree: Root) => {
          visit(tree, 'code', (node) => {
            node.lang = node.lang ?? 'plaintext';
          });
        },
      ]}
      rehypePlugins={[rehypeRaw]}
      children={children}
      components={{
        li: ({
          index,
          ordered,
          className: componentClasses,
          children: componentChildren,
          ...args
        }) => (
          <li
            className={classNames(componentClasses, 'flex gap-2 items-center')}
            {...args}
          >
            {ordered ? `${index + 1}. ` : <>&bull;</>}
            <div>{componentChildren}</div>
          </li>
        ),
        a: ({ children: linkChildren, ...props }) => {
          return (
            <span
              onClick={(e) => {
                e.stopPropagation()
                window.open(props.href, '_blank')
              }}
              className="link"
            >
              {linkChildren}
            </span>
          )
        },
        code: CodeBlock,
      }}
    />
  )
}

export default Markdown
