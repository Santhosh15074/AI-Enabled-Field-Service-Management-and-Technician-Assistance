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
    { title: 'Service requests', icon: ClipboardListIcon, phase: 2 },
    { title: 'Users', icon: UsersIcon, phase: 2 },
    { title: 'Knowledge base', icon: BookOpenIcon, phase: 4 },
    { title: 'Failure predictions', icon: ShieldAlertIcon, phase: 6 },
    { title: 'Analytics', icon: BarChart3Icon, phase: 7 },
  ],
  customer: [
    { title: 'Overview', icon: LayoutDashboardIcon, to: '/customer' },
    { title: 'New complaint', icon: MessageSquarePlusIcon, phase: 2 },
    { title: 'My requests', icon: ClipboardListIcon, phase: 2 },
    { title: 'My equipment', icon: HardDriveIcon, phase: 2 },
  ],
  technician: [
    { title: 'Overview', icon: LayoutDashboardIcon, to: '/technician' },
    { title: 'My jobs', icon: WrenchIcon, phase: 2 },
    { title: 'Service reports', icon: FileTextIcon, phase: 5 },
  ],
}
