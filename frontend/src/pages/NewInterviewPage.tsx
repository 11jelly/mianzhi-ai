import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Card, Form, Input, Radio, Select, Space, Switch, Typography } from 'antd'
import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { getApiErrorMessage } from '../api/client'
import { createInterview } from '../api/interviews'
import { listKnowledgeBases } from '../api/knowledgeBases'
import { listResumes } from '../api/resumes'
import type { InterviewCreateRequest } from '../api/types'
import { PageHeader } from '../components/ui'

const { Text, Title } = Typography

export function NewInterviewPage() {
  const [form] = Form.useForm<InterviewCreateRequest>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: createInterview,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['interviews'] })
      navigate(`/interviews/${data.id}`)
    },
  })
  const knowledgeBasesQuery = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: listKnowledgeBases,
  })
  const resumesQuery = useQuery({
    queryKey: ['resumes'],
    queryFn: listResumes,
  })
  const availableKnowledgeBases =
    knowledgeBasesQuery.data?.filter(
      (item) => item.status === 'READY' || item.chunk_count > 0,
    ) ?? []
  const activeResume = resumesQuery.data?.find(
    (item) => item.is_active && item.status === 'READY',
  )

  useEffect(() => {
    if (!resumesQuery.isFetched) {
      return
    }
    form.setFieldValue('use_active_resume', Boolean(activeResume))
  }, [activeResume, form, resumesQuery.isFetched])

  return (
    <div className="page-stack">
      <PageHeader
        title="创建面试"
        description="设置岗位、题量、难度和知识库关联，创建后进入面试详情页继续开始训练。"
      />
      <Card className="section-card form-workspace">
        <Form<InterviewCreateRequest>
          form={form}
          layout="vertical"
          initialValues={{
            difficulty: 'intermediate',
            interview_type: 'technical',
            question_count: 5,
            knowledge_base_ids: [],
            use_active_resume: true,
          }}
          onFinish={(values) =>
            mutation.mutate({
              ...values,
              knowledge_base_ids: values.knowledge_base_ids ?? [],
              use_active_resume: Boolean(activeResume && values.use_active_resume),
            })
          }
        >
          {mutation.isError && (
            <Alert type="error" showIcon message={getApiErrorMessage(mutation.error)} />
          )}
          <div className="interview-form-grid">
            <section className="form-section form-section-compact">
              <Title level={4}>基本设置</Title>
              <Form.Item
                name="target_role"
                label="目标岗位"
                rules={[{ required: true, message: '请输入目标岗位' }]}
              >
                <Input placeholder="AI产品经理" />
              </Form.Item>
            </section>

            <section className="form-section form-section-compact">
              <Title level={4}>岗位与面试类型</Title>
              <Form.Item name="interview_type" label="面试类型" rules={[{ required: true }]}>
                <Select
                  options={[
                    { value: 'technical', label: '技术面试' },
                    { value: 'project', label: '项目面试' },
                    { value: 'comprehensive', label: '综合面试' },
                    { value: 'product', label: '产品面试' },
                  ]}
                />
              </Form.Item>
            </section>

            <section className="form-section form-section-compact">
              <Title level={4}>难度</Title>
              <Form.Item name="difficulty" label="难度" rules={[{ required: true }]}>
                <Select
                  options={[
                    { value: 'junior', label: '初级' },
                    { value: 'intermediate', label: '中级' },
                    { value: 'senior', label: '高级' },
                  ]}
                />
              </Form.Item>
            </section>

            <section className="form-section form-section-compact">
              <Title level={4}>题目数量</Title>
              <Form.Item name="question_count" label="题目数量" rules={[{ required: true }]}>
                <Radio.Group
                  options={[
                    { value: 3, label: '3 题' },
                    { value: 5, label: '5 题' },
                    { value: 8, label: '8 题' },
                  ]}
                  optionType="button"
                  buttonStyle="solid"
                />
              </Form.Item>
            </section>

            <section className="form-section form-section-wide">
              <Title level={4}>知识库关联</Title>
              <Form.Item
                name="knowledge_base_ids"
                label="关联岗位知识库（可选）"
                extra={
                  <Space direction="vertical" size={2}>
                    {knowledgeBasesQuery.isError && (
                      <Text type="danger">{getApiErrorMessage(knowledgeBasesQuery.error)}</Text>
                    )}
                    {!knowledgeBasesQuery.isLoading && availableKnowledgeBases.length === 0 && (
                      <Text type="secondary">
                        暂无可用知识库，可先前往 <Link to="/knowledge-bases">知识库页面</Link> 上传资料
                      </Text>
                    )}
                  </Space>
                }
              >
                <Select
                  mode="multiple"
                  allowClear
                  loading={knowledgeBasesQuery.isLoading}
                  disabled={knowledgeBasesQuery.isLoading || availableKnowledgeBases.length === 0}
                  placeholder="选择用于增强出题与评分的知识库"
                  optionLabelProp="label"
                  options={availableKnowledgeBases.map((item) => ({
                    value: item.id,
                    label: item.name,
                    children: (
                      <Space direction="vertical" size={0}>
                        <Text strong>{item.name}</Text>
                        <Text type="secondary">
                          {item.description || '暂无描述'} · {item.document_count} 个可用文档
                        </Text>
                      </Space>
                    ),
                  }))}
                />
              </Form.Item>
            </section>

            <section className="form-section form-section-wide form-section-note">
              <Title level={4}>其他增强设置</Title>
              <Space direction="vertical" size={12} className="resume-enhance-panel">
                <Text type="secondary">
                  创建后可在面试详情页继续使用浏览器朗读、录音转写、本地虚拟面试官和讯飞云端数字人试用。
                </Text>
                <div className="resume-enhance-box">
                  <Space direction="vertical" size={6}>
                    <Text strong>简历增强面试</Text>
                    {activeResume ? (
                      <Text type="secondary">本场引用当前启用简历：{activeResume.title}</Text>
                    ) : (
                      <Text type="secondary">
                        未启用简历，本场面试仍将按岗位与知识库生成问题。
                        <Link to="/resumes"> 去添加简历</Link>
                      </Text>
                    )}
                  </Space>
                  <Form.Item
                    name="use_active_resume"
                    valuePropName="checked"
                    className="resume-enhance-switch"
                  >
                    <Switch
                      checkedChildren="结合简历"
                      unCheckedChildren="不使用"
                      disabled={!activeResume}
                    />
                  </Form.Item>
                </div>
                {resumesQuery.isError && (
                  <Text type="danger">{getApiErrorMessage(resumesQuery.error)}</Text>
                )}
              </Space>
            </section>
          </div>
          <div className="form-submit-row">
            <Button onClick={() => navigate('/dashboard')}>取消</Button>
            <Button type="primary" htmlType="submit" loading={mutation.isPending}>
              创建面试
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  )
}
