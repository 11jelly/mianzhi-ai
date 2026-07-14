import { BranchesOutlined, StepForwardOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Space, Typography } from 'antd'

import type { AnswerSubmitResponse } from '../api/types'

const { Paragraph, Text } = Typography

type AgentFollowUpNoticeProps = {
  result: AnswerSubmitResponse
  onContinue: () => void
}

export function AgentFollowUpNotice({ result, onContinue }: AgentFollowUpNoticeProps) {
  if (!result.next_question) {
    return null
  }

  const isFollowUp = result.agent_action === 'FOLLOW_UP'
  const title = isFollowUp ? 'AI 生成了一道追问' : '可以进入下一道主问题'
  const buttonText = isFollowUp ? '回答 AI 追问' : '进入下一题'
  const icon = isFollowUp ? <BranchesOutlined /> : <StepForwardOutlined />

  return (
    <Card>
      <Space direction="vertical" size={12} className="question-panel">
        <Alert
          showIcon
          type={isFollowUp ? 'warning' : 'success'}
          message={title}
          description={
            result.agent_reason_summary || '系统已根据本题回答选择后续面试流程。'
          }
        />
        <Paragraph>
          <Text strong>{result.next_question.question_text}</Text>
        </Paragraph>
        <Button type="primary" icon={icon} onClick={onContinue}>
          {buttonText}
        </Button>
      </Space>
    </Card>
  )
}
