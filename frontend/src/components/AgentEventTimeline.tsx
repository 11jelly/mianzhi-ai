import { BranchesOutlined, CheckCircleOutlined, StepForwardOutlined } from '@ant-design/icons'
import { Card, Empty, Skeleton, Tag, Timeline, Typography } from 'antd'

import type { AgentEvent } from '../api/types'

const { Text } = Typography

type AgentEventTimelineProps = {
  events?: AgentEvent[]
  loading?: boolean
  embedded?: boolean
}

function eventColor(decision: AgentEvent['decision']) {
  if (decision === 'FOLLOW_UP') {
    return 'orange'
  }
  if (decision === 'READY_FOR_REPORT') {
    return 'green'
  }
  return 'blue'
}

function eventIcon(decision: AgentEvent['decision']) {
  if (decision === 'FOLLOW_UP') {
    return <BranchesOutlined />
  }
  if (decision === 'READY_FOR_REPORT') {
    return <CheckCircleOutlined />
  }
  return <StepForwardOutlined />
}

function eventLabel(decision: AgentEvent['decision']) {
  if (decision === 'FOLLOW_UP') {
    return '生成追问'
  }
  if (decision === 'READY_FOR_REPORT') {
    return '进入报告'
  }
  return '进入下一题'
}

export function AgentEventTimeline({
  events = [],
  loading,
  embedded,
}: AgentEventTimelineProps) {
  if (loading) {
    const skeleton = <Skeleton active paragraph={{ rows: 2 }} />
    return embedded ? skeleton : <Card title="AI 追问决策">{skeleton}</Card>
  }

  const content =
    events.length === 0 ? (
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 Agent 决策事件" />
    ) : (
      <Timeline
        items={events.map((event) => ({
          color: eventColor(event.decision),
          dot: eventIcon(event.decision),
          children: (
            <>
              <Tag color={eventColor(event.decision)}>{eventLabel(event.decision)}</Tag>
              {event.reason_summary && <Text>{event.reason_summary}</Text>}
            </>
          ),
        }))}
      />
    )

  return embedded ? content : <Card title="AI 追问决策">{content}</Card>
}
