import { FileTextOutlined, PlayCircleOutlined, SendOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Input,
  List,
  Skeleton,
  Space,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

import { getApiErrorMessage } from '../api/client'
import {
  getCurrentQuestion,
  getInterview,
  getInterviewAgentEvents,
  getInterviewAnswers,
  getInterviewQuestions,
  startInterview,
  submitInterviewAnswer,
} from '../api/interviews'
import { generateInterviewReport, getInterviewReport } from '../api/reports'
import type { AnswerSubmitResponse, Evaluation, InterviewQuestion } from '../api/types'
import { AgentEventTimeline } from '../components/AgentEventTimeline'
import { AgentFollowUpNotice } from '../components/AgentFollowUpNotice'
import { AnswerEvaluationCard } from '../components/AnswerEvaluationCard'
import { InterviewProgress } from '../components/InterviewProgress'
import { InterviewReport } from '../components/InterviewReport'
import { SpeechSynthesisButton } from '../components/SpeechSynthesisButton'
import { VirtualInterviewer } from '../components/VirtualInterviewer'
import { VoiceAnswerRecorder } from '../components/VoiceAnswerRecorder'
import { XfyunAvatarPanel } from '../components/XfyunAvatarPanel'
import { PageHeader, StatusBadge } from '../components/ui'
import { useInterviewerState } from '../hooks/useInterviewerState'
import { useXfyunAvatar } from '../hooks/useXfyunAvatar'
import type { InterviewerState } from '../types/interviewer'

const { Paragraph, Text } = Typography
const { TextArea } = Input

type PlaybackRuntimeState = {
  completed?: boolean
  thinking?: boolean
  listening?: boolean
  currentQuestionId?: string
}

function resolvePlaybackState(runtime: PlaybackRuntimeState): InterviewerState {
  if (runtime.completed) {
    return 'COMPLETED'
  }
  if (runtime.thinking) {
    return 'THINKING'
  }
  if (runtime.listening) {
    return 'LISTENING'
  }
  return 'IDLE'
}

export function InterviewDetailPage() {
  const { sessionId } = useParams()
  const queryClient = useQueryClient()
  const [answerText, setAnswerText] = useState('')
  const [recordingDurationSeconds, setRecordingDurationSeconds] = useState<number | null>(null)
  const [latestResult, setLatestResult] = useState<AnswerSubmitResponse | null>(null)
  const [interviewerSpeaking, setInterviewerSpeaking] = useState(false)
  const [interviewerListening, setInterviewerListening] = useState(false)
  const [interviewerTranscribing, setInterviewerTranscribing] = useState(false)
  const [cloudAvatarState, setCloudAvatarState] = useState<InterviewerState>('IDLE')
  const [localCurrentQuestion, setLocalCurrentQuestion] = useState<
    InterviewQuestion | undefined
  >()
  const playbackRuntimeRef = useRef<PlaybackRuntimeState>({})
  const previousQuestionIdRef = useRef<string | undefined>(undefined)
  const getAvatarRuntimeState = useCallback(() => playbackRuntimeRef.current, [])
  const avatar = useXfyunAvatar({
    onStateChange: setCloudAvatarState,
    getRuntimeState: getAvatarRuntimeState,
  })

  const interviewQuery = useQuery({
    queryKey: ['interview', sessionId],
    queryFn: () => getInterview(sessionId ?? ''),
    enabled: Boolean(sessionId),
  })

  const interview = interviewQuery.data
  const isInProgress = interview?.status === 'IN_PROGRESS'
  const isCompleted = interview?.status === 'COMPLETED'
  const canLoadAnswers = Boolean(sessionId && interview)

  const currentQuestionQuery = useQuery({
    queryKey: ['interview-current-question', sessionId],
    queryFn: () => getCurrentQuestion(sessionId ?? ''),
    enabled: Boolean(sessionId && isInProgress),
    retry: false,
  })
  const questionsQuery = useQuery({
    queryKey: ['interview-questions', sessionId],
    queryFn: () => getInterviewQuestions(sessionId ?? ''),
    enabled: Boolean(sessionId && isInProgress),
  })
  const answersQuery = useQuery({
    queryKey: ['interview-answers', sessionId],
    queryFn: () => getInterviewAnswers(sessionId ?? ''),
    enabled: canLoadAnswers,
  })
  const agentEventsQuery = useQuery({
    queryKey: ['interview-agent-events', sessionId],
    queryFn: () => getInterviewAgentEvents(sessionId ?? ''),
    enabled: canLoadAnswers,
  })
  const reportQuery = useQuery({
    queryKey: ['interview-report', sessionId],
    queryFn: () => getInterviewReport(sessionId ?? ''),
    enabled: Boolean(sessionId && isCompleted),
    retry: false,
  })

  function invalidateInterviewQueries() {
    queryClient.invalidateQueries({ queryKey: ['interview', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['interview-current-question', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['interview-questions', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['interview-answers', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['interview-agent-events', sessionId] })
    queryClient.invalidateQueries({ queryKey: ['interview-report', sessionId] })
  }

  useEffect(() => {
    setAnswerText('')
    setRecordingDurationSeconds(null)
    setLatestResult(null)
    setInterviewerSpeaking(false)
    setInterviewerListening(false)
    setInterviewerTranscribing(false)
    setCloudAvatarState('IDLE')
    setLocalCurrentQuestion(undefined)
  }, [sessionId])

  useEffect(() => {
    if (!latestResult && currentQuestionQuery.data) {
      setLocalCurrentQuestion(currentQuestionQuery.data)
    }
  }, [currentQuestionQuery.data, latestResult])

  const startMutation = useMutation({
    mutationFn: () => startInterview(sessionId ?? ''),
    onSuccess: (data) => {
      setLocalCurrentQuestion(data.current_question)
      queryClient.setQueryData(
        ['interview-current-question', sessionId],
        data.current_question,
      )
      setLatestResult(null)
      setAnswerText('')
      setRecordingDurationSeconds(null)
      queryClient.invalidateQueries({ queryKey: ['interview-questions', sessionId] })
      invalidateInterviewQueries()
    },
  })

  const answerMutation = useMutation({
    mutationFn: ({
      questionId,
      answer,
      durationSeconds,
    }: {
      questionId: string
      answer: string
      durationSeconds: number | null
    }) =>
      submitInterviewAnswer(sessionId ?? '', {
        question_id: questionId,
        answer_text: answer,
        recording_duration_seconds: durationSeconds,
      }),
    onSuccess: (data) => {
      setLatestResult(data)
      setAnswerText(data.next_question ? data.answer.answer_text : '')
      if (data.next_question) {
        queryClient.setQueryData(
          ['interview-current-question', sessionId],
          data.next_question,
        )
      } else {
        setLocalCurrentQuestion(undefined)
        queryClient.removeQueries({ queryKey: ['interview-current-question', sessionId] })
      }
      setRecordingDurationSeconds(null)
      queryClient.setQueryData(['interview', sessionId], (old: unknown) => {
        if (!old || typeof old !== 'object') {
          return old
        }
        return {
          ...old,
          status: data.session_status,
        }
      })
      invalidateInterviewQueries()
    },
  })

  const reportMutation = useMutation({
    mutationFn: () => generateInterviewReport(sessionId ?? ''),
    onSuccess: (report) => {
      queryClient.setQueryData(['interview-report', sessionId], report)
      queryClient.setQueryData(['interview', sessionId], (old: unknown) => {
        if (!old || typeof old !== 'object') {
          return old
        }
        return { ...old, status: 'COMPLETED' }
      })
      invalidateInterviewQueries()
    },
  })

  const currentQuestion: InterviewQuestion | undefined =
    localCurrentQuestion ?? currentQuestionQuery.data
  const lastEvaluation: Evaluation | undefined = latestResult?.evaluation
  const hasPendingNextQuestion = Boolean(latestResult?.next_question)

  const getDisplaySequence = (question?: InterviewQuestion) => {
    if (!question || !interview) {
      return 0
    }
    if (question.question_type === 'FOLLOW_UP') {
      const parent = questionsQuery.data?.find((item) => item.id === question.parent_question_id)
      return (
        parent?.sequence ?? Math.min(interview.current_question_index + 1, interview.question_count)
      )
    }
    return question.sequence
  }

  const currentSequence = useMemo(() => {
    if (currentQuestion && !hasPendingNextQuestion) {
      return getDisplaySequence(currentQuestion)
    }
    if (interview?.status === 'READY_FOR_REPORT' || interview?.status === 'COMPLETED') {
      return interview.question_count
    }
    return interview?.current_question_index ?? 0
  }, [currentQuestion, hasPendingNextQuestion, interview, questionsQuery.data])

  const interviewerThinkingBase =
    startMutation.isPending ||
    answerMutation.isPending ||
    reportMutation.isPending ||
    (!currentQuestion && currentQuestionQuery.isFetching) ||
    reportQuery.isFetching ||
    interviewerTranscribing
  const interviewerThinking = interviewerThinkingBase || cloudAvatarState === 'THINKING'

  playbackRuntimeRef.current = {
    completed: interview?.status === 'COMPLETED',
    thinking: interviewerThinkingBase,
    listening: interviewerListening,
    currentQuestionId: currentQuestion?.id,
  }
  const interviewerState = useInterviewerState({
    completed: interview?.status === 'COMPLETED',
    thinking: interviewerThinking,
    listening: interviewerListening,
    speaking: interviewerSpeaking || cloudAvatarState === 'SPEAKING',
  })
  const preparingInterviewQuestions = startMutation.isPending && !currentQuestion
  const virtualInterviewerStatusText = preparingInterviewQuestions
    ? '正在准备本轮面试题'
    : undefined
  const virtualInterviewerStatusDescription = preparingInterviewQuestions
    ? '系统正在生成与岗位相关的面试问题，请稍候。'
    : undefined

  const stopQuestionPlayback = useCallback(
    async (_reason: string) => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
      setInterviewerSpeaking(false)
      setCloudAvatarState(resolvePlaybackState(playbackRuntimeRef.current))
      await avatar.interrupt()
      setCloudAvatarState(resolvePlaybackState(playbackRuntimeRef.current))
    },
    [avatar.interrupt],
  )

  const disableCloudAvatar = useCallback(async () => {
    await stopQuestionPlayback('disable-cloud-avatar')
    avatar.disable()
  }, [avatar.disable, stopQuestionPlayback])

  const destroyCloudAvatar = useCallback(async () => {
    await stopQuestionPlayback('destroy-cloud-avatar')
    await avatar.destroy()
  }, [avatar.destroy, stopQuestionPlayback])

  useEffect(() => {
    const previousQuestionId = previousQuestionIdRef.current
    const currentQuestionId = currentQuestion?.id
    if (previousQuestionId && currentQuestionId && previousQuestionId !== currentQuestionId) {
      void stopQuestionPlayback('question-changed')
    }
    previousQuestionIdRef.current = currentQuestionId
  }, [currentQuestion?.id, stopQuestionPlayback])

  useEffect(() => {
    if (interview?.status === 'COMPLETED') {
      void destroyCloudAvatar()
      setCloudAvatarState('COMPLETED')
    }
  }, [destroyCloudAvatar, interview?.status])

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
      void stopQuestionPlayback('page-unmount')
      void avatar.destroy()
    }
  }, [avatar.destroy, stopQuestionPlayback])

  if (interviewQuery.isLoading) {
    return <Skeleton active />
  }

  if (!interview) {
    return <Alert type="error" showIcon message="未找到面试会话" />
  }

  const trimmedAnswer = answerText.trim()
  const answerLocked = answerMutation.isPending || hasPendingNextQuestion
  const canSubmit =
    Boolean(currentQuestion) &&
    !hasPendingNextQuestion &&
    trimmedAnswer.length >= 20 &&
    !answerMutation.isPending
  const report = reportMutation.data ?? reportQuery.data

  const cloudAvatarPanel = (
    <XfyunAvatarPanel
      avatar={avatar}
      completed={false}
      questionText={currentQuestion?.question_text}
      onEnable={async () => {
        await avatar.enable()
      }}
      onSpeak={async () => {
        if (!currentQuestion) {
          return
        }
        await stopQuestionPlayback('before-cloud-avatar-speak')
        await avatar.speak(currentQuestion.question_text, currentQuestion.id)
      }}
      onInterrupt={() => stopQuestionPlayback('manual-interrupt')}
      onDisable={disableCloudAvatar}
    />
  )

  return (
    <div className="page-stack">
      <PageHeader
        title={interview.target_role}
        description="面试详情、作答、语音转写、虚拟面试官和综合报告生成都在这里完成。"
        actions={<StatusBadge status={interview.status} />}
      />
      <div className="interview-meta-strip">
        <span>
          <Text type="secondary">难度</Text>
          <strong>{interview.difficulty}</strong>
        </span>
        <span>
          <Text type="secondary">类型</Text>
          <strong>{interview.interview_type}</strong>
        </span>
        <span>
          <Text type="secondary">题量</Text>
          <strong>{interview.question_count} 题</strong>
        </span>
        <span>
          <Text type="secondary">进度</Text>
          <strong>
            {interview.current_question_index}/{interview.question_count}
          </strong>
        </span>
        <span className="interview-meta-wide">
          <Text type="secondary">关联知识库</Text>
          <strong>
            {interview.knowledge_bases?.length
              ? interview.knowledge_bases.map((item) => item.name).join('、')
              : '未关联'}
          </strong>
        </span>
        <span className="interview-meta-wide">
          <Text type="secondary">引用简历</Text>
          <strong>{interview.resume ? interview.resume.resume_title : '未引用'}</strong>
        </span>
      </div>

      {interview.status === 'CREATED' && (
        <div className="created-interview-workspace">
          <Card title="本地面试官与开始区域" className="section-card created-start-card">
            <VirtualInterviewer
              state={interviewerState}
              statusText={virtualInterviewerStatusText}
              statusDescription={virtualInterviewerStatusDescription}
            />
            <Alert
              showIcon
              type="info"
              message="当前会话尚未开始"
              description="点击按钮后，系统会生成本次面试题并进入作答流程。"
            />
            {startMutation.isError && (
              <Alert type="error" showIcon message={getApiErrorMessage(startMutation.error)} />
            )}
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={startMutation.isPending}
              disabled={startMutation.isPending}
              onClick={() => startMutation.mutate()}
            >
              开始文本面试
            </Button>
          </Card>
          {cloudAvatarPanel}
        </div>
      )}

      {interview.status === 'READY_FOR_REPORT' && (
        <Card className="section-card">
          <Space direction="vertical" size={16}>
            <Alert
              showIcon
              type="success"
              message="本轮问答已完成"
              description="可以生成综合诊断报告，查看总体得分、能力雷达图和训练计划。"
            />
            {reportMutation.isError && (
              <Alert type="error" showIcon message={getApiErrorMessage(reportMutation.error)} />
            )}
            {reportMutation.isPending && (
              <Alert showIcon type="info" message="正在生成综合诊断报告，请稍候。" />
            )}
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              loading={reportMutation.isPending}
              disabled={reportMutation.isPending}
              onClick={() => {
                void (async () => {
                  await stopQuestionPlayback('before-generate-report')
                  reportMutation.mutate()
                })()
              }}
            >
              生成综合诊断报告
            </Button>
          </Space>
        </Card>
      )}

      {interview.status === 'IN_PROGRESS' && (
        <>
          <div className="interview-workspace">
            <section className="interview-stage-column">
              <Card title="面试官舞台" className="section-card interviewer-stage-card">
                <XfyunAvatarPanel
                  avatar={avatar}
                  completed={false}
                  embedded
                  questionText={currentQuestion?.question_text}
                  onEnable={async () => {
                    await avatar.enable()
                  }}
                  onSpeak={async () => {
                    if (!currentQuestion) {
                      return
                    }
                    await stopQuestionPlayback('before-cloud-avatar-speak')
                    await avatar.speak(currentQuestion.question_text, currentQuestion.id)
                  }}
                  onInterrupt={() => stopQuestionPlayback('manual-interrupt')}
                  onDisable={disableCloudAvatar}
                />
                <div className="local-interviewer-strip">
                  <VirtualInterviewer
                    state={interviewerState}
                    statusText={virtualInterviewerStatusText}
                    statusDescription={virtualInterviewerStatusDescription}
                    compact
                  />
                </div>
              </Card>
            </section>

            <section className="interview-answer-column">
              <Card title="当前题目" className="section-card question-card">
                {currentQuestion ? (
                  <Space direction="vertical" size={16} className="question-panel">
                    <InterviewProgress
                      currentSequence={currentSequence}
                      questionCount={interview.question_count}
                      category={currentQuestion.category}
                      questionType={currentQuestion.question_type}
                    />
                    <Space direction="vertical" size={10} className="question-panel">
                      <Paragraph className="question-text">{currentQuestion.question_text}</Paragraph>
                      <SpeechSynthesisButton
                        text={currentQuestion.question_text}
                        onSpeakingChange={setInterviewerSpeaking}
                        beforeSpeak={() => stopQuestionPlayback('before-browser-tts')}
                        label={
                          currentQuestion.question_type === 'FOLLOW_UP'
                            ? '朗读追问'
                            : '朗读题目'
                        }
                      />
                    </Space>
                  </Space>
                ) : (
                  <Skeleton active />
                )}
              </Card>

              {currentQuestion && (
                <Card title="回答与语音输入" className="section-card answer-card">
                  <Space direction="vertical" size={14} className="question-panel">
                    <TextArea
                      rows={8}
                      maxLength={5000}
                      showCount
                      value={answerText}
                      disabled={answerLocked}
                      placeholder="请输入你的回答，至少 20 个字符。"
                      onChange={(event) => {
                        setAnswerText(event.target.value)
                        setRecordingDurationSeconds(null)
                      }}
                    />
                    {hasPendingNextQuestion && (
                      <Alert
                        showIcon
                        type="info"
                        message="本题已提交，正在准备下一题，请查看下方评分反馈。"
                      />
                    )}
                    {trimmedAnswer.length > 0 && trimmedAnswer.length < 20 && (
                      <Text type="danger">回答至少需要 20 个字符。</Text>
                    )}
                    <VoiceAnswerRecorder
                      disabled={answerLocked}
                      onTranscription={(text, durationSeconds) => {
                        setAnswerText(text)
                        setRecordingDurationSeconds(durationSeconds)
                      }}
                      onRecordingChange={setInterviewerListening}
                      onTranscribingChange={setInterviewerTranscribing}
                      beforeStartRecording={() => stopQuestionPlayback('before-recording')}
                    />
                    {answerMutation.isError && (
                      <Alert
                        type="error"
                        showIcon
                        message={getApiErrorMessage(answerMutation.error)}
                      />
                    )}
                    {answerMutation.isPending && (
                      <Alert showIcon type="info" message="AI 正在评估回答，请稍候。" />
                    )}
                    <Button
                      type="primary"
                      icon={<SendOutlined />}
                      className="answer-submit-button"
                      loading={answerMutation.isPending}
                      disabled={!canSubmit}
                      onClick={() => {
                        void (async () => {
                          await stopQuestionPlayback('before-submit-answer')
                          answerMutation.mutate({
                            questionId: currentQuestion.id,
                            answer: trimmedAnswer,
                            durationSeconds: recordingDurationSeconds,
                          })
                        })()
                      }}
                    >
                      提交并获取 AI 评分
                    </Button>
                  </Space>
                </Card>
              )}
            </section>

            <section className="interview-console-column">
              <Card title="面试控制台" className="section-card interview-console-card">
                <Tabs
                  defaultActiveKey="status"
                  className="interview-console-tabs"
                  items={[
                    {
                      key: 'status',
                      label: '会话状态',
                      children: (
                        <Space direction="vertical" size={12} className="question-panel">
                          <StatusBadge status={interview.status} />
                          <Text type="secondary">
                            主问题和追问完成后，会话会进入待生成报告状态。
                          </Text>
                          <div className="console-status-grid">
                            <span>
                              <Text type="secondary">当前进度</Text>
                              <strong>
                                {interview.current_question_index}/{interview.question_count}
                              </strong>
                            </span>
                            <span>
                              <Text type="secondary">当前题型</Text>
                              <strong>{currentQuestion?.question_type ?? '-'}</strong>
                            </span>
                          </div>
                        </Space>
                      ),
                    },
                    {
                      key: 'questions',
                      label: '题目进度',
                      children: (
                        <List
                          loading={questionsQuery.isLoading}
                          dataSource={questionsQuery.data ?? []}
                          locale={{ emptyText: '暂无题目进度' }}
                          renderItem={(item) => (
                            <List.Item>
                              <Space wrap>
                                <Text strong>第 {item.sequence} 题</Text>
                                <Tag>{item.category}</Tag>
                                {item.question_type === 'FOLLOW_UP' && (
                                  <Tag color="orange">AI 追问</Tag>
                                )}
                                {item.sequence === currentSequence && !hasPendingNextQuestion && (
                                  <Tag color="success">当前</Tag>
                                )}
                              </Space>
                            </List.Item>
                          )}
                        />
                      ),
                    },
                    {
                      key: 'agent',
                      label: 'Agent 决策',
                      children: (
                        <AgentEventTimeline
                          embedded
                          events={agentEventsQuery.data ?? []}
                          loading={agentEventsQuery.isLoading}
                        />
                      ),
                    },
                  ]}
                />
              </Card>
            </section>
          </div>

          {lastEvaluation && (
            <div className="single-question-feedback">
              <AnswerEvaluationCard evaluation={lastEvaluation} />
            </div>
          )}

          {latestResult?.next_question && (
            <AgentFollowUpNotice
              result={latestResult}
              onContinue={() => {
                void (async () => {
                  await stopQuestionPlayback('before-next-question')
                  if (latestResult.next_question) {
                    setLocalCurrentQuestion(latestResult.next_question)
                    queryClient.setQueryData(
                      ['interview-current-question', sessionId],
                      latestResult.next_question,
                    )
                  }
                  setLatestResult(null)
                  setAnswerText('')
                  setRecordingDurationSeconds(null)
                  queryClient.invalidateQueries({ queryKey: ['interview', sessionId] })
                  queryClient.invalidateQueries({ queryKey: ['interview-answers', sessionId] })
                  queryClient.invalidateQueries({
                    queryKey: ['interview-agent-events', sessionId],
                  })
                })()
              }}
            />
          )}
        </>
      )}

      {interview.status === 'COMPLETED' && (
        <>
          <Card title="虚拟面试官" className="section-card">
            <VirtualInterviewer state={interviewerState} />
          </Card>
          <XfyunAvatarPanel
            avatar={avatar}
            completed={interview.status === 'COMPLETED'}
            questionText={currentQuestion?.question_text}
            onEnable={async () => {
              await avatar.enable()
            }}
            onSpeak={async () => {
              if (!currentQuestion) {
                return
              }
              await stopQuestionPlayback('before-cloud-avatar-speak')
              await avatar.speak(currentQuestion.question_text, currentQuestion.id)
            }}
            onInterrupt={() => stopQuestionPlayback('manual-interrupt')}
            onDisable={disableCloudAvatar}
          />
          {reportQuery.isError && (
            <Alert type="error" showIcon message={getApiErrorMessage(reportQuery.error)} />
          )}
          {report ? (
            <InterviewReport report={report} answers={answersQuery.data ?? []} />
          ) : (
            <Skeleton active />
          )}
        </>
      )}
    </div>
  )
}
