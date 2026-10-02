import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { ChevronsUpDownIcon, LogOutIcon } from 'lucide-react'
import { toast } from 'sonner'

import { Brand } from '@/components/brand'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { initials, ROLE_LABEL, useCurrentUser, useLogout, type User } from '@/lib/auth'
import { NAVIGATION } from '@/lib/navigation'

export function AppShell() {
  const { data: user } = useCurrentUser()
  // RequireRole only renders this once the user is loaded.
  if (!user) return null

  return (
    <SidebarProvider>
      <AppSidebar user={user} />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background/80 px-4 backdrop-blur">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-1 data-[orientation=vertical]:h-4" />
          <span className="text-sm text-muted-foreground">{ROLE_LABEL[user.role]} workspace</span>
        </header>
        <div className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

function AppSidebar({ user }: { user: User }) {
  const { pathname } = useLocation()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="h-14 justify-center border-b px-4 group-data-[collapsible=icon]:px-2">
        <Brand />
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAVIGATION[user.role].map((item) => (
                <SidebarMenuItem key={item.title}>
                  {item.to ? (
                    <SidebarMenuButton asChild isActive={pathname === item.to} tooltip={item.title}>
                      <NavLink to={item.to} end>
                        <item.icon aria-hidden="true" />
                        <span>{item.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  ) : (
                    <SidebarMenuButton
                      aria-disabled="true"
                      tooltip={`${item.title} · coming in Phase ${item.phase}`}
                      className="cursor-default text-muted-foreground hover:bg-transparent hover:text-muted-foreground"
                    >
                      <item.icon aria-hidden="true" />
                      <span>{item.title}</span>
                      <Badge variant="secondary" className="ml-auto text-[10px] font-normal">
                        Soon
                      </Badge>
                    </SidebarMenuButton>
                  )}
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t">
        <UserMenu user={user} />
      </SidebarFooter>
    </Sidebar>
  )
}

function UserMenu({ user }: { user: User }) {
  const navigate = useNavigate()
  const logout = useLogout()

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => navigate('/login', { replace: true }),
      onError: (error) => toast.error(error.message),
    })
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg" className="data-[state=open]:bg-sidebar-accent">
              <Avatar className="size-8 rounded-lg">
                <AvatarFallback className="rounded-lg bg-primary/10 text-xs font-medium text-primary">
                  {initials(user.name)}
                </AvatarFallback>
              </Avatar>
              <div className="grid min-w-0 flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{user.name}</span>
                <span className="truncate text-xs text-muted-foreground">{user.email}</span>
              </div>
              <ChevronsUpDownIcon className="ml-auto size-4" aria-hidden="true" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start" className="w-(--radix-dropdown-menu-trigger-width) min-w-56">
            <DropdownMenuLabel className="font-normal">
              <p className="truncate font-medium">{user.name}</p>
              <p className="truncate text-xs text-muted-foreground">{ROLE_LABEL[user.role]}</p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={handleLogout} disabled={logout.isPending}>
              <LogOutIcon aria-hidden="true" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
