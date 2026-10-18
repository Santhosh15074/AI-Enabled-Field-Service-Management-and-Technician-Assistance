import {
  BarChart3Icon,
  BookOpenIcon,
  ClipboardListIcon,
  FileTextIcon,
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
  /** Route of a page that exists. Items without one are shown as "Soon". */
  to?: string
  /** Build phase that adds the page. */
  phase?: number
}

export const NAVIGATION: Record<Role, NavItem[]> = {
  admin: [
    { title: 'Overview', icon: LayoutDashboardIcon, to: '/admin' },
    { title: 'Service requests', icon: ClipboardListIcon, to: '/admin/requests' },
    { title: 'Users', icon: UsersIcon, to: '/admin/users' },
    { title: 'Knowledge base', icon: BookOpenIcon, to: '/admin/knowledge-base' },
    { title: 'Failure predictions', icon: ShieldAlertIcon, to: '/admin/failure-predictions' },
    { title: 'Analytics', icon: BarChart3Icon, phase: 7 },
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
    { title: 'Service reports', icon: FileTextIcon, phase: 5 },
  ],
}
