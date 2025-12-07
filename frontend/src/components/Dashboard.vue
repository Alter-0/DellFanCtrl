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
    <el-card class="chart-card">
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
      <div ref="chartRef" class="history-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFanStore } from '../stores/fan'
import * as echarts from 'echarts'

const fanStore = useFanStore()
const chartRef = ref(null)
const timeRange = ref('1h')
let chart = null

const tempClass = computed(() => {
  const temp = fanStore.status.cpu_temp
  if (temp >= 80) return 'danger'
  if (temp >= 70) return 'warning'
  return 'normal'
})

function initChart() {
  chart = echarts.init(chartRef.value)
  updateChart()
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
    updateChart()
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

watch(() => fanStore.history, updateChart, { deep: true })

onMounted(() => {
  initChart()
  loadHistory()
  
  window.addEventListener('resize', () => chart?.resize())
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
