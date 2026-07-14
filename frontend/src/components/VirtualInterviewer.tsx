import { CheckCircleOutlined, RobotOutlined } from '@ant-design/icons'
import { Tag } from 'antd'

import avatarUrl from '../assets/ai-interviewer.svg'
import type { InterviewerState } from '../types/interviewer'
import styles from './VirtualInterviewer.module.css'

type VirtualInterviewerProps = {
  state: InterviewerState
  statusText?: string
  statusDescription?: string
  compact?: boolean
}

const stateText: Record<InterviewerState, string> = {
  IDLE: 'AI 面试官已就绪',
  SPEAKING: 'AI 面试官正在提问',
  LISTENING: 'AI 面试官正在倾听',
  THINKING: 'AI 面试官正在分析',
  COMPLETED: '本轮面试已完成',
}

const stateTag: Record<InterviewerState, string> = {
  IDLE: '待机',
  SPEAKING: '提问中',
  LISTENING: '倾听中',
  THINKING: '分析中',
  COMPLETED: '已完成',
}

const stateClass: Record<InterviewerState, string> = {
  IDLE: '',
  SPEAKING: styles.speaking,
  LISTENING: styles.listening,
  THINKING: styles.thinking,
  COMPLETED: styles.completed,
}

export function VirtualInterviewer({
  state,
  statusText,
  statusDescription,
  compact,
}: VirtualInterviewerProps) {
  const isCompleted = state === 'COMPLETED'
  const displayStatus = statusText ?? stateText[state]
  const panelClassName = `${styles.panel} ${stateClass[state]} ${
    compact ? styles.compact : ''
  }`

  return (
    <div className={panelClassName} data-state={state}>
      <div className={styles.avatarWrap} aria-hidden="true">
        <div className={styles.ring} />
        <img
          src={avatarUrl}
          className={styles.avatar}
          alt=""
          onError={(event) => {
            event.currentTarget.style.display = 'none'
          }}
        />
      </div>
      <div className={styles.content}>
        <p className={styles.title}>
          <RobotOutlined /> AI 虚拟面试官
        </p>
        <p className={styles.status}>
          {displayStatus}
          {state === 'THINKING' && (
            <span className={styles.dots} aria-hidden="true">
              <span className={styles.dot} />
              <span className={styles.dot} />
              <span className={styles.dot} />
            </span>
          )}
        </p>
        {statusDescription ? <p className={styles.description}>{statusDescription}</p> : null}
        <div className={styles.visualizer} aria-hidden="true">
          <span className={styles.bar} />
          <span className={styles.bar} />
          <span className={styles.bar} />
          <span className={styles.bar} />
        </div>
        <Tag color={isCompleted ? 'green' : 'blue'} icon={isCompleted ? <CheckCircleOutlined /> : undefined}>
          {stateTag[state]}
        </Tag>
        <p className={styles.fallback}>AI 面试官状态：{displayStatus}</p>
      </div>
    </div>
  )
}
