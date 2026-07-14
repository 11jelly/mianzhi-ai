import { Progress, Space, Tag, Typography } from 'antd'

const { Text } = Typography

type InterviewProgressProps = {
  currentSequence: number
  questionCount: number
  category?: string
  questionType?: 'PRIMARY' | 'FOLLOW_UP'
}

export function InterviewProgress({
  currentSequence,
  questionCount,
  category,
  questionType = 'PRIMARY',
}: InterviewProgressProps) {
  const percent = Math.round((currentSequence / questionCount) * 100)

  return (
    <Space direction="vertical" size={12} className="question-panel">
      <Space wrap>
        <Text strong>
          第 {currentSequence} / {questionCount} 题
        </Text>
        {category && <Tag color="blue">{category}</Tag>}
        {questionType === 'FOLLOW_UP' && <Tag color="orange">AI 追问</Tag>}
      </Space>
      <Progress percent={percent} status="active" />
    </Space>
  )
}
