import type { ReactNode } from 'react'
import { Button, Card, Empty, Space, Statistic, Tag, Typography } from 'antd'
import type { ButtonProps } from 'antd'

import type { InterviewSession } from '../api/types'

const { Paragraph, Text, Title } = Typography

type PageHeaderProps = {
  title: string
  description?: string
  actions?: ReactNode
}

export function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 48 48" role="img">
        <rect x="8" y="10" width="27" height="20" rx="6" />
        <path d="M16 30l-5 7 11-6" />
        <rect x="19" y="18" width="21" height="18" rx="5" />
        <circle cx="26" cy="27" r="2.4" />
        <circle cx="33" cy="27" r="2.4" />
        <path d="M26 19v-5m7 5v-5m-7 0h7" />
      </svg>
    </span>
  )
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <section className="page-heading">
      <div>
        <Title level={2}>{title}</Title>
        {description ? <Paragraph type="secondary">{description}</Paragraph> : null}
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </section>
  )
}

type SectionCardProps = {
  title?: ReactNode
  extra?: ReactNode
  className?: string
  children: ReactNode
}

export function SectionCard({ title, extra, className, children }: SectionCardProps) {
  return (
    <Card className={className ? `section-card ${className}` : 'section-card'} title={title} extra={extra}>
      {children}
    </Card>
  )
}

type MetricCardProps = {
  title: string
  value: ReactNode
  suffix?: ReactNode
  hint?: ReactNode
  icon?: ReactNode
}

export function MetricCard({ title, value, suffix, hint, icon }: MetricCardProps) {
  return (
    <Card className="metric-card">
      <Space align="start" className="metric-card-inner">
        {icon ? <span className="metric-icon">{icon}</span> : null}
        <div>
          <Statistic title={title} value={value as string | number} suffix={suffix} />
          {hint ? <Text type="secondary">{hint}</Text> : null}
        </div>
      </Space>
    </Card>
  )
}

const statusMeta: Record<InterviewSession['status'], { label: string; color: string }> = {
  CREATED: { label: '待开始', color: 'default' },
  IN_PROGRESS: { label: '进行中', color: 'processing' },
  READY_FOR_REPORT: { label: '待生成报告', color: 'warning' },
  COMPLETED: { label: '已完成', color: 'success' },
}

export function StatusBadge({ status }: { status: InterviewSession['status'] }) {
  const meta = statusMeta[status] ?? { label: status, color: 'default' }
  return <Tag color={meta.color}>{meta.label}</Tag>
}

type EmptyStateProps = {
  title: string
  description?: ReactNode
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Empty description={title} image={Empty.PRESENTED_IMAGE_SIMPLE}>
      {description ? <Paragraph type="secondary">{description}</Paragraph> : null}
      {action}
    </Empty>
  )
}

export function PrimaryButton(props: ButtonProps) {
  return <Button type="primary" {...props} />
}

export function SecondaryButton(props: ButtonProps) {
  return <Button {...props} />
}
