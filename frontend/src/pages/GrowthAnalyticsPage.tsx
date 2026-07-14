import {
  LineChartOutlined,
  RadarChartOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Card,
  Empty,
  List,
  Radio,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import * as echarts from 'echarts'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { getAnalyticsHistory, getAnalyticsOverview, getAnalyticsTrend } from '../api/analytics'
import { getApiErrorMessage } from '../api/client'
import { AbilityRadarChart } from '../components/AbilityRadarChart'
import { EmptyState, MetricCard, PageHeader } from '../components/ui'
import type { AnalyticsHistoryItem, AnalyticsTrendItem } from '../types/analytics'

const { Text } = Typography

const dayOptions = [
  { label: '近 30 天', value: 30 },
  { label: '近 90 天', value: 90 },
  { label: '近 180 天', value: 180 },
  { label: '近一年', value: 365 },
]

function TrendChart({ items }: { items: AnalyticsTrendItem[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!containerRef.current || items.length === 0) {
      return undefined
    }
    const chart = echarts.init(containerRef.current)
    const labels = items.map((item) => new Date(item.report_created_at).toLocaleDateString())
    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: {
        top: 0,
        data: ['综合得分', '逻辑结构', '技术准确性', '表达清晰度', '项目深度'],
      },
      grid: { top: 56, left: 40, right: 24, bottom: 32 },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value', min: 0, max: 100 },
      series: [
        {
          name: '综合得分',
          type: 'line',
          smooth: true,
          data: items.map((item) => item.overall_score),
        },
        {
          name: '逻辑结构',
          type: 'line',
          smooth: true,
          data: items.map((item) => item.logic_score),
        },
        {
          name: '技术准确性',
          type: 'line',
          smooth: true,
          data: items.map((item) => item.technical_score),
        },
        {
          name: '表达清晰度',
          type: 'line',
          smooth: true,
          data: items.map((item) => item.expression_score),
        },
        {
          name: '项目深度',
          type: 'line',
          smooth: true,
          data: items.map((item) => item.project_depth_score),
        },
      ],
    })
    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
    }
  }, [items])

  if (items.length === 0) {
    return <Empty description="暂无匹配的趋势数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  return <div ref={containerRef} className="trend-chart" />
}

export function GrowthAnalyticsPage() {
  const [days, setDays] = useState(90)
  const [selectedTargetRole, setSelectedTargetRole] = useState<string | undefined>()
  const overviewQuery = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: getAnalyticsOverview,
  })
  const roleHistoryQuery = useQuery({
    queryKey: ['analytics-history-roles'],
    queryFn: () => getAnalyticsHistory(1, 50),
  })
  const trendQuery = useQuery({
    queryKey: ['analytics-trend', days, selectedTargetRole],
    queryFn: () => getAnalyticsTrend(days, selectedTargetRole),
  })
  const historyQuery = useQuery({
    queryKey: ['analytics-history', 1, 10, selectedTargetRole],
    queryFn: () => getAnalyticsHistory(1, 10, selectedTargetRole),
  })

  const overview = overviewQuery.data
  const latestReport = overview?.latest_report
  const hasData = Boolean(overview && overview.completed_interview_count > 0)
  const targetRoleOptions = useMemo(() => {
    const roles = new Set(
      (roleHistoryQuery.data?.items ?? []).map((item) => item.target_role).filter(Boolean),
    )
    return Array.from(roles).map((role) => ({ label: role, value: role }))
  }, [roleHistoryQuery.data?.items])

  const recommendedReviewRole = useMemo(() => {
    return historyQuery.data?.items[0]?.target_role ?? latestReport?.target_role
  }, [historyQuery.data?.items, latestReport?.target_role])

  const columns: ColumnsType<AnalyticsHistoryItem> = [
    { title: '岗位', dataIndex: 'target_role', key: 'target_role' },
    {
      title: '完成时间',
      dataIndex: 'report_created_at',
      key: 'report_created_at',
      render: (value: string) => new Date(value).toLocaleString(),
    },
    { title: '综合得分', dataIndex: 'overall_score', key: 'overall_score' },
    {
      title: '四维分数',
      key: 'dimensions',
      render: (_, record) => (
        <Space wrap>
          <Tag>逻辑 {record.logic_score}</Tag>
          <Tag>技术 {record.technical_score}</Tag>
          <Tag>表达 {record.expression_score}</Tag>
          <Tag>项目 {record.project_depth_score}</Tag>
        </Space>
      ),
    },
    {
      title: '关联知识库',
      dataIndex: 'knowledge_base_names',
      key: 'knowledge_base_names',
      render: (names: string[]) =>
        names.length ? (
          <Space wrap>
            {names.map((name) => (
              <Tag key={name} color="blue">
                {name}
              </Tag>
            ))}
          </Space>
        ) : (
          <Text type="secondary">未关联</Text>
        ),
    },
    {
      title: '报告',
      key: 'action',
      render: (_, record) => <Link to={`/interviews/${record.session_id}`}>查看报告</Link>,
    },
  ]

  if (overviewQuery.isLoading) {
    return <Skeleton active />
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="成长分析"
        description="基于当前用户已完成且已生成报告的面试记录统计，不调用额外 AI 服务。"
      />

      {overviewQuery.isError && (
        <Alert type="error" showIcon message={getApiErrorMessage(overviewQuery.error)} />
      )}

      {!hasData ? (
        <Card className="section-card">
          <EmptyState
            title="暂无可分析的完成面试记录"
            description="完成一次面试并生成综合报告后，这里会展示能力成长趋势。"
          />
        </Card>
      ) : (
        <>
          <div className="metric-grid">
            <MetricCard
              title="完成面试次数"
              value={overview?.completed_interview_count ?? 0}
              icon={<TrophyOutlined />}
            />
            <MetricCard title="平均综合得分" value={overview?.average_overall_score ?? 0} />
            <MetricCard
              title="当前最弱能力"
              value={overview?.weakest_dimension?.label ?? '暂无'}
              suffix={
                overview?.weakest_dimension
                  ? `${overview.weakest_dimension.average_score}/${overview.weakest_dimension.max_score}`
                  : undefined
              }
            />
            <MetricCard
              title="最近一次面试得分"
              value={latestReport?.overall_score ?? 0}
              hint={latestReport?.target_role}
            />
          </div>

          <Card className="section-card">
            <Space direction="vertical" size={8} style={{ width: '100%' }}>
              <Space wrap>
                <Text strong>岗位筛选</Text>
                <Select
                  allowClear
                  loading={roleHistoryQuery.isLoading}
                  placeholder="全部岗位"
                  value={selectedTargetRole}
                  style={{ minWidth: 240 }}
                  options={targetRoleOptions}
                  onChange={(value) => setSelectedTargetRole(value)}
                />
              </Space>
              <Text type="secondary">
                岗位筛选只影响成长趋势图和历史面试列表；上方概览卡片保持全局历史统计。
              </Text>
              {roleHistoryQuery.isError && (
                <Alert type="error" showIcon message={getApiErrorMessage(roleHistoryQuery.error)} />
              )}
            </Space>
          </Card>

          <div className="analytics-chart-grid">
            <Card title="最近一次能力雷达图" extra={<RadarChartOutlined />} className="section-card">
              <AbilityRadarChart report={latestReport} />
            </Card>
            <Card
              title="成长趋势"
              className="section-card"
              extra={
                <Radio.Group
                  size="small"
                  options={dayOptions}
                  value={days}
                  onChange={(event) => setDays(event.target.value)}
                  optionType="button"
                />
              }
            >
              {trendQuery.isError && (
                <Alert type="error" showIcon message={getApiErrorMessage(trendQuery.error)} />
              )}
              {trendQuery.isLoading ? (
                <Skeleton active />
              ) : (
                <TrendChart items={trendQuery.data?.items ?? []} />
              )}
            </Card>
          </div>

          <Card title="当前薄弱能力与训练建议" extra={<LineChartOutlined />} className="section-card">
            <Space direction="vertical" size={12}>
              <Text>
                当前最弱能力维度：<Text strong>{overview?.weakest_dimension?.label}</Text>
              </Text>
              {overview?.latest_improvement_plan.length ? (
                <List
                  dataSource={overview.latest_improvement_plan}
                  renderItem={(item) => (
                    <List.Item>
                      <Tag color="orange">{item.priority}</Tag>
                      <Text>{item.topic}</Text>
                    </List.Item>
                  )}
                />
              ) : (
                <Text type="secondary">最近报告暂无训练计划摘要。</Text>
              )}
              <Text type="secondary">
                推荐回看：{recommendedReviewRole ? `${recommendedReviewRole} 相关历史面试` : '最近一次面试'}
              </Text>
            </Space>
          </Card>

          <Card title="历史面试" className="section-card table-card">
            {historyQuery.isError && (
              <Alert type="error" showIcon message={getApiErrorMessage(historyQuery.error)} />
            )}
            <Table
              rowKey="session_id"
              loading={historyQuery.isLoading}
              columns={columns}
              dataSource={historyQuery.data?.items ?? []}
              pagination={false}
              locale={{
                emptyText: selectedTargetRole
                  ? '暂无匹配该岗位的完成面试记录'
                  : '暂无历史面试记录',
              }}
            />
          </Card>
        </>
      )}
    </div>
  )
}
