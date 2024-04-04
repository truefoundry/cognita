import logo from '@/assets/img/logos/logo-with-text.png'
import { IconProp } from '@fortawesome/fontawesome-svg-core'
import {
  IconDefinition,
  faDatabase,
  faGear,
  faPlay,
} from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import classNames from 'classnames'
import React from 'react'
import { NavLink } from 'react-router-dom'

import IconProvider from '@/components/assets/IconProvider'
import { Link } from 'react-router-dom'
import { DarkTooltip } from '@/components/base/atoms/Tooltip'
import Button from '@/components/base/atoms/Button'

function getMenuOptions(): {
  label: string
  route: string
  icon: IconDefinition
}[] {
  return [
    {
      label: 'DocsQA',
      route: '/',
      icon: faPlay,
    },
    {
      label: 'Collections',
      route: '/collections',
      icon: faGear,
    },
    {
      label: 'Data Sources',
      route: '/data-sources',
      icon: faDatabase,
    },
  ]
}

export default function NavBar({ children }: any) {
  const menu = getMenuOptions().map((menuOption, index) => (
    <div key={index} className="align-middle mt-1 flex items-center">
      <NavLink
        to={menuOption.route}
        className={({ isActive }) =>
          classNames('pb-2 flex flex-row gap-2 items-center', {
            'cursor-default border-b-[3px] border-[#2300F7]': isActive,
            'cursor-pointer border-b-[3px] border-white': !isActive,
          })
        }
      >
        {({ isActive }) => (
          <>
            <FontAwesomeIcon
              icon={menuOption.icon}
              className={`text-[12px] ${
                isActive ? 'text-[#2300F7]' : 'text-[#82a0ce]'
              }`}
            />
            <p
              className={
                isActive
                  ? 'text-base font-semibold'
                  : 'text-base font-medium text-gray-500 hover:text-gray-900'
              }
            >
              {menuOption.label}
            </p>
          </>
        )}
      </NavLink>
    </div>
  ))

  return (
    <div className="flex flex-col border bg-white font-inter">
      <div className="flex items-center inline-block mx-5 my-4 gap-x-4 flex-wrap">
        <div className="flex gap-10 items-center">
          <Link to={'/'}>
            <img src={logo} className="h-8 w-[10.875rem]" />
          </Link>
          <div className="flex gap-5 items-center">{menu}</div>
        </div>

        <div className="flex-1" />
        <Button
          className="btn-xs text-xs h-7"
          text="View All APIs"
          onClick={() => {
            window.open(`${window.location.origin}/api/`, '_blank')
          }}
        />
        <div
          className="mt-1 mr-2 cursor-pointer flex justify-end items-center self-flex-end"
          onClick={() => {
            window.open(
              'https://github.com/truefoundry/docs-qa-playground',
              '_blank'
            )
          }}
        >
          <IconProvider icon={'fa-brands fa-github' as IconProp} size={1.25} />
        </div>
        {children}
      </div>
    </div>
  )
}
