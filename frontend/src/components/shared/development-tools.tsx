'use client'

import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useEffect, useState } from 'react'

export default function DevelopmentTools() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    // Delay rendering to avoid hydration mismatch if server env differs (though usually it matches for NODE_ENV)
    // and to ensure it only mounts on client
    setShow(process.env.NODE_ENV === 'development')
  }, [])

  if (!show) return null

  return (
    <ReactQueryDevtools 
      initialIsOpen={false} 
      buttonPosition="bottom-left" 
    />
  )
}
