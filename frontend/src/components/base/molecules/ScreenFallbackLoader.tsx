import React from 'react'
import Spinner from '../atoms/Spinner/Spinner'
import classNames from 'classnames'

const ScreenFallbackLoader = ({ hClass = 'h-screen', wClass = 'w-screen' }) => (
  <div className={classNames('grid place-items-center', wClass, hClass)}>
    <Spinner big />
  </div>
)

export default ScreenFallbackLoader
