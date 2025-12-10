<template>
  <div class="dashboard">
    <!-- 实时状态卡片 -->
    <el-row :gutter="20" class="status-cards">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Cpu /></el-icon>
              <span>CPU 温度</span>
            </div>
          </template>
          <div class="stat-value" :class="tempClass">
            {{ (fanStore.status.cpu_temp || 0).toFixed(1) }}°C
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Odometer /></el-icon>
              <span>风扇转速</span>
            </div>
          </template>
          <div class="stat-value">
            {{ fanStore.status.fan_speed }}%
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Lightning /></el-icon>
              <span>系统功耗</span>
            </div>
          </template>
          <div class="stat-value">
            {{ fanStore.status.power }}W
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 历史趋势图 -->
    <el-card class="chart-card" shadow="hover">
      <template #header>
        <div class="chart-header">
          <span>历史趋势</span>
          <el-radio-group v-model="timeRange" size="small" @change="loadHistory">
            <el-radio-button label="1h">1小时</el-radio-button>
            <el-radio-button label="6h">6小时</el-radio-button>
            <el-radio-button label="24h">24小时</el-radio-button>
            <el-radio-button label="7d">7天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <template v-if="hasHistoryData">
        <div ref="chartRef" class="history-chart"></div>
      </template>
      <template v-else>
        <EmptyState />
      </template>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useFanStore } from '../stores/fan'
import * as echarts from 'echarts'
import EmptyState from './EmptyState.vue'

const fanStore = useFanStore()
const chartRef = ref(null)
const timeRange = ref('1h')
let chart = null
let resizeObserver = null

const tempClass = computed(() => {
  const temp = fanStore.status.cpu_temp
  if (temp >= 80) return 'danger'
  if (temp >= 70) return 'warning'
  return 'normal'
})

// Computed property to check if history data is empty
const hasHistoryData = computed(() => {
  return fanStore.history && fanStore.history.length > 0
})

function initChart() {
  if (!chartRef.value) return
  
  // 确保容器有尺寸
  if (chartRef.value.offsetWidth === 0 || chartRef.value.offsetHeight === 0) {
    setTimeout(initChart, 100)
    return
  }
  
  chart = echarts.init(chartRef.value)
  updateChart()
  
  // 使用 ResizeObserver 监听容器尺寸变化
  resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartRef.value)
}

function updateChart() {
  const data = fanStore.history
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['CPU温度', '风扇转速', '功耗']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: '温度/转速',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}' }
      },
      {
        type: 'value',
        name: '功耗(W)',
        min: 0,
        axisLabel: { formatter: '{value}W' }
      }
    ],
    series: [
      {
        name: 'CPU温度',
        type: 'line',
        smooth: true,
        data: data.map(d => [d.time, d.cpu_temp]),
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: '风扇转速',
        type: 'line',
        smooth: true,
        data: data.map(d => [d.time, d.fan_speed]),
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '功耗',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: data.map(d => [d.time, d.power]),
        itemStyle: { color: '#67C23A' }
      }
    ]
  }
  
  chart.setOption(option)
}

async function loadHistory() {
  try {
    await fanStore.fetchHistory(timeRange.value)
    // Only update chart if it exists and we have data
    if (chart && hasHistoryData.value) {
      updateChart()
    }
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

// Watch history changes and update chart when data is available
watch(() => fanStore.history, () => {
  if (hasHistoryData.value) {
    nextTick(() => {
      if (!chart && chartRef.value) {
        initChart()
      } else {
        updateChart()
      }
    })
  }
}, { deep: true })

// Watch hasHistoryData to initialize chart when data becomes available
watch(hasHistoryData, (newValue) => {
  if (newValue) {
    nextTick(() => {
      if (!chart && chartRef.value) {
        initChart()
      }
    })
  }
})

// 保存 resize 处理函数引用，以便正确移除
const handleResize = () => chart?.resize()

onMounted(async () => {
  // 等待 DOM 更新后再初始化图表
  await nextTick()
  loadHistory()
  
  // Only initialize chart if we have data
  if (hasHistoryData.value) {
    setTimeout(initChart, 50)
  }
  
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.status-cards {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  text-align: center;
  color: #409EFF;
}

.stat-value.warning { color: #E6A23C; }
.stat-value.danger { color: #F56C6C; }

.chart-card {
  margin-top: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-chart {
  height: 400px;
}
</style>
