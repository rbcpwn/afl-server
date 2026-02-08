<template>
  <div class="upload-container">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>上传测试文件</h2>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 白盒测试上传 -->
        <el-tab-pane label="白盒测试" name="whitebox">
          <div class="upload-section">
            <div class="section-desc">
              <el-alert
                title="白盒测试说明"
                type="info"
                :closable="false"
                show-icon
              >
                <p>上传C/C++源代码文件，AFL将通过编译插桩方式进行测试</p>
                <p>支持的文件类型：.c, .cpp, .cc, .cxx, .h, .hpp</p>
              </el-alert>
            </div>

            <el-form :model="whiteboxForm" label-width="120px">
              <el-form-item label="任务名称">
                <el-input
                  v-model="whiteboxForm.taskName"
                  placeholder="请输入任务名称"
                  clearable
                />
              </el-form-item>

              <el-form-item label="源代码文件">
                <el-upload
                  ref="sourceUploadRef"
                  class="upload-area"
                  drag
                  action="#"
                  :auto-upload="false"
                  :multiple="true"
                  :accept="'.c,.cpp,.cc,.cxx,.h,.hpp'"
                  :on-change="handleSourceChange"
                  :on-remove="handleSourceRemove"
                  :file-list="sourceFileList"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">
                    拖拽文件到此处或 <em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      支持上传多个C/C++源文件和头文件
                    </div>
                  </template>
                </el-upload>
              </el-form-item>

              <el-form-item label="主程序文件">
                <el-select
                  v-model="whiteboxForm.mainFile"
                  placeholder="请选择主程序文件（包含main函数的文件）"
                  style="width: 100%"
                  :disabled="sourceFileList.length === 0"
                >
                  <el-option
                    v-for="file in sourceFileList"
                    :key="file.uid"
                    :label="file.name"
                    :value="file.name"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="编译参数">
                <el-input
                  v-model="whiteboxForm.compileArgs"
                  placeholder="例如: -O2 -pthread"
                  clearable
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  :loading="uploading"
                  :disabled="!canUploadWhitebox"
                  @click="handleWhiteboxUpload"
                >
                  上传并创建任务
                </el-button>
                <el-button @click="resetWhiteboxForm">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 黑盒测试上传 -->
        <el-tab-pane label="黑盒测试" name="blackbox">
          <div class="upload-section">
            <div class="section-desc">
              <el-alert
                title="黑盒测试说明"
                type="info"
                :closable="false"
                show-icon
              >
                <p>上传编译好的ELF二进制文件，AFL将使用QEMU模式进行测试</p>
                <p>支持的文件类型：ELF可执行文件</p>
              </el-alert>
            </div>

            <el-form :model="blackboxForm" label-width="120px">
              <el-form-item label="任务名称">
                <el-input
                  v-model="blackboxForm.taskName"
                  placeholder="请输入任务名称"
                  clearable
                />
              </el-form-item>

              <el-form-item label="目标程序">
                <el-upload
                  ref="elfUploadRef"
                  class="upload-area"
                  drag
                  action="#"
                  :auto-upload="false"
                  :multiple="false"
                  :accept="''"
                  :on-change="handleElfChange"
                  :on-remove="handleElfRemove"
                  :file-list="elfFileList"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">
                    拖拽ELF文件到此处或 <em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      仅支持上传单个ELF可执行文件
                    </div>
                  </template>
                </el-upload>
              </el-form-item>

              <el-form-item label="输入类型">
                <el-select
                  v-model="blackboxForm.inputType"
                  placeholder="请选择输入类型"
                  style="width: 100%"
                >
                  <el-option label="标准输入 (stdin)" value="stdin" />
                  <el-option label="文件输入" value="file" />
                  <el-option label="命令行参数" value="args" />
                </el-select>
              </el-form-item>

              <el-form-item label="依赖库">
                <el-input
                  v-model="blackboxForm.dependencies"
                  type="textarea"
                  :rows="3"
                  placeholder="如有依赖库，请列出库名称（每行一个）"
                />
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  :loading="uploading"
                  :disabled="!canUploadBlackbox"
                  @click="handleBlackboxUpload"
                >
                  上传并创建任务
                </el-button>
                <el-button @click="resetBlackboxForm">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 种子文件上传 -->
        <el-tab-pane label="种子文件" name="seeds">
          <div class="upload-section">
            <div class="section-desc">
              <el-alert
                title="种子文件说明"
                type="success"
                :closable="false"
                show-icon
              >
                <p>上传初始种子文件，AFL将基于这些文件进行变异和测试</p>
                <p>种子文件质量越好，fuzz效率越高</p>
              </el-alert>
            </div>

            <el-form :model="seedsForm" label-width="120px">
              <el-form-item label="种子文件">
                <el-upload
                  ref="seedsUploadRef"
                  class="upload-area"
                  drag
                  action="#"
                  :auto-upload="false"
                  :multiple="true"
                  :on-change="handleSeedsChange"
                  :on-remove="handleSeedsRemove"
                  :file-list="seedsFileList"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">
                    拖拽文件到此处或 <em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      支持上传任意格式的种子文件
                    </div>
                  </template>
                </el-upload>
              </el-form-item>

              <el-form-item label="关联任务">
                <el-select
                  v-model="seedsForm.taskId"
                  placeholder="请选择要关联的fuzz任务（可选）"
                  style="width: 100%"
                  clearable
                >
                  <el-option
                    v-for="task in taskList"
                    :key="task.id"
                    :label="task.name"
                    :value="task.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  :loading="uploading"
                  :disabled="!canUploadSeeds"
                  @click="handleSeedsUpload"
                >
                  上传种子文件
                </el-button>
                <el-button @click="resetSeedsForm">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 上传进度对话框 -->
    <el-dialog
      v-model="uploadProgressDialog"
      title="上传进度"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-progress :percentage="uploadProgress" :status="uploadStatus" />
      <p style="margin-top: 16px; text-align: center">{{ uploadMessage }}</p>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadWhiteboxFiles, uploadBlackboxFile, uploadSeedFiles, getTasks } from '@/api/upload'

const router = useRouter()

const activeTab = ref('whitebox')
const uploading = ref(false)
const uploadProgressDialog = ref(false)
const uploadProgress = ref(0)
const uploadMessage = ref('')
const uploadStatus = ref('')

const sourceUploadRef = ref(null)
const elfUploadRef = ref(null)
const seedsUploadRef = ref(null)

const sourceFileList = ref([])
const elfFileList = ref([])
const seedsFileList = ref([])
const taskList = ref([])

const whiteboxForm = ref({
  taskName: '',
  mainFile: '',
  compileArgs: ''
})

const blackboxForm = ref({
  taskName: '',
  inputType: 'stdin',
  dependencies: ''
})

const seedsForm = ref({
  taskId: ''
})

const canUploadWhitebox = computed(() => {
  return whiteboxForm.value.taskName &&
         sourceFileList.value.length > 0 &&
         whiteboxForm.value.mainFile
})

const canUploadBlackbox = computed(() => {
  return blackboxForm.value.taskName &&
         elfFileList.value.length > 0
})

const canUploadSeeds = computed(() => {
  return seedsFileList.value.length > 0
})

const handleSourceChange = (file, fileList) => {
  const validExtensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp']
  const fileName = file.name.toLowerCase()
  const isValid = validExtensions.some(ext => fileName.endsWith(ext))

  if (!isValid) {
    ElMessage.error('只支持C/C++源文件和头文件')
    const index = fileList.indexOf(file)
    fileList.splice(index, 1)
    return
  }

  sourceFileList.value = fileList
}

const handleSourceRemove = (file, fileList) => {
  sourceFileList.value = fileList
  if (whiteboxForm.value.mainFile === file.name) {
    whiteboxForm.value.mainFile = ''
  }
}

const handleElfChange = (file, fileList) => {
  if (fileList.length > 1) {
    ElMessage.warning('只能上传一个ELF文件')
    fileList.pop()
    return
  }

  elfFileList.value = fileList
}

const handleElfRemove = (file, fileList) => {
  elfFileList.value = fileList
}

const handleSeedsChange = (file, fileList) => {
  seedsFileList.value = fileList
}

const handleSeedsRemove = (file, fileList) => {
  seedsFileList.value = fileList
}

const updateUploadProgress = (progress, message, status = '') => {
  uploadProgress.value = progress
  uploadMessage.value = message
  uploadStatus.value = status
}

const handleWhiteboxUpload = async () => {
  if (!canUploadWhitebox.value) {
    ElMessage.warning('请填写完整信息并上传源文件')
    return
  }

  uploading.value = true
  uploadProgressDialog.value = true
  updateUploadProgress(10, '正在准备上传...')

  try {
    updateUploadProgress(30, '正在上传源文件...')

    const formData = new FormData()
    sourceFileList.value.forEach(file => {
      formData.append('files', file.raw)
    })
    formData.append('taskName', whiteboxForm.value.taskName)
    formData.append('mainFile', whiteboxForm.value.mainFile)
    formData.append('compileArgs', whiteboxForm.value.compileArgs || '')

    updateUploadProgress(50, '正在创建白盒测试任务...')

    const response = await uploadWhiteboxFiles(formData)

    updateUploadProgress(80, '任务创建成功...')

    setTimeout(() => {
      updateUploadProgress(100, '上传完成！', 'success')
      uploading.value = false

      setTimeout(() => {
        uploadProgressDialog.value = false
        ElMessage.success('白盒测试任务创建成功！')
        resetWhiteboxForm()
        router.push(`/tasks?taskId=${response.data.taskId}`)
      }, 1000)
    }, 500)
  } catch (error) {
    updateUploadProgress(0, '上传失败：' + (error.message || '未知错误'), 'exception')
    uploading.value = false
    setTimeout(() => {
      uploadProgressDialog.value = false
    }, 2000)
  }
}

const handleBlackboxUpload = async () => {
  if (!canUploadBlackbox.value) {
    ElMessage.warning('请填写任务名称并上传ELF文件')
    return
  }

  uploading.value = true
  uploadProgressDialog.value = true
  updateUploadProgress(10, '正在准备上传...')

  try {
    updateUploadProgress(30, '正在上传ELF文件...')

    const formData = new FormData()
    formData.append('file', elfFileList.value[0].raw)
    formData.append('taskName', blackboxForm.value.taskName)
    formData.append('inputType', blackboxForm.value.inputType)
    formData.append('dependencies', blackboxForm.value.dependencies || '')

    updateUploadProgress(50, '正在创建黑盒测试任务...')

    const response = await uploadBlackboxFile(formData)

    updateUploadProgress(80, '任务创建成功...')

    setTimeout(() => {
      updateUploadProgress(100, '上传完成！', 'success')
      uploading.value = false

      setTimeout(() => {
        uploadProgressDialog.value = false
        ElMessage.success('黑盒测试任务创建成功！')
        resetBlackboxForm()
        router.push(`/tasks?taskId=${response.data.taskId}`)
      }, 1000)
    }, 500)
  } catch (error) {
    updateUploadProgress(0, '上传失败：' + (error.message || '未知错误'), 'exception')
    uploading.value = false
    setTimeout(() => {
      uploadProgressDialog.value = false
    }, 2000)
  }
}

const handleSeedsUpload = async () => {
  if (!canUploadSeeds.value) {
    ElMessage.warning('请上传至少一个种子文件')
    return
  }

  uploading.value = true
  uploadProgressDialog.value = true
  updateUploadProgress(10, '正在准备上传...')

  try {
    updateUploadProgress(30, '正在上传种子文件...')

    const formData = new FormData()
    seedsFileList.value.forEach(file => {
      formData.append('files', file.raw)
    })
    if (seedsForm.value.taskId) {
      formData.append('taskId', seedsForm.value.taskId)
    }

    updateUploadProgress(50, '正在处理种子文件...')

    await uploadSeedFiles(formData)

    updateUploadProgress(80, '种子文件处理完成...')

    setTimeout(() => {
      updateUploadProgress(100, '上传完成！', 'success')
      uploading.value = false

      setTimeout(() => {
        uploadProgressDialog.value = false
        ElMessage.success('种子文件上传成功！')
        resetSeedsForm()
      }, 1000)
    }, 500)
  } catch (error) {
    updateUploadProgress(0, '上传失败：' + (error.message || '未知错误'), 'exception')
    uploading.value = false
    setTimeout(() => {
      uploadProgressDialog.value = false
    }, 2000)
  }
}

const resetWhiteboxForm = () => {
  whiteboxForm.value = {
    taskName: '',
    mainFile: '',
    compileArgs: ''
  }
  sourceFileList.value = []
  sourceUploadRef.value?.clearFiles()
}

const resetBlackboxForm = () => {
  blackboxForm.value = {
    taskName: '',
    inputType: 'stdin',
    dependencies: ''
  }
  elfFileList.value = []
  elfUploadRef.value?.clearFiles()
}

const resetSeedsForm = () => {
  seedsForm.value = {
    taskId: ''
  }
  seedsFileList.value = []
  seedsUploadRef.value?.clearFiles()
}

const loadTasks = async () => {
  try {
    const response = await getTasks()
    taskList.value = response.data || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.upload-container {
  max-width: 1200px;
  margin: 0 auto;
}

.upload-card {
  min-height: 600px;
}

.card-header h2 {
  color: #303133;
  margin: 0;
}

.upload-section {
  padding: 24px 0;
}

.section-desc {
  margin-bottom: 24px;
}

.section-desc :deep(.el-alert__description) p {
  margin: 4px 0;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
}

:deep(.el-tabs__content) {
  padding: 24px;
}

.el-form-item {
  margin-bottom: 24px;
}
</style>
