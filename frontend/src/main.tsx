import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import App from '@/App'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ApiError } from '@/lib/api'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Auth and permission errors won't fix themselves; only retry network or server errors.
      retry: (failures, error) => !(error instanceof ApiError && error.status < 500) && failures < 2,
      refetchOnWindowFocus: false,
    },
  },
})

// If the browser restores this page from its back/forward cache (e.g. Back after logout),
// reload so the app asks the server who is logged in instead of showing the old screen.
window.addEventListener('pageshow', (event) => {
  if (event.persisted) window.location.reload()
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <TooltipProvider>
          <App />
          <Toaster position="top-right" />
        </TooltipProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
