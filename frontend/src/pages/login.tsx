import { useNavigate } from 'react-router-dom'

import { Brand } from '@/components/brand'
import { LoginForm } from '@/components/login-form'
import { ROLE_HOME } from '@/lib/auth'

/** Staff login — admin and technician. No sign-up link: those accounts are created by an admin. */
export function LoginPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-svh flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>

        <h1 className="text-center text-xl font-semibold tracking-tight">Log in</h1>

        <LoginForm onLoggedIn={(user) => navigate(ROLE_HOME[user.role], { replace: true })} />
      </div>
    </div>
  )
}
