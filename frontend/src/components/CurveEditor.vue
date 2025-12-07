<template>
  <div class="curve-editor">
    <el-card>
      <template #header>
        <div class="editor-header">
          <span>风扇曲线编辑器</span>
          <div class="actions">
            <el-button type="primary" @click="saveCurve" :loading="saving">
              <el-icon><Check /></el-icon> 保存曲线
            </el-button>
            <el-button @click="resetCurve">
              <el-icon><RefreshRight /></el-icon> 重置
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 曲线图表 -->
      <div ref="chartRef" class="curve-chart"></div>
      
      <!-- 控制点列表 -->
      <el-divider>控制点列表</el-divider>
      
      <el-table :data="points" border size="small">
        <el-table-column label="温度 (°C)" width="200">
          <template #default="{ row }">
            <el-input-number 
              v-model="row.temp" 
              :min="0" 
              :max="100" 
              size="small"
              @change="updateChart"
            />
          </template>
        </el-table-column>
        <el-table-column label="风扇转速 (%)" width="200">
          <template #default="{ row }">
            <el-input-number 
              v-model="row.speed" 
              :min="0" 
              :max="100" 
              size="small"
              @change="updateChart"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ $index }">
            <el-button 
              type="danger" 
              size="small" 
              :disabled="points.length <= 2"
              @click="removePoint($index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-button class="add-btn" @click="addPoint">
        <el-icon><Plus /></el-icon> 添加控制点
      </el-button>
      
      <!-- 当前状态指示 -->
      <el-alert 
        v-if="fanStore.status.cpu_temp > 0"
        :title="`当前温度 ${(fanStore.status.cpu_temp || 0).toFixed(1)}°C → 目标转速 ${calculateSpeed(fanStore.status.cpu_temp || 0)}%`"
        type="info"
        show-icon
        :closable="false"
        class="current-status"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useFanStore } from '../stores/fan'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const fanStore = useFanStore()
const chartRef = ref(null)
const points = ref([])
const saving = ref(false)
let chart = null
let resizeObserver = null

// 计算给定温度对应的转速
function calculateSpeed(temp) {
  const sorted = [...points.value].sort((a, b) => a.temp - b.temp)
  if (sorted.length === 0) return 20
  
  if (temp <= sorted[0].temp) return sorted[0].speed
  if (temp >= sorted[sorted.length - 1].temp) return sorted[sorted.length - 1].speed
  
  for (let i = 0; i < sorted.length - 1; i++) {
    if (sorted[i].temp <= temp && temp < sorted[i + 1].temp) {
      const t0 = sorted[i].temp, s0 = sorted[i].speed
      const t1 = sorted[i + 1].temp, s1 = sorted[i + 1].speed
      return Math.round(s0 + (temp - t0) * (s1 - s0) / (t1 - t0))
    }
  }
  return sorted[sorted.length - 1].speed
}

function initChart() {
  if (!chartRef.value) return
  
  // 确保容器有尺寸
  if (chartRef.value.offsetWidth === 0 || chartRef.value.offsetHeight === 0) {
    // 延迟初始化
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
  const sorted = [...points.value].sort((a, b) => a.temp - b.temp)
  
  // 生成平滑曲线数据
  const curveData = []
  for (let t = 0; t <= 100; t++) {
    curveData.push([t, calculateSpeed(t)])
  }
  
  const option = {
    title: {
      text: '温度-转速曲线',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `温度: ${p.data[0]}°C<br/>转速: ${p.data[1]}%`
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'value',
      name: '温度 (°C)',
      min: 0,
      max: 100,
      splitLine: { show: true }
    },
    yAxis: {
      type: 'value',
      name: '风扇转速 (%)',
      min: 0,
      max: 100,
      splitLine: { show: true }
    },
    series: [
      {
        name: '风扇曲线',
        type: 'line',
        smooth: true,
        data: curveData,
        lineStyle: { width: 3, color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '控制点',
        type: 'scatter',
        data: sorted.map(p => [p.temp, p.speed]),
        symbolSize: 15,
        itemStyle: { color: '#E6A23C' },
        label: {
          show: true,
          formatter: (p) => `${p.data[0]}°C`,
          position: 'top'
        }
      },
      // 当前温度指示线
      fanStore.status.cpu_temp > 0 ? {
        name: '当前温度',
        type: 'line',
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#F56C6C', type: 'dashed', width: 2 },
          data: [{ xAxis: fanStore.status.cpu_temp }],
          label: {
            formatter: `当前: ${(fanStore.status.cpu_temp || 0).toFixed(1)}°C`
          }
        }
      } : null
    ].filter(Boolean)
  }
  
  chart.setOption(option, true)
}

function addPoint() {
  const sorted = [...points.value].sort((a, b) => a.temp - b.temp)
  let newTemp = 50
  
  // 找一个合适的温度点
  if (sorted.length > 0) {
    const lastTemp = sorted[sorted.length - 1].temp
    newTemp = Math.min(lastTemp + 10, 100)
  }
  
  points.value.push({ temp: newTemp, speed: 30 })
  updateChart()
}

function removePoint(index) {
  points.value.splice(index, 1)
  updateChart()
}

async function saveCurve() {
  saving.value = true
  try {
    await fanStore.saveCurve(points.value)
    ElMessage.success('风扇曲线已保存')
  } catch (error) {
    ElMessage.error('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function resetCurve() {
  try {
    await fanStore.fetchCurve()
    points.value = [...fanStore.curve]
    updateChart()
  } catch (error) {
    ElMessage.error('重置失败: ' + error.message)
  }
}

watch(() => fanStore.status.cpu_temp, updateChart)

onMounted(async () => {
  try {
    await fanStore.fetchCurve()
    points.value = [...fanStore.curve]
  } catch (error) {
    console.error('Failed to fetch curve:', error)
    // 使用默认曲线
    points.value = [
      { temp: 50, speed: 15 },
      { temp: 60, speed: 15 },
      { temp: 70, speed: 20 },
      { temp: 80, speed: 40 }
    ]
  }
  
  // 等待 DOM 更新后再初始化图表
  await nextTick()
  setTimeout(initChart, 50)
  
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (chart) {
    chart.dispose()
    chart = null
  }
  window.removeEventListener('resize', () => chart?.resize())
})
</script>

<style scoped>
.curve-editor {
  padding: 20px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.curve-chart {
  height: 400px;
  margin-bottom: 20px;
}

.add-btn {
  margin-top: 15px;
  width: 100%;
}

.current-status {
  margin-top: 20px;
}
</style>
