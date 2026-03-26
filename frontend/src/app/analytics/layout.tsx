"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
} from "lucide-react"

const NAV_ITEMS = [
  {
    label: "Overview",
    href: "/analytics",
    icon: LayoutDashboard,
  },
  {
    label: "Patterns",
    href: "/analytics/patterns",
    icon: TrendingUp,
  },
]

export default function AnalyticsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo/Title */}
            <div className="flex items-center gap-3">
              <BarChart3 className="h-6 w-6 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Analytics</h1>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main>{children}</main>
    </div>
  )
}
