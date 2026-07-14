import { Empty } from 'antd'
import * as echarts from 'echarts'
import { useEffect, useRef } from 'react'

type AbilityRadarChartProps = {
  report?: {
    logic_score: number
    technical_score: number
    expression_score: number
    project_depth_score: number
  } | null
}

const dimensions = [
  { name: '逻辑结构', max: 25, key: 'logic_score' },
  { name: '技术准确性', max: 30, key: 'technical_score' },
  { name: '表达清晰度', max: 20, key: 'expression_score' },
  { name: '项目深度', max: 25, key: 'project_depth_score' },
] as const

function isValidScore(value: unknown, max: number): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= max
}

export function AbilityRadarChart({ report }: AbilityRadarChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  const values = report
    ? dimensions.map((dimension) => report[dimension.key])
    : []
  const hasValidData =
    Boolean(report) &&
    dimensions.every((dimension, index) => isValidScore(values[index], dimension.max))

  useEffect(() => {
    if (!containerRef.current || !hasValidData) {
      return undefined
    }

    const chart = echarts.init(containerRef.current)
    chart.setOption({
      tooltip: {},
      radar: {
        indicator: dimensions.map(({ name, max }) => ({ name, max })),
        radius: '64%',
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: values,
              name: '能力分布',
              areaStyle: { opacity: 0.18 },
            },
          ],
        },
      ],
    })

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
    }
  }, [hasValidData, values])

  if (!hasValidData) {
    return (
      <div className="radar-chart radar-chart-empty">
        <Empty description="暂无有效能力数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    )
  }

  return <div ref={containerRef} className="radar-chart" />
}
