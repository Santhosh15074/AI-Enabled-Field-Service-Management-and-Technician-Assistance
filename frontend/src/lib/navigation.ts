import {
  BarChart3Icon,
  BookOpenIcon,
  ClipboardListIcon,
  HardDriveIcon,
  LayoutDashboardIcon,
  MessageSquarePlusIcon,
  ShieldAlertIcon,
  UsersIcon,
  WrenchIcon,
  type LucideIcon,
} from 'lucide-react'

import type { Role } from '@/lib/auth'

export type NavItem = {
  title: string
  icon: LucideIcon
  to: string
}

export const NAVIGATION: Record<Role, NavItem[]> = {
  admin: [
    { title: 'Overview', icon: LayoutDashboardIcon, to: '/admin' },
    { title: 'Service requests', icon: ClipboardListIcon, to: '/admin/requests' },
    { title: 'Users', icon: UsersIcon, to: '/admin/users' },
    { title: 'Knowledge base', icon: BookOpenIcon, to: '/admin/knowledge-base' },
    { title: 'Failure predictions', icon: ShieldAlertIcon, to: '/admin/failure-predictions' },
    { title: 'Analytics', icon: BarChart3Icon, to: '/admin/analytics' },
  ],
  customer: [
    { title: 'Overview', icon: LayoutDashboardIcon, to: '/portal' },
    { title: 'New complaint', icon: MessageSquarePlusIcon, to: '/portal/requests/new' },
    { title: 'My requests', icon: ClipboardListIcon, to: '/portal/requests' },
    { title: 'My equipment', icon: HardDriveIcon, to: '/portal/equipment' },
  ],
  technician: [
    { title: 'Overview', icon: LayoutDashboardIcon, to: '/technician' },
    { title: 'My jobs', icon: WrenchIcon, to: '/technician/jobs' },
  ],
}
