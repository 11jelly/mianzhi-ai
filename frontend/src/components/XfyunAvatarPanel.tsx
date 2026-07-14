import { CloudOutlined, PauseCircleOutlined, SoundOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Space, Tag, Tooltip, Typography } from 'antd'

import type { XfyunAvatarController } from '../hooks/useXfyunAvatar'
import styles from './XfyunAvatarPanel.module.css'

type XfyunAvatarPanelProps = {
  avatar: XfyunAvatarController
  completed?: boolean
  questionText?: string
  embedded?: boolean
  onEnable: () => Promise<void>
  onSpeak: () => Promise<void>
  onInterrupt: () => Promise<void>
  onDisable: () => Promise<void>
}

const { Paragraph, Text } = Typography

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    disabled: '未启用',
    unconfigured: '未配置',
    ready: '可启用',
    starting: '连接中',
    running: '已连接',
    speaking: '播报中',
    error: '连接失败',
  }
  return labels[status] ?? status
}

export function XfyunAvatarPanel({
  avatar,
  completed,
  questionText,
  embedded,
  onEnable,
  onSpeak,
  onInterrupt,
  onDisable,
}: XfyunAvatarPanelProps) {
  if (completed) {
    const completedContent = (
      <Alert showIcon type="info" message="本轮面试已完成，云端数字人已停止。" />
    )
    return embedded ? (
      completedContent
    ) : (
      <Card title="云端数字人（讯飞试用）">{completedContent}</Card>
    )
  }

  const canEnable = avatar.config.enabled && avatar.configured
  const canSpeak = Boolean(questionText && avatar.isRunning)
  const enableText = avatar.status === 'error' ? '重试连接' : '启用数字人'

  const content = (
    <Space direction="vertical" size={12} className="question-panel">
      <Space wrap>
        <Tag color={avatar.isRunning ? 'green' : avatar.status === 'error' ? 'red' : 'default'}>
          {statusLabel(avatar.status)}
        </Tag>
        <Text type="secondary">SDK 3.2.3.1002 / 文本驱动</Text>
      </Space>
      <div ref={avatar.wrapperRef} className={styles.stage}>
        {!avatar.isRunning && (
          <div className={styles.placeholder}>
            <CloudOutlined />
            <Text strong>云端数字人舞台</Text>
            <Text type="secondary">
              启用后可使用讯飞数字人朗读当前题目；未启用时本地虚拟面试官继续提供状态提示。
            </Text>
          </div>
        )}
      </div>
      <div className={styles.toolbar}>
        <div className={styles.toolbarRow}>
          <Tooltip title="启用或重试连接云端讯飞数字人">
            {canEnable ? (
              <Button
                icon={<CloudOutlined />}
                loading={avatar.status === 'starting'}
                disabled={avatar.status === 'starting' || avatar.isRunning}
                title="启用或重试连接云端讯飞数字人"
                onClick={() => {
                  void onEnable()
                }}
              >
                {enableText}
              </Button>
            ) : (
              <Button icon={<CloudOutlined />} disabled title="云端数字人未配置">
                启用数字人
              </Button>
            )}
          </Tooltip>
          <Tooltip title="关闭云端数字人并释放前端资源">
            <Button
              disabled={!avatar.isRunning}
              title="关闭云端数字人"
              onClick={() => {
                void onDisable()
              }}
            >
              关闭数字人
            </Button>
          </Tooltip>
        </div>
        <div className={styles.toolbarRow}>
          <Tooltip title="让云端数字人朗读当前题目">
            <Button
              icon={<SoundOutlined />}
              disabled={!canSpeak}
              title="让云端数字人朗读当前题目"
              onClick={() => {
                void onSpeak()
              }}
            >
              朗读当前题目
            </Button>
          </Tooltip>
          <Tooltip title="中断云端数字人当前播报">
            <Button
              icon={<PauseCircleOutlined />}
              disabled={!avatar.isRunning}
              title="中断云端数字人当前播报"
              onClick={() => {
                void onInterrupt()
              }}
            >
              中断播报
            </Button>
          </Tooltip>
        </div>
      </div>
      {!avatar.config.enabled && (
        <Alert
          showIcon
          type="info"
          message="云端数字人默认关闭"
          description="如需本机课程演示，请在前端本地环境变量中配置 VITE_XFYUN_AVATAR_* 后手动启用。"
        />
      )}
      {avatar.config.enabled && !avatar.configured && (
        <Alert
          showIcon
          type="warning"
          message="云端数字人配置不完整"
          description="已保留本地虚拟面试官与浏览器朗读，不影响答题、录音、评分和报告。"
        />
      )}
      {avatar.message && <Alert showIcon type="warning" message={avatar.message} />}
      <Paragraph className={styles.hint}>
        该区域仅负责播报与画面展示，不参与 Qwen、LangGraph、RAG、ASR、评分或报告决策。
      </Paragraph>
    </Space>
  )

  return embedded ? (
    <div className={styles.embedded}>{content}</div>
  ) : (
    <Card title="云端数字人（讯飞试用）">{content}</Card>
  )
}
