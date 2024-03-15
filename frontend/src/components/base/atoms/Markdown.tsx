import React from 'react'
import ReactMarkdown from 'react-markdown'

import classNames from '@/utils/classNames'
import { InfoType } from '@/types/enums'

export type MarkdownProps = React.ComponentProps<typeof ReactMarkdown> & {
  type?: InfoType
}

const Markdown: React.FC<MarkdownProps> = ({ children, className }) => {
  const classes = classNames('markdown-body', className)
  return (
    <ReactMarkdown
      className={classes}
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
      }}
    />
  )
}

export default Markdown
