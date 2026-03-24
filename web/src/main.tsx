import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Outlet, NavLink } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import {
  GitBranch,
  Sparkles,
  Clock,
  Folder,
  Activity,
} from 'lucide-react'
import './index.css'

// Pages
import WorkflowList from './pages/WorkflowList'
import WorkflowEditor from './pages/WorkflowEditor'
import Planner from './pages/Planner'
import AssetManager from './pages/AssetManager'
import Scheduler from './pages/Scheduler'
import ExecutionMonitor from './pages/ExecutionMonitor'

function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <a href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-accent-purple rounded-lg flex items-center justify-center">
                  <GitBranch className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-accent-purple bg-clip-text text-transparent">
                  ForgeClaw
                </span>
              </a>
            </div>

            <div className="flex items-center gap-1">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
                end
              >
                <GitBranch className="w-4 h-4" />
                Workflows
              </NavLink>
              <NavLink
                to="/planner"
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                <Sparkles className="w-4 h-4" />
                Planner
              </NavLink>
              <NavLink
                to="/executions"
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                <Activity className="w-4 h-4" />
                Executions
              </NavLink>
              <NavLink
                to="/scheduler"
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                <Clock className="w-4 h-4" />
                Scheduler
              </NavLink>
              <NavLink
                to="/assets"
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                <Folder className="w-4 h-4" />
                Assets
              </NavLink>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Toast notifications */}
      <Toaster position="top-right" />
    </div>
  )
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        path: '/',
        element: <WorkflowList />,
      },
      {
        path: '/workflows',
        element: <WorkflowList />,
      },
      {
        path: '/workflows/new',
        element: <WorkflowEditor />,
      },
      {
        path: '/workflows/:id/edit',
        element: <WorkflowEditor />,
      },
      {
        path: '/planner',
        element: <Planner />,
      },
      {
        path: '/executions',
        element: <ExecutionMonitor />,
      },
      {
        path: '/scheduler',
        element: <Scheduler />,
      },
      {
        path: '/assets',
        element: <AssetManager />,
      },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
)
