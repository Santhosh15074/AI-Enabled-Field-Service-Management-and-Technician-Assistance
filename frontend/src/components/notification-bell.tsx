import { useNavigate } from 'react-router-dom'
import { BellIcon, CheckCheckIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useMarkAllRead, useMarkRead, useNotifications, useUnreadCount, type Notification } from '@/lib/notifications'
import { cn } from '@/lib/utils'

function timeAgo(iso: string): string {
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'Just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function NotificationBell() {
  const navigate = useNavigate()
  const unreadCount = useUnreadCount()
  const notifications = useNotifications()
  const markRead = useMarkRead()
  const markAllRead = useMarkAllRead()

  const count = unreadCount.data?.count ?? 0

  function handleSelect(notification: Notification) {
    if (notification.status === 'unread') markRead.mutate(notification.id)
    if (notification.link) navigate(notification.link)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label={count > 0 ? `${count} unread notifications` : 'Notifications'}>
          <BellIcon aria-hidden="true" />
          {count > 0 && (
            <span className="absolute top-1 right-1 flex size-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground tabular-nums">
              {count > 9 ? '9+' : count}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between px-2 py-1.5">
          <DropdownMenuLabel className="p-0 font-medium">Notifications</DropdownMenuLabel>
          {count > 0 && (
            <Button variant="ghost" size="xs" onClick={() => markAllRead.mutate()} disabled={markAllRead.isPending}>
              <CheckCheckIcon aria-hidden="true" />
              Mark all read
            </Button>
          )}
        </div>
        <DropdownMenuSeparator />
        {notifications.isPending ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">Loading…</p>
        ) : notifications.isError ? (
          <p className="px-2 py-4 text-center text-sm text-destructive">Couldn't load notifications.</p>
        ) : notifications.data.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">You're all caught up.</p>
        ) : (
          <div className="max-h-80 overflow-y-auto">
            {notifications.data.map((notification) => (
              <DropdownMenuItem
                key={notification.id}
                className={cn('flex flex-col items-start gap-0.5 whitespace-normal', notification.status === 'unread' && 'bg-primary/5')}
                onSelect={() => handleSelect(notification)}
              >
                <p className="text-sm">{notification.message}</p>
                <p className="text-xs text-muted-foreground">{timeAgo(notification.sent_on)}</p>
              </DropdownMenuItem>
            ))}
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
