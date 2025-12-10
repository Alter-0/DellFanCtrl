<template>
  <div class="empty-state">
    <el-empty description="暂无历史数据">
      <template #image>
        <el-icon :size="64" class="empty-icon"><DataLine /></el-icon>
      </template>
      <p class="empty-hint">系统正在收集监控数据，请稍后查看</p>
    </el-empty>
  </div>
</template>

<script setup>
import { DataLine } from '@element-plus/icons-vue'
</script>

<style scoped>
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background-color: #fafafa;
  border-radius: 8px;
}

.empty-icon {
  color: #909399;
}

.empty-hint {
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}
</style>
