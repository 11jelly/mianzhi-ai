import { DeleteOutlined, SearchOutlined, UploadOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  List,
  Space,
  Tag,
  Typography,
  Upload,
} from 'antd'
import type { UploadProps } from 'antd'
import { Link, useParams } from 'react-router-dom'

import { getApiErrorMessage } from '../api/client'
import {
  deleteKnowledgeDocument,
  getKnowledgeBase,
  listKnowledgeDocuments,
  searchKnowledgeBase,
  uploadKnowledgeDocument,
} from '../api/knowledgeBases'
import { EmptyState, PageHeader } from '../components/ui'

const { Text } = Typography

export function KnowledgeBaseDetailPage() {
  const { knowledgeBaseId } = useParams()
  const queryClient = useQueryClient()
  const id = knowledgeBaseId ?? ''
  const baseQuery = useQuery({
    queryKey: ['knowledge-bases', id],
    queryFn: () => getKnowledgeBase(id),
    enabled: Boolean(id),
  })
  const documentsQuery = useQuery({
    queryKey: ['knowledge-bases', id, 'documents'],
    queryFn: () => listKnowledgeDocuments(id),
    enabled: Boolean(id),
  })
  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadKnowledgeDocument(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases', id] })
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases', id, 'documents'] })
    },
  })
  const deleteMutation = useMutation({
    mutationFn: (documentId: string) => deleteKnowledgeDocument(id, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases', id] })
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases', id, 'documents'] })
    },
  })
  const searchMutation = useMutation({
    mutationFn: (query: string) => searchKnowledgeBase(id, query),
  })

  const uploadProps: UploadProps = {
    accept: '.txt,.md,.pdf',
    maxCount: 1,
    showUploadList: false,
    beforeUpload: (file) => {
      uploadMutation.mutate(file)
      return false
    },
  }

  return (
    <div className="page-stack">
      <PageHeader
        title={baseQuery.data?.name ?? '知识库详情'}
        description={baseQuery.data?.description || '管理知识库文档与检索测试。'}
        actions={<Link to="/knowledge-bases">返回知识库</Link>}
      />

      {(baseQuery.isError || documentsQuery.isError) && (
        <Alert
          type="error"
          showIcon
          message={getApiErrorMessage(baseQuery.error ?? documentsQuery.error)}
        />
      )}

      <div className="knowledge-detail-layout">
        <Card
          title="文档"
          className="section-card"
          extra={
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />} loading={uploadMutation.isPending}>
                上传文档
              </Button>
            </Upload>
          }
        >
          {uploadMutation.isError && (
            <Alert type="error" showIcon message={getApiErrorMessage(uploadMutation.error)} />
          )}
          {documentsQuery.data?.length ? (
            <List
              className="local-scroll-list"
              dataSource={documentsQuery.data}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      key="delete"
                      danger
                      type="text"
                      icon={<DeleteOutlined />}
                      loading={deleteMutation.isPending}
                      onClick={() => deleteMutation.mutate(item.id)}
                    />,
                  ]}
                >
                  <List.Item.Meta
                    title={item.original_filename}
                    description={
                      <Space wrap>
                        <Tag>{item.file_type}</Tag>
                        <Tag>{item.chunk_count} 个分块</Tag>
                        <Tag color={item.status === 'READY' ? 'success' : 'processing'}>
                          {item.status}
                        </Tag>
                        {item.error_message ? <Text type="danger">{item.error_message}</Text> : null}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <EmptyState title="还没有上传文档" description="支持上传 txt、md、pdf 文件用于后续检索。" />
          )}
        </Card>

        <Card title="检索测试" className="section-card">
          <Form<{ query: string }>
            layout="inline"
            onFinish={(values) => searchMutation.mutate(values.query)}
          >
            <Form.Item
              name="query"
              rules={[{ required: true, message: '请输入检索内容' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="输入岗位要求、技术点或面试问题" />
            </Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SearchOutlined />}
              loading={searchMutation.isPending}
            >
              搜索
            </Button>
          </Form>
          {searchMutation.isError && (
            <Alert type="error" showIcon message={getApiErrorMessage(searchMutation.error)} />
          )}
          {searchMutation.data?.items.length ? (
            <List
              className="local-scroll-list"
              dataSource={searchMutation.data.items}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={`${item.document_name} · ${item.score.toFixed(3)}`}
                    description={item.content_preview}
                  />
                </List.Item>
              )}
            />
          ) : null}
        </Card>
      </div>
    </div>
  )
}
