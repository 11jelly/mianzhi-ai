import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { Alert, Button, Form, Input, Space, Typography, message } from 'antd'
import { Link, useNavigate } from 'react-router-dom'

import { registerUser } from '../api/auth'
import { getApiErrorMessage } from '../api/client'
import type { RegisterRequest } from '../api/types'
import { AuthShell } from './AuthShell'

const { Text } = Typography

export function RegisterPage() {
  const navigate = useNavigate()
  const mutation = useMutation({
    mutationFn: registerUser,
    onSuccess: () => {
      message.success('注册成功，请登录')
      navigate('/login')
    },
  })

  return (
    <AuthShell title="注册" subtitle="创建本地训练账号，开始AI产品经理面试训练。">
      <Form<RegisterRequest> layout="vertical" onFinish={(values) => mutation.mutate(values)}>
        {mutation.isError && (
          <Alert type="error" showIcon message={getApiErrorMessage(mutation.error)} />
        )}
        <Form.Item
          name="username"
          label="用户名"
          rules={[{ required: true, min: 3, max: 32, message: '用户名长度为 3 到 32 个字符' }]}
        >
          <Input prefix={<UserOutlined />} autoComplete="username" />
        </Form.Item>
        <Form.Item
          name="email"
          label="邮箱"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '邮箱格式不正确' },
          ]}
        >
          <Input prefix={<MailOutlined />} autoComplete="email" />
        </Form.Item>
        <Form.Item
          name="password"
          label="密码"
          rules={[{ required: true, min: 8, max: 72, message: '密码长度为 8 到 72 个字符' }]}
        >
          <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
        </Form.Item>
        <Space className="form-actions">
          <Button type="primary" htmlType="submit" loading={mutation.isPending}>
            注册
          </Button>
          <Text type="secondary">
            已有账号？ <Link to="/login">登录</Link>
          </Text>
        </Space>
      </Form>
    </AuthShell>
  )
}
