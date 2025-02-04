<template>
  <div class="settings-container">
    <h2>系统设置</h2>
    <el-form :model="settings" label-width="120px">
      <el-form-item label="API地址">
        <el-input v-model="settings.apiUrl" placeholder="请输入API地址"></el-input>
      </el-form-item>
      <el-form-item label="代理设置">
        <el-switch v-model="settings.useProxy"></el-switch>
      </el-form-item>
      <el-form-item label="代理地址" v-if="settings.useProxy">
        <el-input v-model="settings.proxyUrl" placeholder="请输入代理地址"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const settings = ref({
  apiUrl: '',
  useProxy: false,
  proxyUrl: ''
})

const saveSettings = () => {
  // TODO: 实现保存设置的逻辑
  console.log('保存设置:', settings.value)
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
</style> 