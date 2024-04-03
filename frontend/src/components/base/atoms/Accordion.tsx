import * as React from 'react'
import MuiAccordion from '@mui/material/Accordion'
import AccordionSummary from '@mui/material/AccordionSummary'
import AccordionDetails from '@mui/material/AccordionDetails'
import IconProvider from '@/components/assets/IconProvider'

interface AccordionProps {
  summary: string
  details: string
  containerClassNames?: string
}

const Accordion = ({
  summary,
  details,
  containerClassNames,
}: AccordionProps) => {
  return (
    <div className={containerClassNames}>
      <MuiAccordion
        sx={{
          '.MuiAccordionSummary-root.Mui-expanded': {
            backgroundColor: 'rgba(0, 0, 0, 0.025)',
            minHeight: '3rem',
          },
        }}
      >
        <AccordionSummary
          expandIcon={<IconProvider icon="chevron-down" />}
          aria-controls="panel1-content"
          id="panel1-header"
          sx={{
            wordBreak: 'break-word',
            '& .MuiAccordionSummary-content': {
              marginTop: '0.5rem !important',
              marginBottom: '0.5rem !important',
              fontSize: '0.0.875rem',
            },
          }}
        >
          {summary}
        </AccordionSummary>
        <AccordionDetails
          sx={{
            wordBreak: 'break-word',
            fontSize: '0.875rem',
          }}
        >
          {details}
        </AccordionDetails>
      </MuiAccordion>
    </div>
  )
}

export default Accordion
