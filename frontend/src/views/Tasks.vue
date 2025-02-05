<template>
  <div class="tasks">
    <h2>任务列表</h2>
    <div class="task-list">
      <div class="task-item" v-for="task in tasks" :key="task.id">
        <div class="task-info">
          <h3>{{ task.name }}</h3>
          <p>状态: {{ task.status }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Tasks',
  data() {
    return {
      tasks: []
    }
  }
}
</script>

<style scoped>
.tasks {
  padding: 20px;
}

.task-list {
  margin-top: 20px;
}

.task-item {
  background: #fff;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-info h3 {
  margin: 0;
  color: #2c3e50;
}

.task-info p {
  margin: 5px 0 0;
  color: #666;
}
</style>
