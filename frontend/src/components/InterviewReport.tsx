import { Alert, Card, Col, Empty, List, Progress, Row, Space, Statistic, Tabs, Tag, Typography } from 'antd'
import type { ReactNode } from 'react'

import type {
  AnswerEvidenceGroup,
  AnswerEvidenceItem,
  AnswerHistoryItem,
  EvidencePolarity,
  ExpressionMetrics,
  InterviewReport as InterviewReportType,
} from '../api/types'
import { AbilityRadarChart } from './AbilityRadarChart'

const { Paragraph, Text, Title } = Typography

const dimensionLabels: Record<string, string> = {
  logic: '逻辑结构',
  technical: '技术准确性',
  expression: '表达清晰度',
  project_depth: '项目深度',
}

const polarityColors: Record<string, string> = {
  strength: 'green',
  improvement: 'orange',
}

type InterviewReportProps = {
  report: InterviewReportType
  answers: AnswerHistoryItem[]
}

export function InterviewReport({ report }: InterviewReportProps) {
  const dimensions = [
    { label: '逻辑结构', value: report.logic_score, max: 25 },
    { label: '技术准确性', value: report.technical_score, max: 30 },
    { label: '表达清晰度', value: report.expression_score, max: 20 },
    { label: '项目深度', value: report.project_depth_score, max: 25 },
  ]
  const evidenceGroups = report.answer_evidence ?? []
  const expressionAnalysis = report.expression_analysis

  return (
    <Card className="section-card report-center">
      <Tabs
        items={[
          {
            key: 'overview',
            label: '报告总览',
            children: (
              <Space direction="vertical" size={18} className="question-panel">
                <Row gutter={[16, 16]} align="middle">
                  <Col xs={24} md={8}>
                    <Statistic title="综合得分" value={report.overall_score} suffix="/ 100" />
                  </Col>
                  <Col xs={24} md={16}>
                    <Paragraph>{report.summary}</Paragraph>
                  </Col>
                </Row>
                <div className="report-balance-grid">
                  <section className="nested-light-card">
                    <Title level={4}>优势</Title>
                    <List
                      dataSource={report.strengths}
                      renderItem={(item) => <List.Item>{item}</List.Item>}
                    />
                  </section>
                  <section className="nested-light-card">
                    <Title level={4}>待提升能力</Title>
                    <List
                      dataSource={report.weaknesses}
                      renderItem={(item) => <List.Item>{item}</List.Item>}
                    />
                  </section>
                </div>
                <section className="nested-light-card">
                  <Title level={4}>岗位能力差距分析</Title>
                  <Paragraph>{report.role_gap_analysis}</Paragraph>
                </section>
              </Space>
            ),
          },
          {
            key: 'radar',
            label: '能力雷达',
            children: (
              <Row gutter={[16, 16]} align="middle">
                <Col xs={24} lg={12}>
                  <AbilityRadarChart report={report} />
                </Col>
                <Col xs={24} lg={12}>
                  <Space direction="vertical" size={12} className="question-panel">
                    {dimensions.map((item) => (
                      <div key={item.label}>
                        <Text strong>{item.label}</Text>
                        <Progress
                          percent={Math.round((item.value / item.max) * 100)}
                          format={() => `${item.value}/${item.max}`}
                        />
                      </div>
                    ))}
                  </Space>
                </Col>
              </Row>
            ),
          },
          {
            key: 'evidence',
            label: '回答证据',
            children: (
              <Space direction="vertical" size={16} className="question-panel">
                {evidenceGroups.length === 0 ? (
                  <Empty description="该历史会话未生成回答证据与表达质量分析。" />
                ) : (
                  <List
                    dataSource={evidenceGroups}
                    renderItem={(item) => (
                      <List.Item>
                        <EvidenceGroupCard group={item} />
                      </List.Item>
                    )}
                  />
                )}
              </Space>
            ),
          },
          {
            key: 'expression',
            label: '表达质量',
            children: (
              <Space direction="vertical" size={16} className="question-panel">
                <Alert
                  showIcon
                  type="info"
                  message="表达质量为辅助诊断"
                  description="指标仅基于回答文本与可用录音时长估算，不代表情绪、口音、声纹、人格或真实语音质量。"
                />
                {expressionAnalysis?.summary ? (
                  <>
                    <Row gutter={[16, 16]}>
                      <Col xs={12} lg={6}>
                        <Statistic
                          title="平均回答长度"
                          value={formatMetric(expressionAnalysis.summary.average_answer_length)}
                        />
                      </Col>
                      <Col xs={12} lg={6}>
                        <Statistic
                          title="平均句长"
                          value={formatMetric(expressionAnalysis.summary.average_sentence_length)}
                        />
                      </Col>
                      <Col xs={12} lg={6}>
                        <Statistic
                          title="填充词总数"
                          value={formatMetric(expressionAnalysis.summary.total_filler_word_count)}
                        />
                      </Col>
                      <Col xs={12} lg={6}>
                        <Statistic
                          title="结构信号总数"
                          value={formatMetric(
                            expressionAnalysis.summary.total_structure_signal_count,
                          )}
                        />
                      </Col>
                    </Row>
                    <Card className="nested-light-card" size="small">
                      <Space direction="vertical" size={6}>
                        <Text strong>
                          估算语速：
                          {expressionAnalysis.summary.average_estimated_speech_rate
                            ? `${expressionAnalysis.summary.average_estimated_speech_rate} ${
                                expressionAnalysis.summary.speech_rate_unit ?? ''
                              }`
                            : '样本不足'}
                        </Text>
                        <Text type="secondary">
                          仅基于转写文本与录音时长估算；无有效录音时长的回答不参与语速汇总。
                        </Text>
                      </Space>
                    </Card>
                    <List
                      dataSource={expressionAnalysis.answers}
                      renderItem={(item) => (
                        <List.Item>
                          <ExpressionMetricsCard
                            sequence={item.sequence}
                            metrics={item.metrics}
                          />
                        </List.Item>
                      )}
                    />
                  </>
                ) : (
                  <Empty description="该历史会话未生成表达质量分析。" />
                )}
              </Space>
            ),
          },
          {
            key: 'plan',
            label: '训练建议',
            children: (
              <Space direction="vertical" size={18} className="question-panel">
                <section className="nested-light-card">
                  <Title level={4}>优先级训练计划</Title>
                  <List
                    dataSource={report.improvement_plan}
                    renderItem={(item) => (
                      <List.Item>
                        <Space direction="vertical" size={8} className="question-panel">
                          <Space wrap>
                            <Tag color="blue">P{item.priority}</Tag>
                            <Title level={5} className="compact-title">
                              {item.topic}
                            </Title>
                          </Space>
                          <Text type="secondary">{item.reason}</Text>
                          <List
                            size="small"
                            dataSource={item.actions}
                            renderItem={(action) => <List.Item>{action}</List.Item>}
                          />
                          <Text strong>预期结果：{item.expected_outcome}</Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                </section>
                <section className="nested-light-card">
                  <Title level={4}>推荐练习问题</Title>
                  <List
                    dataSource={report.next_practice_questions}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                </section>
              </Space>
            ),
          },
          {
            key: 'full',
            label: '完整报告',
            children: (
              <div className="report-scroll">
                <Space direction="vertical" size={18} className="question-panel">
                  <Title level={4}>综合评价</Title>
                  <Paragraph>{report.summary}</Paragraph>
                  <Title level={4}>岗位能力差距分析</Title>
                  <Paragraph>{report.role_gap_analysis}</Paragraph>
                  <Title level={4}>优势</Title>
                  <List
                    dataSource={report.strengths}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                  <Title level={4}>待提升能力</Title>
                  <List
                    dataSource={report.weaknesses}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                </Space>
              </div>
            ),
          },
        ]}
      />
    </Card>
  )
}

function EvidenceGroupCard({ group }: { group: AnswerEvidenceGroup }) {
  const strengths = group.evidence_items.filter((item) => item.polarity === 'strength')
  const improvements = group.evidence_items.filter((item) => item.polarity === 'improvement')

  return (
    <Space direction="vertical" size={12} className="question-panel evidence-group-card">
      <Space wrap>
        <Text strong>第 {group.sequence} 题</Text>
        <Tag>{group.category}</Tag>
        {group.question_type === 'FOLLOW_UP' && <Tag color="orange">AI 追问</Tag>}
      </Space>
      <Text>{group.question_text}</Text>
      <Paragraph className="answer-evidence-text">
        {renderHighlightedAnswer(group.answer_text, group.evidence_items)}
      </Paragraph>
      <EvidenceList title="优势证据" items={strengths} emptyText="暂无可靠优势证据" />
      <EvidenceList title="待改进证据" items={improvements} emptyText="暂无可靠改进证据" />
    </Space>
  )
}

function EvidenceList({
  title,
  items,
  emptyText,
}: {
  title: string
  items: AnswerEvidenceItem[]
  emptyText: string
}) {
  return (
    <section className="nested-light-card evidence-list-card">
      <Title level={5}>{title}</Title>
      {items.length === 0 ? (
        <Text type="secondary">{emptyText}</Text>
      ) : (
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => (
            <List.Item>
              <Space direction="vertical" size={4} className="question-panel">
                <Space wrap>
                  <Tag color={polarityColors[item.polarity]}>{dimensionLabels[item.dimension]}</Tag>
                  <Text code>{item.quote}</Text>
                </Space>
                <Text>{item.reason}</Text>
                {item.suggestion && <Text type="secondary">建议：{item.suggestion}</Text>}
              </Space>
            </List.Item>
          )}
        />
      )}
    </section>
  )
}

function ExpressionMetricsCard({
  sequence,
  metrics,
}: {
  sequence: number
  metrics: ExpressionMetrics | null
}) {
  if (!metrics) {
    return <Empty description={`第 ${sequence} 题暂无表达质量指标`} />
  }
  return (
    <section className="nested-light-card expression-metrics-card">
      <Space direction="vertical" size={10} className="question-panel">
        <Text strong>第 {sequence} 题</Text>
        <Space wrap>
          <Tag>长度 {metrics.character_count}</Tag>
          <Tag>句子 {metrics.sentence_count}</Tag>
          <Tag>平均句长 {formatMetric(metrics.average_sentence_length)}</Tag>
          <Tag>填充词 {metrics.filler_word_count}</Tag>
          <Tag>结构信号 {metrics.structure_signal_count}</Tag>
          <Tag color={metrics.speech_rate_status === '不可用' ? 'default' : 'blue'}>
            语速 {metrics.speech_rate_status}
          </Tag>
        </Space>
        {metrics.repetition_hint && <Text type="secondary">{metrics.repetition_hint}</Text>}
        <Text type="secondary">{metrics.speech_rate_note}</Text>
      </Space>
    </section>
  )
}

function renderHighlightedAnswer(text: string, evidenceItems: AnswerEvidenceItem[]): ReactNode[] {
  const ranges: { start: number; end: number; polarity: EvidencePolarity }[] = []
  evidenceItems.forEach((item) => {
    const start = text.indexOf(item.quote)
    if (start >= 0) {
      ranges.push({
        start,
        end: start + item.quote.length,
        polarity: item.polarity,
      })
    }
  })
  ranges.sort((left, right) => left.start - right.start)

  const nodes: ReactNode[] = []
  let cursor = 0
  ranges.forEach((range, index) => {
    if (range.start < cursor) {
      return
    }
    if (range.start > cursor) {
      nodes.push(text.slice(cursor, range.start))
    }
    nodes.push(
      <mark key={`${range.start}-${index}`} className={`evidence-highlight ${range.polarity}`}>
        {text.slice(range.start, range.end)}
      </mark>,
    )
    cursor = range.end
  })
  if (cursor < text.length) {
    nodes.push(text.slice(cursor))
  }
  return nodes.length ? nodes : [text]
}

function formatMetric(value: number | null | undefined) {
  return value === null || value === undefined ? '样本不足' : value
}
