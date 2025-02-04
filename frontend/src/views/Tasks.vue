<template>
  <div class="tasks">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>任务列表</h2>
          <el-button type="primary" @click="showCreateDialog">创建任务</el-button>
        </div>
      </template>

      <el-table :data="tasks" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button-group>
              <el-button size="small" @click="viewTask(scope.row)">查看</el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteTask(scope.row)">
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建新任务"
      width="50%">
      <el-form :model="newTask" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="newTask.name" />
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="newTask.type" placeholder="请选择任务类型">
            <el-option label="网页爬取" value="web" />
            <el-option label="API采集" value="api" />
            <el-option label="数据处理" value="process" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input
            v-model="newTask.description"
            type="textarea"
            rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createTask">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const tasks = ref([
  {
    id: 1,
    name: '示例任务',
    type: 'web',
    status: '运行中',
    createTime: '2024-02-04 12:00:00',
  }
])

const dialogVisible = ref(false)
const newTask = ref({
  name: '',
  type: '',
  description: ''
})

const showCreateDialog = () => {
  dialogVisible.value = true
  newTask.value = {
    name: '',
    type: '',
    description: ''
  }
}

const createTask = () => {
  // 这里添加创建任务的逻辑
  tasks.value.push({
    id: tasks.value.length + 1,
    name: newTask.value.name,
    type: newTask.value.type,
    status: '等待中',
    createTime: new Date().toLocaleString('zh-CN')
  })
  
  ElMessage.success('任务创建成功')
  dialogVisible.value = false
}

const viewTask = (task) => {
  ElMessage('查看任务详情：' + task.name)
}

const deleteTask = (task) => {
  ElMessageBox.confirm(
    '确定要删除这个任务吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(() => {
      tasks.value = tasks.value.filter(t => t.id !== task.id)
      ElMessage.success('任务已删除')
    })
    .catch(() => {
      ElMessage.info('已取消删除')
    })
}

const getStatusType = (status) => {
  const types = {
    '运行中': 'success',
    '等待中': 'info',
    '已完成': 'primary',
    '失败': 'danger'
  }
  return types[status] || 'info'
}
</script>

<style scoped>
.tasks {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h2 {
  margin: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 