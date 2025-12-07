<template>
  <div class="log-viewer">
    <el-card>
      <template #header>
        <div class="log-header">
          <span>系统日志</span>
          <div class="filters">
            <el-select v-model="levelFilter" placeholder="日志级别" clearable size="small" @change="loadLogs">
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
            </el-select>
            <el-input 
              v-model="searchKeyword" 
              placeholder="搜索关键词" 
              size="small" 
              clearable
              @keyup.enter="loadLogs"
              style="width: 200px"
            />
            <el-button size="small" @click="loadLogs">
              <el-icon><Search /></el-icon>
            </el-button>
            <el-button size="small" @click="clearFilters">清除</el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="fanStore.logs" 
        height="500" 
        stripe 
        size="small"
        :row-class-name="getRowClass"
      >
        <el-table-column prop="time" label="时间" width="180" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" show-overflow-tooltip />
      </el-table>
      
      <div class="log-footer">
        <span>共 {{ fanStore.logs.length }} 条日志</span>
        <el-button size="small" @click="loadLogs">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useFanStore } from '../stores/fan'

const fanStore = useFanStore()
const levelFilter = ref('')
const searchKeyword = ref('')

function getLevelType(level) {
  const types = {
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'danger',
    'CRITICAL': 'danger'
  }
  return types[level] || 'info'
}

function getRowClass({ row }) {
  if (row.level === 'ERROR' || row.level === 'CRITICAL') {
    return 'error-row'
  }
  if (row.level === 'WARNING') {
    return 'warning-row'
  }
  return ''
}

async function loadLogs() {
  try {
    await fanStore.fetchLogs({
      level: levelFilter.value || undefined,
      search: searchKeyword.value || undefined,
      limit: 200
    })
  } catch (error) {
    console.error('Failed to load logs:', error)
  }
}

function clearFilters() {
  levelFilter.value = ''
  searchKeyword.value = ''
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.log-viewer {
  padding: 20px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  color: #909399;
}

:deep(.error-row) {
  background-color: #fef0f0 !important;
}

:deep(.warning-row) {
  background-color: #fdf6ec !important;
}
</style>
