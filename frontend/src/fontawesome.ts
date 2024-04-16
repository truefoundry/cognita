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
  faChevronDown,
  faFile,
  faMessage,
  faPaperPlane,
  faCaretRight,
  faCircleInfo,
  faTriangleExclamation,
  faXmark,
} from '@fortawesome/free-solid-svg-icons'

const icons: any[] = [
  faCheck,
  faCircleInfo,
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
  faFile,
  faMessage,
  faTriangleExclamation,
  faDatabase,
  faSync,
  faLinkSlash,
  faClone,
  faGithub,
  faChevronDown,
  faPaperPlane,
  faCaretRight,
  faXmark,
]

library.add(...icons)
