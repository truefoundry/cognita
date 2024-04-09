import cn, { Argument } from 'classnames'
import { twMerge } from 'tailwind-merge'

export default function classNames(...args: Argument[]) {
  return twMerge(cn(args))
}
