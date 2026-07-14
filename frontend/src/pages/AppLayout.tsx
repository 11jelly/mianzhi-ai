import {
  DatabaseOutlined,
  FileTextOutlined,
  HomeOutlined,
  LineChartOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { Button, Typography } from 'antd'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { getCurrentUser } from '../api/auth'
import { BrandMark } from '../components/ui'
import { useAuthStore } from '../stores/auth'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

const { Text } = Typography

const navItems = [
  { label: '我的面试', path: '/dashboard', icon: <HomeOutlined /> },
  { label: '创建面试', path: '/interviews/new', icon: <PlusOutlined /> },
  { label: '成长分析', path: '/growth', icon: <LineChartOutlined /> },
  { label: '知识库', path: '/knowledge-bases', icon: <DatabaseOutlined /> },
  { label: '我的简历', path: '/resumes', icon: <FileTextOutlined /> },
]

export function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const clearToken = useAuthStore((state) => state.clearToken)
  const [collapsed, setCollapsed] = useState(false)
  const meQuery = useQuery({ queryKey: ['me'], queryFn: getCurrentUser })

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 900) {
        setCollapsed(true)
      }
    }
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className={collapsed ? 'app-shell is-collapsed' : 'app-shell'}>
      <aside className="app-sidebar">
        <Link to="/dashboard" className="brand">
          <BrandMark />
          <span className="brand-copy">
            <strong>面智AI</strong>
            <small>AI产品经理面试训练</small>
          </span>
        </Link>

        <nav className="sidebar-nav" aria-label="主导航">
          {navItems.map((item) => {
            const basePath = item.path.split('#')[0]
            const active =
              location.pathname === basePath ||
              (basePath === '/knowledge-bases' && location.pathname.startsWith('/knowledge-bases'))
            return (
              <NavLink
                key={item.label}
                to={item.path}
                className={active ? 'sidebar-link is-active' : 'sidebar-link'}
              >
                {item.icon}
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <span className="user-avatar">{meQuery.data?.username?.slice(0, 1) ?? 'U'}</span>
            <span className="user-copy">
              <Text strong>{meQuery.data?.username ?? '当前用户'}</Text>
              <Text type="secondary">{meQuery.data?.email ?? '已登录'}</Text>
            </span>
          </div>
          <Button
            block
            icon={<LogoutOutlined />}
            onClick={() => {
              clearToken()
              navigate('/login')
            }}
          >
            退出登录
          </Button>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-topbar">
          <Button
            aria-label={collapsed ? '展开侧边栏' : '收起侧边栏'}
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed((value) => !value)}
          />
          <div>
            <Text strong>面向AI产品经理岗位的智能面试训练平台</Text>
            <Text type="secondary">AI产品面试 — 文本 · 语音 · RAG · 虚拟面试官 · 成长分析</Text>
          </div>
        </header>
        <section className="app-content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}
