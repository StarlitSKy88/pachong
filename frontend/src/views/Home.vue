<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <h2>欢迎使用爬虫工具</h2>
            </div>
          </template>
          <div class="card-content">
            <p>服务器状态：{{ serverStatus }}</p>
            <p>当前时间：{{ currentTime }}</p>
            <el-button type="primary" @click="checkHealth">检查服务器状态</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-4">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>快速开始</h3>
            </div>
          </template>
          <div class="card-content">
            <el-button type="success" @click="$router.push('/tasks')">创建新任务</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>系统状态</h3>
            </div>
          </template>
          <div class="card-content">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="API版本">{{ apiVersion }}</el-descriptions-item>
              <el-descriptions-item label="运行环境">{{ environment }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>最近任务</h3>
            </div>
          </template>
          <div class="card-content">
            <el-empty v-if="!recentTasks.length" description="暂无任务"></el-empty>
            <el-timeline v-else>
              <el-timeline-item
                v-for="task in recentTasks"
                :key="task.id"
                :timestamp="task.time">
                {{ task.name }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const serverStatus = ref('检查中...')
const currentTime = ref('')
const apiVersion = ref('1.0.0')
const environment = ref('生产环境')
const recentTasks = ref([])

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN')
}

const checkHealth = async () => {
  try {
    const response = await axios.get('http://localhost:9000/health')
    serverStatus.value = response.data.status === 'healthy' ? '正常' : '异常'
    ElMessage.success('服务器状态正常')
  } catch (error) {
    serverStatus.value = '无法连接'
    ElMessage.error('无法连接到服务器')
  }
}

onMounted(() => {
  updateTime()
  setInterval(updateTime, 1000)
  checkHealth()
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  padding: 10px 0;
}

.mt-4 {
  margin-top: 20px;
}

h2, h3 {
  margin: 0;
}
</style> 