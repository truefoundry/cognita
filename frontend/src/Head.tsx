import React from 'react'
import { Helmet } from 'react-helmet-async'
import { GTAG_ID } from './stores/constants'

const Head = () => (
  <Helmet>
    <script
      async
      src={`https://www.googletagmanager.com/gtag/js?id=${GTAG_ID}`}
    ></script>
    <script>
      {`
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '${GTAG_ID}');
      `}
    </script>
  </Helmet>
)

export default Head
