import React, { useCallback, useEffect, useRef, useState } from 'react'
import Editor from '@monaco-editor/react'
import Spinner from '../atoms/Spinner'
import classNames from 'classnames'

export interface SimpleCodeEditorProps {
  defaultValue?: string
  value?: string
  language: string
  readOnly?: boolean
  className?: string
  height?: string | number
  hideLineNumbers?: boolean
  enableExpand?: boolean
  autoLayout?: boolean
  fontSize?: number
  background?: string
  onChange?: (value?: string) => void
}

export default function SimpleCodeEditor({
  defaultValue,
  value,
  language,
  readOnly,
  className,
  height,
  hideLineNumbers,
  enableExpand,
  autoLayout,
  fontSize,
  background,
  onChange = () => {},
}: SimpleCodeEditorProps) {
  const [codeValue, setCodeValue] = useState(defaultValue)
  const linesView = useRef<Element | null>(null)
  const editorRef = useRef<any>(null)
  const wrapperView = useRef<HTMLDivElement | null>(null)

  const MIN_HEIGHT = height ?? 120
  const SOFT_MAX_HEIGHT = 300
  const [editorHeight, setEditorHeight] = useState(MIN_HEIGHT)

  const updateAutoLayout = useCallback(() => {
    if (autoLayout && editorRef.current) {
      setTimeout(
        () => setEditorHeight(editorRef.current.getContentHeight() + 24),
        0
      )
    }
  }, [autoLayout])

  useEffect(() => {
    setCodeValue(defaultValue)
  }, [defaultValue])

  useEffect(() => {
    updateAutoLayout()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  useEffect(() => {
    window.addEventListener('resize', updateAutoLayout)
    return () => window.removeEventListener('resize', updateAutoLayout)
  }, [updateAutoLayout])

  async function handleBeforeMount(monaco: any) {
    monaco.editor.defineTheme('inputTheme', {
      base: 'vs',
      inherit: true,
      rules: [{ background: background || '#f0f7ff' }],
      colors: {
        'editor.background': background || '#f0f7ff',
      },
    })
  }

  async function handleEditorMount(editor: any, monaco: any) {
    const options = {
      hover: true,
      completion: true,
      validate: true,
      format: true,
    }
    const json = monaco.languages.json
    if (json && json.jsonDefaults) {
      json.jsonDefaults.setDiagnosticsOptions(options)
    }
    const yaml = monaco.languages.yaml
    if (yaml && yaml.jsonDefaults) {
      yaml.yamlDefaults.setDiagnosticsOptions(options)
    }
    editor.getModel().updateOptions({ tabSize: 2 })

    linesView.current = document.getElementsByClassName(
      'view-lines monaco-mouse-cursor-text'
    )[0]

    editorRef.current = editor
    updateAutoLayout()
  }

  function handleResize() {
    if (enableExpand && linesView.current) {
      if (
        typeof MIN_HEIGHT === 'number' &&
        linesView.current.clientHeight > MIN_HEIGHT
      ) {
        setEditorHeight(
          linesView.current.clientHeight > SOFT_MAX_HEIGHT
            ? SOFT_MAX_HEIGHT
            : linesView.current.clientHeight
        )
      } else {
        setEditorHeight(MIN_HEIGHT)
      }
    }
  }

  useEffect(() => {
    setEditorHeight(MIN_HEIGHT)
    handleResize()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height])

  return (
    <div
      ref={wrapperView}
      className={classNames(
        'w-full relative',
        'rounded overflow-hidden border border-blue-500 py-2 bg-gray-100',
        className
      )}
      style={
        autoLayout
          ? {
              height: editorHeight,
            }
          : enableExpand
          ? {
              resize: 'vertical',
              overflow: 'auto',
              minHeight: MIN_HEIGHT,
              maxHeight: 'auto',
              height: editorHeight,
            }
          : {
              minHeight: MIN_HEIGHT,
              maxHeight: 'auto',
              height: editorHeight,
            }
      }
    >
      <Editor
        defaultLanguage={language ?? 'json'}
        defaultValue={codeValue}
        value={value}
        className="rounded"
        onChange={(e) => {
          onChange(e)
          setCodeValue(e)
          handleResize()
        }}
        onMount={handleEditorMount}
        beforeMount={handleBeforeMount}
        theme="inputTheme"
        loading={<Spinner small />}
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollbar: {
            useShadows: false,
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
            ...(autoLayout
              ? {
                  vertical: 'hidden',
                  horizontal: 'hidden',
                  handleMouseWheel: false,
                }
              : {}),
          },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          fontSize: fontSize ?? 12,
          renderLineHighlight: readOnly ? 'none' : undefined,
          ...(hideLineNumbers
            ? {
                lineNumbers: 'off',
                glyphMargin: false,
                folding: false,
                lineDecorationsWidth: 0,
                lineNumbersMinChars: 0,
              }
            : {}),
          wordWrap: autoLayout ? 'on' : 'off',
          overviewRulerLanes: autoLayout ? 0 : undefined,
        }}
      />
    </div>
  )
}

export const PreloadEditor = ({ language = 'json' }) => {
  return (
    <div className="hidden">
      <SimpleCodeEditor readOnly language={language} onChange={() => {}} />
    </div>
  )
}
