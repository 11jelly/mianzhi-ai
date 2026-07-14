import {
  CheckCircleOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileTextOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Drawer,
  Form,
  Input,
  List,
  Modal,
  Space,
  Switch,
  Tabs,
  Tag,
  Typography,
  Upload,
} from 'antd'
import type { UploadFile } from 'antd'
import { useState } from 'react'

import { getApiErrorMessage } from '../api/client'
import {
  activateResume,
  deactivateResume,
  deleteResume,
  getResume,
  listResumes,
  pasteResume,
  uploadResume,
} from '../api/resumes'
import { EmptyState, PageHeader } from '../components/ui'
import type { Resume, ResumePasteRequest } from '../types/resume'

const { Paragraph, Text } = Typography

const statusMeta: Record<Resume['status'], { label: string; color: string }> = {
  PROCESSING: { label: '处理中', color: 'processing' },
  READY: { label: '可用', color: 'success' },
  FAILED: { label: '失败', color: 'error' },
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

export function ResumePage() {
  const [pasteForm] = Form.useForm<ResumePasteRequest>()
  const [uploadForm] = Form.useForm<{ title?: string; activate?: boolean }>()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const resumesQuery = useQuery({ queryKey: ['resumes'], queryFn: listResumes })
  const detailQuery = useQuery({
    queryKey: ['resume', selectedResumeId],
    queryFn: () => getResume(selectedResumeId as string),
    enabled: Boolean(selectedResumeId),
  })
  const invalidateResumes = () => {
    queryClient.invalidateQueries({ queryKey: ['resumes'] })
    queryClient.invalidateQueries({ queryKey: ['resume'] })
  }

  const pasteMutation = useMutation({
    mutationFn: pasteResume,
    onSuccess: () => {
      pasteForm.resetFields()
      invalidateResumes()
    },
  })
  const uploadMutation = useMutation({
    mutationFn: (values: { file: File; title: string; activate: boolean }) =>
      uploadResume(values.file, values.title, values.activate),
    onSuccess: () => {
      uploadForm.resetFields()
      setSelectedFile(null)
      invalidateResumes()
    },
  })
  const activateMutation = useMutation({
    mutationFn: activateResume,
    onSuccess: invalidateResumes,
  })
  const deactivateMutation = useMutation({
    mutationFn: deactivateResume,
    onSuccess: invalidateResumes,
  })
  const deleteMutation = useMutation({
    mutationFn: deleteResume,
    onSuccess: invalidateResumes,
  })

  const activeResume = resumesQuery.data?.find((item) => item.is_active)

  return (
    <div className="page-stack">
      <PageHeader
        title="我的简历"
        description="管理多个简历版本，启用当前简历后可在创建面试时结合简历生成更贴合经历的问题。"
      />

      <div className="resume-layout">
        <Card title="当前启用与历史版本" className="section-card resume-list-pane">
          {resumesQuery.isError && (
            <Alert type="error" showIcon message={getApiErrorMessage(resumesQuery.error)} />
          )}
          {activeResume ? (
            <Alert
              type="success"
              showIcon
              message={`当前启用简历：${activeResume.title}`}
              className="resume-active-alert"
            />
          ) : (
            <Alert
              type="info"
              showIcon
              message="当前未启用简历，创建面试时将仅依据岗位和知识库生成问题。"
              className="resume-active-alert"
            />
          )}

          {resumesQuery.data?.length ? (
            <List
              className="resume-version-list"
              dataSource={resumesQuery.data}
              renderItem={(item) => {
                const meta = statusMeta[item.status]
                return (
                  <List.Item
                    actions={[
                      <Button
                        key="view"
                        type="text"
                        icon={<EyeOutlined />}
                        onClick={() => setSelectedResumeId(item.id)}
                      >
                        查看解析内容
                      </Button>,
                      item.is_active ? (
                        <Button
                          key="deactivate"
                          onClick={() => deactivateMutation.mutate(item.id)}
                          loading={deactivateMutation.isPending}
                        >
                          停用
                        </Button>
                      ) : (
                        <Button
                          key="activate"
                          type="primary"
                          disabled={item.status !== 'READY'}
                          icon={<CheckCircleOutlined />}
                          onClick={() => activateMutation.mutate(item.id)}
                          loading={activateMutation.isPending}
                        >
                          启用
                        </Button>
                      ),
                      <Button
                        key="delete"
                        danger
                        type="text"
                        icon={<DeleteOutlined />}
                        loading={deleteMutation.isPending}
                        onClick={() => {
                          Modal.confirm({
                            title: '删除简历？',
                            content:
                              '删除只会停用并软删除该简历，不会影响已创建面试保留的简历快照。',
                            okText: '删除',
                            okButtonProps: { danger: true },
                            cancelText: '取消',
                            onOk: () => deleteMutation.mutate(item.id),
                          })
                        }}
                      />,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<FileTextOutlined />}
                      title={
                        <Space wrap>
                          <span className="resume-title">{item.title}</span>
                          {item.is_active ? <Tag color="blue">当前启用</Tag> : null}
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={4}>
                          <Space wrap>
                            <Tag>{item.source_type === 'UPLOAD' ? '上传' : '粘贴'}</Tag>
                            <Tag color={meta.color}>{meta.label}</Tag>
                            <Tag>{item.extracted_text_length} 字</Tag>
                            <Tag>{item.chunk_count} 个片段</Tag>
                          </Space>
                          {item.original_filename ? (
                            <Text type="secondary">文件：{item.original_filename}</Text>
                          ) : null}
                          {item.error_message ? (
                            <Text type="danger">{item.error_message}</Text>
                          ) : null}
                          <Text type="secondary">创建于 {formatTime(item.created_at)}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )
              }}
            />
          ) : (
            <EmptyState
              title="还没有简历"
              description="上传文件或粘贴文本后，可启用其中一份作为简历增强面试背景。"
            />
          )}
        </Card>

        <Card title="添加简历" className="section-card resume-create-pane">
          <Tabs
            items={[
              {
                key: 'upload',
                label: '上传文件',
                children: (
                  <Form
                    form={uploadForm}
                    layout="vertical"
                    initialValues={{ activate: true }}
                    onFinish={(values) => {
                      if (!selectedFile) {
                        return
                      }
                      uploadMutation.mutate({
                        file: selectedFile,
                        title: values.title ?? '',
                        activate: values.activate ?? true,
                      })
                    }}
                  >
                    {uploadMutation.isError && (
                      <Alert
                        type="error"
                        showIcon
                        message={getApiErrorMessage(uploadMutation.error)}
                      />
                    )}
                    <Form.Item name="title" label="简历标题">
                      <Input placeholder="后端开发简历 2026" />
                    </Form.Item>
                    <Form.Item label="简历文件" required>
                      <Upload
                        maxCount={1}
                        accept=".txt,.md,.pdf"
                        beforeUpload={(file) => {
                          setSelectedFile(file)
                          return false
                        }}
                        onRemove={() => setSelectedFile(null)}
                        fileList={
                          selectedFile
                            ? ([{ uid: selectedFile.name, name: selectedFile.name }] as UploadFile[])
                            : []
                        }
                      >
                        <Button icon={<UploadOutlined />}>选择 PDF / TXT / MD</Button>
                      </Upload>
                    </Form.Item>
                    <Form.Item name="activate" valuePropName="checked" label="保存后启用">
                      <Switch />
                    </Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={uploadMutation.isPending}
                      disabled={!selectedFile}
                    >
                      上传并解析
                    </Button>
                  </Form>
                ),
              },
              {
                key: 'paste',
                label: '粘贴文本',
                children: (
                  <Form<ResumePasteRequest>
                    form={pasteForm}
                    layout="vertical"
                    initialValues={{ activate: true }}
                    onFinish={(values) => pasteMutation.mutate(values)}
                  >
                    {pasteMutation.isError && (
                      <Alert
                        type="error"
                        showIcon
                        message={getApiErrorMessage(pasteMutation.error)}
                      />
                    )}
                    <Form.Item
                      name="title"
                      label="简历标题"
                      rules={[{ required: true, message: '请输入简历标题' }]}
                    >
                      <Input placeholder="后端开发简历 2026" />
                    </Form.Item>
                    <Form.Item
                      name="resume_text"
                      label="简历文本"
                      rules={[{ required: true, message: '请粘贴简历文本' }]}
                    >
                      <Input.TextArea rows={12} placeholder="粘贴简历正文，系统会自动隐藏邮箱、手机号和明显地址字段。" />
                    </Form.Item>
                    <Form.Item name="activate" valuePropName="checked" label="保存后启用">
                      <Switch />
                    </Form.Item>
                    <Button type="primary" htmlType="submit" loading={pasteMutation.isPending}>
                      保存简历
                    </Button>
                  </Form>
                ),
              },
            ]}
          />
        </Card>
      </div>

      <Drawer
        title="解析后的简历内容"
        open={Boolean(selectedResumeId)}
        width={640}
        onClose={() => setSelectedResumeId(null)}
      >
        {detailQuery.isError ? (
          <Alert type="error" showIcon message={getApiErrorMessage(detailQuery.error)} />
        ) : (
          <Space direction="vertical" size={16} className="resume-detail-drawer">
            <Text strong>{detailQuery.data?.title}</Text>
            <Paragraph type="secondary">
              以下内容为系统保存的脱敏解析文本，仅用于简历增强面试。
            </Paragraph>
            <pre className="resume-text-preview">
              {detailQuery.data?.normalized_text || '暂无解析内容'}
            </pre>
          </Space>
        )}
      </Drawer>
    </div>
  )
}
