import { Alert, Button, Result } from 'antd'
import { isRouteErrorResponse, useRouteError } from 'react-router-dom'

export function RouteErrorPage() {
  const error = useRouteError()
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : '页面暂时无法显示。'

  return (
    <Result
      status="error"
      title="页面暂时无法显示"
      subTitle="请刷新页面或稍后重试。"
      extra={
        <>
          <Alert type="error" showIcon message={message} />
          <Button type="primary" onClick={() => window.location.reload()}>
            刷新页面
          </Button>
        </>
      }
    />
  )
}
