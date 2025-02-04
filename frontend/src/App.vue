<template>
  <div class="app-container">
    <el-container>
      <el-header>
        <h1>爬虫工具</h1>
      </el-header>
      
      <el-container>
        <el-aside width="200px">
          <el-menu
            router
            :default-active="$route.path"
            class="el-menu-vertical">
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/tasks">
              <el-icon><List /></el-icon>
              <span>任务列表</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <span>设置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main>
          <router-view></router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { HomeFilled, List, Setting } from '@element-plus/icons-vue'
</script>

<style>
.app-container {
  height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
  text-align: center;
}

.el-aside {
  background-color: #f5f7fa;
}

.el-menu-vertical {
  border-right: none;
}

.el-main {
  padding: 20px;
}
</style> 