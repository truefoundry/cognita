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
  const [showBeforeScript, setShowBeforeScript] = React.useState(false)
  const [showWaitScript, setShowWaitScript] = React.useState(false)
  const [showAIModel, setShowAIModel] = React.useState(false)
  const [showCssSelector, setShowCssSelector] = React.useState(false)

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
      <div className="bg-green-100 p-2 text-xs rounded">
        We will attempt to look for a sitemap at the root of the website.
        Otherwise, we will scrape the website directly.
      </div>
      <div className="m-2 p-4 border-1 space-y-4">
        <label className="flex items-center space-x-2">
          <Switch
            checked={showBeforeScript}
            onChange={(checked) => {
              unregister("webConfig.parserConfigs")
              setShowBeforeScript(checked)
            }}
          />
          <span>Execute JS code before</span>
        </label>
        {showBeforeScript &&
          <label className="block label">
            <span className="label-text font-inter">Pre scrape script *</span>
            <Controller
              name="webConfig.parserConfigs"
              control={control}
              rules={{ required: true }}
              render={({ field }) => (
                <SimpleCodeEditor
                  language="javascript"
                  height={200}
                  value={field.value}
                  onChange={(v) => field.onChange(v ?? "")}
                />
              )}
            />
          </label>
        }
      </div>
      <div className="m-2 p-4 border-1">
        <label className="flex items-center space-x-2">
          <Switch
            checked={showWaitScript}
            onChange={() => {
              unregister("webConfig.waitConfigs")
              setShowWaitScript(!showWaitScript)
            }}
          />
          <span>Execute JS code to wait for</span>
        </label>
        {showWaitScript &&
          <label className="block label">
            <span className="label-text font-inter">Wait Script * :</span>
            <Controller
              name="webConfig.waitConfigs"
              control={control}
              render={({ field }) => (
                <SimpleCodeEditor
                  language="javascript"
                  height={200}
                  value={field.value}
                  onChange={(v) => field.onChange(v ?? "")}
                />
              )}
            />
          </label>
        }
      </div>
      <div className="m-2 p-4 border-1">
        <label className="flex items-center space-x-2">
          <Switch
            checked={showCssSelector}
            onChange={() => {
              unregister("webConfig.waitConfigs")
              setShowCssSelector(!showCssSelector)
            }}
          />
          <span>CSS selector for main content</span>
        </label>
        {showCssSelector &&
          <label className="block label">
            <span className="label-text font-inter">Wait Script *</span>
            <input
              className="block w-full border border-gray-250 outline-none text-md p-2 rounded"
              placeholder="Enter CSS selector (document.querySelectorAll)"
              {...register("webConfig.cssSelector", { required: true })}
            />
          </label>
        }
      </div>
      <div className="m-2 p-4 border-1">
        <label className="flex items-center space-x-2">
          <Switch
            checked={showAIModel}
            onChange={() => {
              unregister("webConfig.aiModel")
              setShowAIModel(!showAIModel)
            }}
          />
          <span>AI Model and Prompt</span>
        </label>
        {showAIModel && (
          <div className="ai-model-prompt space-y-4 mt-2">
            <label className="label flex gap-2">
              <span className="label-text">Select AI Model *</span>
              {allEnabledModels &&
                <Controller
                  name="webConfig.aiModel.model_id"
                  control={control}
                  rules={{ required: true }}
                  defaultValue={allEnabledModels[0].name}
                  render={({ field }) => (
                    <Picker
                      className="flex-grow"
                      options={allEnabledModels.map((model: { name: string }) => model.name)}
                      {...field}
                    />
                  )}
                />
              }
            </label>
            <div className="form-group">
              <label htmlFor="aiPrompt" className="block text-sm font-medium text-gray-700">AI Prompt *</label>
              <input
                className="block w-full border border-gray-250 outline-none text-md p-2 rounded"
                placeholder="Enter extraction insturctions"
                {...register("webConfig.aiModel.prompt", { required: true })}
              />
            </div>
          </div>
        )}
      </div>
    </>
  )
}

export default WebDataSource
