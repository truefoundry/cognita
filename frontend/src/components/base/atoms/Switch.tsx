import React from 'react';

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(({ checked, onChange }, ref) => {
  return (
    <input
      ref={ref}
      type="checkbox"
      className="toggle toggle-primary"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
    />
  );
})

export default Switch;
