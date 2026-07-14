import { ApiOutlined, ClockCircleOutlined, PlusOutlined, RightOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Card, Space, Tag, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'

import { getCurrentUser } from '../api/auth'
import { getHealth } from '../api/health'
import { listInterviews } from '../api/interviews'
import type { InterviewSession } from '../api/types'
import { EmptyState, PageHeader, StatusBadge } from '../components/ui'

const { Paragraph, Text, Title } = Typography

const difficultyLabels: Record<InterviewSession['difficulty'], string> = {
  junior: '初级',
  intermediate: '中级',
  senior: '高级',
}

const typeLabels: Record<InterviewSession['interview_type'], string> = {
  technical: '技术面试',
  project: '项目面试',
  comprehensive: '综合面试',
  product: '产品面试',
}

export function DashboardPage() {
  const navigate = useNavigate()
  const meQuery = useQuery({ queryKey: ['me'], queryFn: getCurrentUser })
  const healthQuery = useQuery({ queryKey: ['health'], queryFn: getHealth, retry: false })
  const interviewsQuery = useQuery({
    queryKey: ['interviews', 1, 100],
    queryFn: () => listInterviews(1, 100),
  })

  return (
    <div className="page-stack">
      <PageHeader
        title="我的面试"
        description="查看未完成会话、历史记录与报告入口，继续你的AI产品经理面试训练。"
        actions={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/interviews/new')}>
            创建面试
          </Button>
        }
      />

      <div className="dashboard-grid dashboard-grid-compact">
        <Card className="section-card">
          <Space direction="vertical" size={4}>
            <Text type="secondary">当前用户</Text>
            <Title level={4} className="compact-title">
              {meQuery.data?.username ?? '正在加载'}
            </Title>
            <Text type="secondary">{meQuery.data?.email ?? '加载用户信息中...'}</Text>
          </Space>
        </Card>
        <Card className="section-card">
          {healthQuery.isSuccess ? (
            <Alert
              showIcon
              type="success"
              icon={<ApiOutlined />}
              message="后端服务已连通"
              description={`${healthQuery.data.service} · ${healthQuery.data.status}`}
            />
          ) : (
            <Alert
              showIcon
              type="error"
              message="后端暂未连通"
              description="请确认 FastAPI 服务运行在 http://127.0.0.1:8000"
            />
          )}
        </Card>
      </div>

      <section id="records" className="session-workbench">
        <div className="section-title-row">
          <div>
            <Title level={3}>全部面试会话</Title>
            <Paragraph type="secondary">待开始、进行中、待生成报告和已完成会话都在这里统一管理。</Paragraph>
          </div>
        </div>
        {interviewsQuery.data?.items.length ? (
          <div className="session-card-grid">
            {interviewsQuery.data.items.map((item) => {
              const progress = Math.min(item.current_question_index, item.question_count)
              const actionText =
                item.status === 'COMPLETED'
                  ? '查看报告'
                  : item.status === 'READY_FOR_REPORT'
                    ? '生成报告'
                    : item.status === 'CREATED'
                      ? '开始面试'
                      : '继续面试'
              return (
                <Card key={item.id} className="session-card">
                  <Space direction="vertical" size={14} className="question-panel">
                    <Space align="start" className="session-card-head">
                      <div>
                        <Title level={4} className="compact-title">
                          {item.target_role}
                        </Title>
                        <Text type="secondary">
                          {new Date(item.updated_at || item.created_at).toLocaleString()}
                        </Text>
                      </div>
                      <StatusBadge status={item.status} />
                    </Space>
                    <div className="session-meta-grid">
                      <span>
                        <Text type="secondary">进度</Text>
                        <strong>
                          {progress}/{item.question_count}
                        </strong>
                      </span>
                      <span>
                        <Text type="secondary">类型</Text>
                        <strong>{typeLabels[item.interview_type]}</strong>
                      </span>
                      <span>
                        <Text type="secondary">难度</Text>
                        <strong>{difficultyLabels[item.difficulty]}</strong>
                      </span>
                      <span>
                        <Text type="secondary">题量</Text>
                        <strong>{item.question_count} 题</strong>
                      </span>
                    </div>
                    <Space wrap>
                      {item.knowledge_bases?.length ? (
                        item.knowledge_bases.map((knowledgeBase) => (
                          <Tag key={knowledgeBase.id} color="blue">
                            {knowledgeBase.name}
                          </Tag>
                        ))
                      ) : (
                        <Tag>未关联知识库</Tag>
                      )}
                    </Space>
                    <Button
                      block
                      type={item.status === 'COMPLETED' ? 'default' : 'primary'}
                      icon={item.status === 'COMPLETED' ? <RightOutlined /> : <ClockCircleOutlined />}
                      onClick={() => navigate(`/interviews/${item.id}`)}
                    >
                      {actionText}
                    </Button>
                  </Space>
                </Card>
              )
            })}
          </div>
        ) : (
          <Card className="section-card">
            <EmptyState
              title="还没有面试会话"
              description="创建第一场AI产品经理面试后，待开始、进行中和已完成记录都会显示在这里。"
              action={
                <Button type="primary" onClick={() => navigate('/interviews/new')}>
                  创建面试
                </Button>
              }
            />
          </Card>
        )}
      </section>
    </div>
  )
}
