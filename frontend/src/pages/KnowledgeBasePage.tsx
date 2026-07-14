import { DatabaseOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Card, Form, Input, List, Modal, Space, Tag, Typography } from 'antd'
import { Link } from 'react-router-dom'

import { getApiErrorMessage } from '../api/client'
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  listKnowledgeBases,
} from '../api/knowledgeBases'
import { EmptyState, PageHeader } from '../components/ui'
import type { KnowledgeBaseCreateRequest } from '../types/knowledgeBase'

const { Text } = Typography

export function KnowledgeBasePage() {
  const [form] = Form.useForm<KnowledgeBaseCreateRequest>()
  const queryClient = useQueryClient()
  const knowledgeBasesQuery = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: listKnowledgeBases,
  })
  const createMutation = useMutation({
    mutationFn: createKnowledgeBase,
    onSuccess: () => {
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] })
    },
  })
  const deleteMutation = useMutation({
    mutationFn: deleteKnowledgeBase,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] }),
  })

  return (
    <div className="page-stack">
      <PageHeader
        title="知识库"
        description="管理岗位 JD、项目材料和技术笔记，用于 RAG 面试生成与评分参考。"
      />

      <div className="knowledge-layout">
        <Card title="我的知识库" className="section-card knowledge-list-pane">
          {knowledgeBasesQuery.isError && (
            <Alert type="error" showIcon message={getApiErrorMessage(knowledgeBasesQuery.error)} />
          )}
          {knowledgeBasesQuery.data?.length ? (
            <List
              dataSource={knowledgeBasesQuery.data}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Link key="detail" to={`/knowledge-bases/${item.id}`}>
                      查看详情
                    </Link>,
                    <Button
                      key="delete"
                      danger
                      type="text"
                      icon={<DeleteOutlined />}
                      loading={deleteMutation.isPending}
                      onClick={() => {
                        Modal.confirm({
                          title: '删除知识库？',
                          content: '删除后该知识库下的文档和分块也会被移除。',
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
                    avatar={<DatabaseOutlined />}
                    title={<Link to={`/knowledge-bases/${item.id}`}>{item.name}</Link>}
                    description={
                      <Space direction="vertical" size={4}>
                        <Text type="secondary">{item.description || '暂无描述'}</Text>
                        <Space wrap>
                          <Tag>{item.document_count} 个文档</Tag>
                          <Tag>{item.chunk_count} 个分块</Tag>
                          <Tag color={item.status === 'READY' ? 'success' : 'default'}>
                            {item.status}
                          </Tag>
                        </Space>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <EmptyState title="还没有知识库" description="创建知识库后，可上传岗位资料并进行检索测试。" />
          )}
        </Card>

        <Card title="新建知识库" className="section-card">
          <Form<KnowledgeBaseCreateRequest>
            form={form}
            layout="vertical"
            onFinish={(values) => createMutation.mutate(values)}
          >
            {createMutation.isError && (
              <Alert type="error" showIcon message={getApiErrorMessage(createMutation.error)} />
            )}
            <Form.Item
              name="name"
              label="名称"
              rules={[{ required: true, message: '请输入知识库名称' }]}
            >
              <Input placeholder="Python 后端面试资料" />
            </Form.Item>
            <Form.Item name="description" label="描述">
              <Input.TextArea rows={4} placeholder="可填写资料范围、岗位方向或项目背景" />
            </Form.Item>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              htmlType="submit"
              loading={createMutation.isPending}
            >
              创建知识库
            </Button>
          </Form>
        </Card>
      </div>
    </div>
  )
}
