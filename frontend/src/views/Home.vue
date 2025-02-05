<template>
  <div class="home-container">
    <!-- 顶部状态栏 -->
    <el-row class="status-bar" :gutter="20">
      <el-col :span="6">
        <el-card>
          <template #header>系统状态</template>
          <div class="status-item">
            <i :class="systemStatus.icon" :style="{color: systemStatus.color}"></i>
            {{ systemStatus.text }}
      </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>运行任务</template>
          <div class="status-item">{{ stats.runningTasks }} 个</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>完成任务</template>
          <div class="status-item">{{ stats.completedTasks }} 个</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>成功率</template>
          <div class="status-item">{{ stats.successRate }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务控制面板 -->
    <el-card class="task-panel">
      <template #header>
        <div class="task-header">
          <span>任务控制</span>
          <el-button type="primary" @click="showCreateTask">新建任务</el-button>
      </div>
      </template>
      
      <!-- 任务列表 -->
      <el-table :data="tasks" style="width: 100%">
        <el-table-column prop="id" label="任务ID" width="180" />
        <el-table-column prop="platform" label="平台" width="120" />
        <el-table-column prop="keywords" label="关键词" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="180">
          <template #default="scope">
            <el-progress :percentage="scope.row.progress" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button 
              size="small" 
              :type="scope.row.status === 'running' ? 'danger' : 'primary'"
              @click="handleTaskAction(scope.row)"
            >
              {{ scope.row.status === 'running' ? '停止' : '查看' }}
            </el-button>
            <el-button 
              size="small"
              type="success" 
              @click="viewResults(scope.row)"
              :disabled="scope.row.status !== 'completed'"
            >
              结果
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="createTaskDialog" title="创建新任务" width="500px">
      <el-form :model="newTask" label-width="100px">
        <el-form-item label="平台">
          <el-select v-model="newTask.platform" placeholder="选择平台">
            <el-option label="小红书" value="xiaohongshu" />
            <el-option label="B站" value="bilibili" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="newTask.keywords" type="textarea" :rows="2" placeholder="每行一个关键词" />
        </el-form-item>
        <el-form-item label="最大页数">
          <el-input-number v-model="newTask.maxPages" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="数据过滤">
          <el-checkbox-group v-model="newTask.filters">
            <el-checkbox label="图文">图文</el-checkbox>
            <el-checkbox label="视频">视频</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createTaskDialog = false">取消</el-button>
          <el-button type="primary" @click="createTask">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看结果对话框 -->
    <el-dialog v-model="resultDialog" title="任务结果" width="80%">
      <el-tabs v-model="activeResultTab">
        <el-tab-pane label="数据概览" name="overview">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="采集数据量" :value="taskResult.totalItems" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="图文数" :value="taskResult.imageCount" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="视频数" :value="taskResult.videoCount" />
            </el-col>
          </el-row>
        </el-tab-pane>
        <el-tab-pane label="详细数据" name="details">
          <el-table :data="taskResult.items" style="width: 100%">
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="likes" label="点赞数" width="100" />
            <el-table-column prop="comments" label="评论数" width="100" />
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button size="small" @click="viewDetail(scope.row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'

// 系统状态数据
const systemStatus = ref({
  text: '运行正常',
  icon: 'el-icon-success',
  color: '#67C23A'
})

// 统计数据
const stats = ref({
  runningTasks: 0,
  completedTasks: 0,
  successRate: 0
})

// 任务列表数据
const tasks = ref([])

// 新建任务相关
const createTaskDialog = ref(false)
const newTask = ref({
  platform: '',
  keywords: '',
  maxPages: 10,
  filters: []
})

// 结果查看相关
const resultDialog = ref(false)
const activeResultTab = ref('overview')
const taskResult = ref({
  totalItems: 0,
  imageCount: 0,
  videoCount: 0,
  items: []
})

// 获取任务状态样式
const getStatusType = (status) => {
  const types = {
    'running': 'primary',
    'completed': 'success',
    'failed': 'danger',
    'pending': 'info'
  }
  return types[status] || 'info'
}

// 显示创建任务对话框
const showCreateTask = () => {
  createTaskDialog.value = true
}

// 创建新任务
const createTask = async () => {
  try {
    // 这里调用API创建任务
    const response = await fetch('/api/v1/crawlers/tasks', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        platform: newTask.value.platform,
        keywords: newTask.value.keywords.split('\n'),
        max_pages: newTask.value.maxPages,
        filters: {
          content_type: newTask.value.filters
        }
      })
    })
    
    if (response.ok) {
      ElMessage.success('任务创建成功')
      createTaskDialog.value = false
      fetchTasks() // 刷新任务列表
    } else {
      throw new Error('任务创建失败')
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

// 处理任务操作
const handleTaskAction = async (task) => {
  if (task.status === 'running') {
    try {
      const response = await fetch(`/api/v1/crawlers/tasks/${task.id}/stop`, {
        method: 'POST'
      })
      if (response.ok) {
        ElMessage.success('任务已停止')
        fetchTasks() // 刷新任务列表
      }
    } catch (error) {
      ElMessage.error('停止任务失败')
    }
  } else {
    // 查看任务详情
    viewResults(task)
  }
}

// 查看任务结果
const viewResults = async (task) => {
  try {
    const response = await fetch(`/api/v1/data/results/${task.id}`)
    if (response.ok) {
      const data = await response.json()
      taskResult.value = {
        totalItems: data.total,
        imageCount: data.items.filter(item => item.type === '图文').length,
        videoCount: data.items.filter(item => item.type === '视频').length,
        items: data.items
      }
      resultDialog.value = true
    }
  } catch (error) {
    ElMessage.error('获取任务结果失败')
  }
}

// 查看详细数据
const viewDetail = (item) => {
  // 实现查看详情的逻辑
  console.log('查看详情:', item)
}

// 获取任务列表
const fetchTasks = async () => {
  try {
    const response = await fetch('/api/v1/crawlers/tasks')
    if (response.ok) {
      const data = await response.json()
      tasks.value = data
      // 更新统计数据
      stats.value = {
        runningTasks: data.filter(t => t.status === 'running').length,
        completedTasks: data.filter(t => t.status === 'completed').length,
        successRate: calculateSuccessRate(data)
      }
    }
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  }
}

// 计算成功率
const calculateSuccessRate = (tasks) => {
  const completed = tasks.filter(t => t.status === 'completed').length
  const total = tasks.filter(t => t.status === 'completed' || t.status === 'failed').length
  return total ? Math.round((completed / total) * 100) : 0
}

// 页面加载时获取数据
onMounted(() => {
  fetchTasks()
  // 定时刷新任务列表
  setInterval(fetchTasks, 5000)
})
</script>

<style scoped>
.home-container {
  padding: 20px;
}

.status-bar {
  margin-bottom: 20px;
}

.status-item {
  font-size: 24px;
  text-align: center;
}

.task-panel {
  margin-bottom: 20px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 