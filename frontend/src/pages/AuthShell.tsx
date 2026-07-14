import { Card, Typography } from 'antd'
import type { ReactNode } from 'react'

import { BrandMark } from '../components/ui'

const { Paragraph, Title } = Typography

type AuthShellProps = {
  title: string
  subtitle: string
  children: ReactNode
}

export function AuthShell({ title, subtitle, children }: AuthShellProps) {
  return (
    <main className="auth-shell">
      <Card className="auth-card">
        <div className="auth-brand">
          <BrandMark />
          <div>
            <strong>面智AI</strong>
            <span>AI产品经理智能面试训练平台</span>
          </div>
        </div>
        <Title level={2}>{title}</Title>
        <Paragraph type="secondary">{subtitle}</Paragraph>
        {children}
      </Card>
    </main>
  )
}
