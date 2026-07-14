import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { Alert, Button, Form, Input, Space, Typography } from 'antd'
import { Link, useNavigate } from 'react-router-dom'

import { loginUser } from '../api/auth'
import { getApiErrorMessage } from '../api/client'
import type { LoginRequest } from '../api/types'
import { useAuthStore } from '../stores/auth'
import { AuthShell } from './AuthShell'

const { Text } = Typography

export function LoginPage() {
  const navigate = useNavigate()
  const setToken = useAuthStore((state) => state.setToken)
  const mutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      setToken(data.access_token)
      navigate('/dashboard')
    },
  })

  return (
    <AuthShell title="登录" subtitle="进入面智AI工作台，继续AI产品经理面试训练。">
      <Form<LoginRequest> layout="vertical" onFinish={(values) => mutation.mutate(values)}>
        {mutation.isError && (
          <Alert type="error" showIcon message={getApiErrorMessage(mutation.error)} />
        )}
        <Form.Item
          name="username_or_email"
          label="用户名或邮箱"
          rules={[{ required: true, message: '请输入用户名或邮箱' }]}
        >
          <Input prefix={<UserOutlined />} autoComplete="username" />
        </Form.Item>
        <Form.Item
          name="password"
          label="密码"
          rules={[{ required: true, min: 8, max: 72, message: '密码长度为 8 到 72 个字符' }]}
        >
          <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
        </Form.Item>
        <Space className="form-actions">
          <Button type="primary" htmlType="submit" loading={mutation.isPending}>
            登录
          </Button>
          <Text type="secondary">
            没有账号？ <Link to="/register">注册</Link>
          </Text>
        </Space>
      </Form>
    </AuthShell>
  )
}
