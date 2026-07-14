import { Navigate, Outlet, RouterProvider, createBrowserRouter } from 'react-router-dom'

import { AppLayout } from './pages/AppLayout'
import { DashboardPage } from './pages/DashboardPage'
import { GrowthAnalyticsPage } from './pages/GrowthAnalyticsPage'
import { InterviewDetailPage } from './pages/InterviewDetailPage'
import { KnowledgeBaseDetailPage } from './pages/KnowledgeBaseDetailPage'
import { KnowledgeBasePage } from './pages/KnowledgeBasePage'
import { LoginPage } from './pages/LoginPage'
import { NewInterviewPage } from './pages/NewInterviewPage'
import { RegisterPage } from './pages/RegisterPage'
import { ResumePage } from './pages/ResumePage'
import { RouteErrorPage } from './pages/RouteErrorPage'
import { useAuthStore } from './stores/auth'

function ProtectedRoute() {
  const token = useAuthStore((state) => state.token)
  return token ? <Outlet /> : <Navigate to="/login" replace />
}

const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/dashboard" replace />, errorElement: <RouteErrorPage /> },
  { path: '/login', element: <LoginPage />, errorElement: <RouteErrorPage /> },
  { path: '/register', element: <RegisterPage />, errorElement: <RouteErrorPage /> },
  {
    element: <ProtectedRoute />,
    errorElement: <RouteErrorPage />,
    children: [
      {
        element: <AppLayout />,
        errorElement: <RouteErrorPage />,
        children: [
          { path: '/dashboard', element: <DashboardPage />, errorElement: <RouteErrorPage /> },
          {
            path: '/knowledge-bases',
            element: <KnowledgeBasePage />,
            errorElement: <RouteErrorPage />,
          },
          {
            path: '/knowledge-bases/:knowledgeBaseId',
            element: <KnowledgeBaseDetailPage />,
            errorElement: <RouteErrorPage />,
          },
          {
            path: '/resumes',
            element: <ResumePage />,
            errorElement: <RouteErrorPage />,
          },
          {
            path: '/growth',
            element: <GrowthAnalyticsPage />,
            errorElement: <RouteErrorPage />,
          },
          {
            path: '/interviews/new',
            element: <NewInterviewPage />,
            errorElement: <RouteErrorPage />,
          },
          {
            path: '/interviews',
            element: <Navigate to="/dashboard" replace />,
            errorElement: <RouteErrorPage />,
          },
          {
            path: '/interviews/:sessionId',
            element: <InterviewDetailPage />,
            errorElement: <RouteErrorPage />,
          },
        ],
      },
    ],
  },
  { path: '*', element: <RouteErrorPage /> },
])

function App() {
  return <RouterProvider router={router} />
}

export default App
