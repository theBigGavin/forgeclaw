import { NavLink } from 'react-router-dom'
import {
  Home,
  GitBranch,
  Play,
  Brain,
  Database,
  FileBox,
  Settings,
  Sparkles,
} from 'lucide-react'

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/planner', icon: Sparkles, label: 'AI Planner' },
  { path: '/workflows', icon: GitBranch, label: 'Workflows' },
  { path: '/executions', icon: Play, label: 'Executions' },
  { path: '/memory', icon: Database, label: 'Memory' },
  { path: '/assets', icon: FileBox, label: 'Assets' },
]

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200">
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">ForgeClaw</h1>
            <p className="text-xs text-gray-500">AI Orchestration</p>
          </div>
        </div>
      </div>

      <nav className="px-4 pb-6">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
        <button className="flex items-center gap-3 px-4 py-3 w-full rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
          <Settings className="w-5 h-5" />
          Settings
        </button>
      </div>
    </aside>
  )
}
