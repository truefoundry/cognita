import React from "react"

import Switch from "@/components/base/atoms/Switch"

import Picker from "@/components/base/atoms/Picker"
import SimpleCodeEditor from "@/components/base/molecules/SimpleCodeEditor"
import { Controller, useFormContext } from "react-hook-form"
import { FormInputData } from "./FormType"
import { useGetAllEnabledChatModelsQuery } from "@/stores/qafoundry"
import { WEBPAGE_URL_REGEX } from "@/stores/constants"
import IconProvider from "@/components/assets/IconProvider"

type Props = {}

const WebDataSource: React.FC<Props> = () => {
  const { register, unregister, control, formState: { errors } } = useFormContext<FormInputData>()

  const { data: allEnabledModels } = useGetAllEnabledChatModelsQuery()

  return (
    <>
      <label className="form-control">
        <div className="label">
          <span className="label-text font-inter">Web URL * <small>(Link to the page to scrape)</small></span>
        </div>
        <input
          className="block w-full border border-gray-250 outline-none text-md p-2 rounded"
          placeholder="Link to web page"
          {...register(
            "dataSourceUri",
            {
              required: true,
              pattern: {
                value: new RegExp(WEBPAGE_URL_REGEX),
                message: "Not a valid URL"
              }
            })
          }
        />
        {errors?.dataSourceUri && (
          <div className="text-error text-xs mt-1 flex gap-1 items-center">
            <IconProvider
              icon="exclamation-triangle"
              className={'w-4 leading-5'}
            />
            <div className="font-medium">
              {errors.dataSourceUri.message}
            </div>
          </div>
        )}
      </label>
      <div className="form-control">
        <label className="label cursor-pointer">
          <span className="label-text font-inter">Use Sitemap</span>
          <Controller
            name="webConfig.use_sitemap"
            control={control}
            render={({ field }) => (
              <Switch
                {...field}
                checked={field.value}
                onChange={(e) => field.onChange(e)}
              />
            )}
          />
        </label>
      </div>

      <div className="bg-green-100 p-2 text-xs rounded">
        We will attempt to look for a sitemap at the root of the website.
        Otherwise, we will scrape the website directly.
      </div>
    </>
  )
}

export default WebDataSource
