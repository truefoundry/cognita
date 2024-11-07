import React, { useMemo } from 'react'
import { useController, useFormContext } from 'react-hook-form'
import classNames from 'classnames'

import { FormInputData } from './FormType'
import { getUniqueFiles } from '@/utils/artifacts'
import IconProvider from '@/components/assets/IconProvider'
import { DOCS_QA_MAX_UPLOAD_SIZE_MB } from '@/stores/constants'
import { DarkTooltip } from '@/components/base/atoms/Tooltip'
import Badge from '@/components/base/atoms/Badge'
import Button from '@/components/base/atoms/Button'
import Spinner from '@/components/base/atoms/Spinner'

const parseFileSize = (size: number) => {
  const units = ['B', 'Ki', 'Mi', 'Gi']
  let i = 0
  while (size >= 1024) {
    size /= 1024
    ++i
  }
  const hasDecimal = size % 1 !== 0
  return `${hasDecimal ? size.toFixed(2) : size} ${units[i]}`
}

const calcUploadSize = (files: FormInputData['localdir']['files']) =>
  files.reduce((acc, { file }) => acc + file.size, 0) / 1024 / 1024

type Props =  {
  uploadedFileIds: string[]
}

const FileUpload: React.FC<Props> = ({ uploadedFileIds }) => {
  const { control, register, formState: {errors, isSubmitting} } = useFormContext<FormInputData>()

  const { field, fieldState } = useController({
    name: 'localdir.files',
    control,
    rules: {
      required: true,
      validate: {
        notEmpty: (files) => files.length > 0 || 'Please upload at least one file',
        maxSize: (files) =>
          calcUploadSize(files) <= DOCS_QA_MAX_UPLOAD_SIZE_MB ||
        `Total upload size cannot be more than ${DOCS_QA_MAX_UPLOAD_SIZE_MB}MB`,
      },
    },
    defaultValue: [],
  })

  const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault()
    e.stopPropagation()
    field.onChange(
      [...field.value, ...getUniqueFiles(e.dataTransfer.files)],
    )
  }

  const removeFile = (id: string) => {
    field.onChange(field.value.filter((f) => f.id !== id))
  }

  return <div>
    <div className="mb-2">
      <label className="form-control">
        <div className='label'>
          <span className="label-text font-inter">
            Source Name * <small>
              (Should only contain lowercase alphanumeric character
              with hyphen (-))
            </small>
          </span>
        </div>
        <input
          className={classNames(
            'block w-full border border-gray-250 outline-none text-md p-2 rounded',
            {
              'field-error': errors?.localdir?.name,
            }
          )}
          {...register(
            "localdir.name",
            {
              required: true,
              pattern: {
                value: /^[a-z0-9-]+$/,
                message: 'Source name should only contain lowercase alphanumeric character with hyphen!'
              }
            })
          }
          placeholder='Enter the source name'
        />
      </label>
      {errors?.localdir?.name && (
        <div className="text-error text-xs mt-1 flex gap-1 items-center">
          <IconProvider
            icon="exclamation-triangle"
            className={'w-4 leading-5'}
          />
          <div className="font-medium">
            {errors.localdir.name.message}
          </div>
        </div>
      )}
    </div>
    <label
      className='space-y-2'
      onDragOver={
        isSubmitting
          ? undefined
          : (e) => {
              e.stopPropagation()
              e.preventDefault()
            }
      }
      onDrop={isSubmitting ? undefined : handleDrop}
    >
      <span className="label-text font-inter mb-1">
        Choose files or a zip to upload
      </span>
      <div
        className={classNames(
          'flex flex-col flex-1 justify-center items-center w-full h-full bg-white p-4 rounded-lg border-1 border-gray-200 border-dashed',
          {
            'hover:bg-gray-100 cursor-pointer': !isSubmitting,
            'cursor-default': isSubmitting,
          }
        )}
      >
        <div className="text-gray-600 flex flex-col justify-center items-center p-3 gap-2">
          <IconProvider icon="cloud-arrow-up" size={2} />
          <p className="text-sm leading-5 mb-2 text-center">
            <span className="font-[500]">
              Click or Drag &amp; Drop to upload files
            </span>
            <span className="block">
              Limit {DOCS_QA_MAX_UPLOAD_SIZE_MB}MB in total
            </span>
          </p>
        </div>
        <input
          disabled={isSubmitting}
          className="hidden"
          type="file"
          multiple
          ref={field.ref}
          name={field.name}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            field.onChange(
              [
                ...field.value,
                ...getUniqueFiles(e.target.files),
              ],
            )
          }
        />
      </div>
    </label>

    {field.value.length > 0 &&  (
      <div
        className={classNames(
          'flex flex-col gap-2 p-2 bg-white border rounded-md mt-2',
          'max-h-[calc(100vh-30.625rem)]'
        )}
      >
        <span className="text-sm flex justify-between">
          Selected Files ({field.value.length}){' '}
          {fieldState.error?.message && (
            <span className="text-xs text-red-700">
              { fieldState.error.message }
            </span>
          )}
        </span>

        <ul
          className={classNames(
            'overflow-y-auto',
            'max-h-[calc(100vh-33.5rem)]'
          )}
        >
          {field.value.map(({ id, file }, idx) => (
            <li
              key={id}
              className="flex flex-row gap-2 p-2 bg-white shadow rounded-lg border mb-2 justify-between items-center"
            >
              <div className="flex items-center gap-2">
                {idx + 1}.
                <div className="flex flex-col gap-1">
                  <div className="font-inter text-sm leading-4">
                    {file.name}
                  </div>
                  <DarkTooltip title={`${file.size} bytes`}>
                    <Badge
                      text={parseFileSize(file.size)}
                      type="gray"
                      className="cursor-default"
                    />
                  </DarkTooltip>
                </div>
              </div>

              {isSubmitting ? (
                <div
                  className={classNames(
                    'w-5 h-5 rounded-full flex items-center justify-center',
                    {
                      'bg-emerald-100 text-emerald-800':
                        uploadedFileIds.includes(id),
                    }
                  )}
                >
                  {uploadedFileIds.includes(id) ? (
                    <IconProvider
                      icon={'fa-check'}
                      className="text-emerald-800"
                    />
                  ) : (
                    <Spinner small />
                  )}
                </div>
              ) : (
                <Button
                  type="button"
                  icon="trash-alt"
                  iconClasses="text-xs text-gray-400"
                  className="btn-sm bg-white hover:bg-white hover:border-gray-500"
                  onClick={() => removeFile(id)}
                  white
                />
              )}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
}

export default FileUpload
