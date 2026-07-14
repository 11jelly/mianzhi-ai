import { Card, Col, List, Progress, Row, Space, Typography } from 'antd'

import type { Evaluation } from '../api/types'

const { Paragraph, Text, Title } = Typography

type AnswerEvaluationCardProps = {
  evaluation: Evaluation
}

export function AnswerEvaluationCard({ evaluation }: AnswerEvaluationCardProps) {
  const scores = [
    { label: '逻辑结构', value: evaluation.logic_score, max: 25 },
    { label: '技术准确性', value: evaluation.technical_score, max: 30 },
    { label: '表达清晰度', value: evaluation.expression_score, max: 20 },
    { label: '项目深度', value: evaluation.project_depth_score, max: 25 },
  ]

  return (
    <Card title="AI 单题评分反馈">
      <Space direction="vertical" size={18} className="question-panel">
        <div>
          <Title level={3}>{evaluation.total_score} / 100</Title>
          <Text type="secondary">总分</Text>
        </div>
        <Row gutter={[16, 16]}>
          {scores.map((score) => (
            <Col xs={24} md={12} key={score.label}>
              <Text strong>{score.label}</Text>
              <Progress
                percent={Math.round((score.value / score.max) * 100)}
                format={() => `${score.value}/${score.max}`}
              />
            </Col>
          ))}
        </Row>
        <div>
          <Text strong>优点</Text>
          <List size="small" dataSource={evaluation.strengths} renderItem={(item) => <List.Item>{item}</List.Item>} />
        </div>
        <div>
          <Text strong>待改进点</Text>
          <List size="small" dataSource={evaluation.weaknesses} renderItem={(item) => <List.Item>{item}</List.Item>} />
        </div>
        <div>
          <Text strong>改进建议</Text>
          <Paragraph>{evaluation.improvement_suggestion}</Paragraph>
        </div>
        <div>
          <Text strong>详细反馈</Text>
          <Paragraph>{evaluation.detailed_feedback}</Paragraph>
        </div>
      </Space>
    </Card>
  )
}
