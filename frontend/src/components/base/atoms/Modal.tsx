import React from 'react'
import MuiModal from '@mui/material/Modal'

export interface ModalProps extends React.ComponentProps<typeof MuiModal> {
  children: JSX.Element
}

const Modal: React.FC<ModalProps> = ({ children, ...nativeProps }) => {
  return (
    <MuiModal
      {...nativeProps}
      className="modal modal-open"
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
    >
      {children}
    </MuiModal>
  )
}

export default Modal
