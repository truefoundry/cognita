import { library } from '@fortawesome/fontawesome-svg-core'

import { faSlack, faGithub } from '@fortawesome/free-brands-svg-icons'

import {
  faCheck,
  faClose,
  faCloudArrowUp,
  faDatabase,
  faGear,
  faInfo,
  faLinkSlash,
  faPlay,
  faPlus,
  faSpinner,
  faSync,
  faTrashAlt,
  faWarning,
  faClone,
  faChevronDown
} from '@fortawesome/free-solid-svg-icons'

import {
  faFiles,
  faMessage,
  faPaperPlaneTop,
  faCircleInfo as fasCircleInfo,
} from '@fortawesome/pro-solid-svg-icons'

import {
  faCircleInfo,
  faFiles as faFilesRegular,
  faGear as faGearRegular,
  faTriangleExclamation,
} from '@fortawesome/pro-regular-svg-icons'

const icons: any[] = [
  faCheck,
  faCircleInfo,
  fasCircleInfo,
  faClose,
  faGear,
  faInfo,
  faPlay,
  faPlus,
  faTrashAlt,
  faWarning,
  faCloudArrowUp,
  faSlack,
  faSpinner,
  faFiles,
  faPaperPlaneTop,
  faMessage,
  faFilesRegular,
  faTriangleExclamation,
  faGearRegular,
  faDatabase,
  faSync,
  faLinkSlash,
  faClone,
  faGithub,
  faChevronDown,
]

library.add(...icons)
