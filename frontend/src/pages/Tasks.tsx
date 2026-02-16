import { useEffect, useState, useCallback, useRef } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  LinearProgress,
  Tabs,
  Tab,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  Pagination,
  InputAdornment,
} from '@mui/material'
import { Add, PlayArrow, Cancel, Delete, Assignment, Build, Search, Visibility } from '@mui/icons-material'
import { useStore } from '@/store'
import { api } from '@/services/api'
import type { Task } from '@/types'
import TaskExecutionDialog from '@/components/TaskExecutionDialog'

export default function Tasks() {
  const { tasks, agents, loading, fetchTasks, fetchAgents, addTask, updateTask, removeTask } = useStore()
  const [openDialog, setOpenDialog] = useState(false)
  const [selectedTab, setSelectedTab] = useState(0)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    assigned_to: '',
    mode: 'manual' as 'manual' | 'auto' | 'team',
  })
  const [analyzingTask, setAnalyzingTask] = useState(false)
  const [recommendedTools, setRecommendedTools] = useState<any[]>([])
  const [selectedTools, setSelectedTools] = useState<string[]>([])
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [llmSettings, setLlmSettings] = useState<any[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [executionDialogOpen, setExecutionDialogOpen] = useState(false)
  const [selectedTaskForExecution, setSelectedTaskForExecution] = useState<Task | null>(null)
  const [analysisError, setAnalysisError] = useState<string>('')
  const [allTools, setAllTools] = useState<any[]>([])
  const [showManualToolSelection, setShowManualToolSelection] = useState(false)
  const [toolSearchQuery, setToolSearchQuery] = useState<string>('')
  const [toolPage, setToolPage] = useState<number>(1)
  const toolsPerPage = 10
  const [lastUpdateTime, setLastUpdateTime] = useState<string | null>(null)

  // 初回データ取得
  useEffect(() => {
    fetchTasks()
    fetchAgents()
    fetchLLMSettings()
    fetchAllTools()
    // 初回取得時に現在時刻を記録
    setLastUpdateTime(new Date().toISOString())
  }, [fetchTasks, fetchAgents])

  // 差分取得のポーリング
  useEffect(() => {
    // 全てのタスクが完了または失敗の場合のみポーリングを停止
    // pending（待機中）のタスクがある場合は、実行開始を検知するためにポーリングを継続
    const allTasksCompleted = tasks.length > 0 && tasks.every(task => {
      const status = task.detailed_status || task.status
      return status === 'completed' || status === 'failed' || status === 'cancelled'
    })

    if (allTasksCompleted) {
      console.log('[Tasks] All tasks are completed/failed/cancelled, stopping polling')
      return
    }

    console.log('[Tasks] Starting polling for task updates')

    const fetchUpdatedTasks = async () => {
      if (!lastUpdateTime) return

      try {
        const response = await api.getTasks({ updated_since: lastUpdateTime })
        if (response.data && response.data.length > 0) {
          console.log(`[Tasks] Received ${response.data.length} updated tasks`)
          // 更新されたタスクをマージ
          response.data.forEach(updatedTask => {
            updateTask(updatedTask.id, updatedTask)
          })
          // 最終更新時刻を更新
          setLastUpdateTime(new Date().toISOString())
        }
      } catch (error) {
        console.error('Failed to fetch updated tasks:', error)
      }
    }

    // 3秒ごとにポーリング
    const interval = setInterval(fetchUpdatedTasks, 3000)

    return () => {
      console.log('[Tasks] Stopping polling')
      clearInterval(interval)
    }
  }, [tasks, lastUpdateTime, updateTask])

  const fetchAllTools = async () => {
    try {
      const response = await api.getTools()
      if (response.data) {
        setAllTools(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch tools:', error)
    }
  }

  const fetchLLMSettings = async () => {
    try {
      const response = await api.getLLMSettings()
      if (response.data) {
        setLlmSettings(response.data)
        // デフォルトでアクティブな設定を選択
        const activeSetting = response.data.find((s: any) => s.is_active)
        if (activeSetting) {
          setSelectedProvider(activeSetting.provider)
        }
      }
    } catch (error) {
      console.error('Failed to fetch LLM settings:', error)
    }
  }

  const handleOpenDialog = () => {
    setFormData({
      title: '',
      description: '',
      priority: 'medium',
      assigned_to: '',
      mode: 'manual',
    })
    setRecommendedTools([])
    setSelectedTools([])
    setAnalysisResult(null)
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setRecommendedTools([])
    setSelectedTools([])
    setAnalysisResult(null)
  }

  const handleAnalyzeTask = async () => {
    if (!formData.description) {
      return
    }

    setAnalyzingTask(true)
    setAnalysisError('')
    try {
      const response = await api.recommendToolsForTask({
        task_description: formData.description,
        provider: selectedProvider || undefined,
      })
      
      if (response.data) {
        setAnalysisResult(response.data.analysis)
        setRecommendedTools(response.data.tools || [])
        // デフォルトで推奨ツールを選択状態にする
        setSelectedTools(response.data.tools?.map((t: any) => t.name) || [])
      }
    } catch (error: any) {
      console.error('Failed to analyze task:', error)
      const errorMessage = error.response?.data?.error || error.message || 'タスク分析に失敗しました'
      setAnalysisError(errorMessage)
    } finally {
      setAnalyzingTask(false)
    }
  }

  const handleToggleTool = (toolName: string) => {
    setSelectedTools(prev =>
      prev.includes(toolName)
        ? prev.filter(t => t !== toolName)
        : [...prev, toolName]
    )
  }

  const handleSubmit = async () => {
    try {
      const taskData: any = {
        title: formData.title,
        description: formData.description,
        priority: formData.priority,
        mode: formData.mode,
      }
      
      if (formData.assigned_to) {
        taskData.assigned_to = parseInt(formData.assigned_to)
      }

      // 選択されたツールをadditional_tool_namesとして保存
      if (selectedTools.length > 0) {
        taskData.additional_tool_names = selectedTools
      }

      // 分析結果もメタデータとして保存
      if (analysisResult) {
        taskData.metadata = {
          analysis: analysisResult,
        }
      }

      const response = await api.createTask(taskData)
      if (response.data) {
        addTask(response.data)
      }
      handleCloseDialog()
      fetchTasks()
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  const handleExecute = async (taskId: number) => {
    try {
      await api.executeTask(taskId)
      fetchTasks()
    } catch (error) {
      console.error('Failed to execute task:', error)
    }
  }

  const handleCancel = async (taskId: number) => {
    try {
      await api.cancelTask(taskId)
      fetchTasks()
    } catch (error) {
      console.error('Failed to cancel task:', error)
    }
  }

  const handleDelete = async (taskId: number) => {
    if (window.confirm('このタスクを削除してもよろしいですか？')) {
      try {
        await api.deleteTask(taskId)
        removeTask(taskId)
      } catch (error) {
        console.error('Failed to delete task:', error)
      }
    }
  }

  const getStatusColor = (detailedStatus: string) => {
    switch (detailedStatus) {
      case 'completed':
        return 'success'
      case 'running':
        return 'primary'
      case 'waiting_input':
        return 'info'
      case 'waiting_approval':
        return 'warning'
      case 'failed':
        return 'error'
      case 'pending':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStatusLabel = (detailedStatus: string) => {
    switch (detailedStatus) {
      case 'pending':
        return '待機中'
      case 'running':
        return '実行中'
      case 'waiting_input':
        return '入力待ち'
      case 'waiting_approval':
        return '承認待ち'
      case 'completed':
        return '完了'
      case 'failed':
        return '失敗'
      default:
        return detailedStatus
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error'
      case 'medium':
        return 'warning'
      case 'low':
        return 'info'
      default:
        return 'default'
    }
  }

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case 'high':
        return '高'
      case 'medium':
        return '中'
      case 'low':
        return '低'
      default:
        return priority
    }
  }

  const filterTasks = (detailedStatus?: string) => {
    if (!detailedStatus) return tasks
    return tasks.filter(task => (task.detailed_status || task.status) === detailedStatus)
  }

  // ツールのフィルタリングとページネーション
  const getFilteredAndPaginatedTools = () => {
    // 検索フィルター
    let filtered = allTools.filter(tool => {
      const searchLower = toolSearchQuery.toLowerCase()
      return (
        tool.name.toLowerCase().includes(searchLower) ||
        tool.description?.toLowerCase().includes(searchLower) ||
        tool.category?.toLowerCase().includes(searchLower)
      )
    })

    // ページネーション
    const startIndex = (toolPage - 1) * toolsPerPage
    const endIndex = startIndex + toolsPerPage
    const paginated = filtered.slice(startIndex, endIndex)

    return {
      tools: paginated,
      totalCount: filtered.length,
      totalPages: Math.ceil(filtered.length / toolsPerPage)
    }
  }

  const handleToolSearchChange = (query: string) => {
    setToolSearchQuery(query)
    setToolPage(1) // 検索時はページを1にリセット
  }

  const tabLabels = [
    { label: 'すべて', status: undefined },
    { label: '待機中', status: 'pending' },
    { label: '実行中', status: 'running' },
    { label: '入力待ち', status: 'waiting_input' },
    { label: '承認待ち', status: 'waiting_approval' },
    { label: '完了', status: 'completed' },
    { label: '失敗', status: 'failed' },
  ]

  const currentTasks = filterTasks(tabLabels[selectedTab].status)

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">タスク</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleOpenDialog}
        >
          新規作成
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={selectedTab} onChange={(_, newValue) => setSelectedTab(newValue)}>
          {tabLabels.map((tab, index) => (
            <Tab key={index} label={tab.label} />
          ))}
        </Tabs>
      </Box>

      {currentTasks.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <Assignment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" gutterBottom>
                タスクがありません
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={2}>
                新しいタスクを作成して始めましょう
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleOpenDialog}
              >
                タスクを作成
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Box display="flex" flexDirection="column" gap={2}>
          {currentTasks.map((task) => (
            <Card key={task.id}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                  <Box flex={1}>
                    <Typography variant="h6" gutterBottom>
                      {task.title}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      {task.description}
                    </Typography>
                  </Box>
                  <Box display="flex" gap={1} ml={2}>
                    <Chip
                      label={getStatusLabel(task.detailed_status || task.status)}
                      color={getStatusColor(task.detailed_status || task.status)}
                      size="small"
                    />
                    <Chip
                      label={getPriorityLabel(task.priority)}
                      color={getPriorityColor(task.priority)}
                      size="small"
                    />
                  </Box>
                </Box>

                {task.status === 'running' && (
                  <Box mb={2}>
                    <LinearProgress />
                  </Box>
                )}

                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    {task.agent && (
                      <Typography variant="caption" color="textSecondary" display="block">
                        担当: {task.agent.name}
                      </Typography>
                    )}
                    <Typography variant="caption" color="textSecondary" display="block">
                      モード: {task.mode === 'manual' ? '手動' : task.mode === 'auto' ? '自動' : 'チーム'}
                    </Typography>
                    <Typography variant="caption" color="textSecondary" display="block">
                      作成: {new Date(task.created_at).toLocaleString('ja-JP')}
                    </Typography>
                  </Box>
                  <Box display="flex" gap={1}>
                    {(task.status === 'running' || task.status === 'completed' || task.status === 'failed') && (
                      <IconButton
                        size="small"
                        color="info"
                        onClick={() => {
                          setSelectedTaskForExecution(task)
                          setExecutionDialogOpen(true)
                        }}
                        title="ログを表示"
                      >
                        <Visibility />
                      </IconButton>
                    )}
                    {task.status === 'pending' && (
                      <>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleExecute(task.id)}
                          title="実行"
                        >
                          <PlayArrow />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(task.id)}
                          title="削除"
                        >
                          <Delete />
                        </IconButton>
                      </>
                    )}
                    {task.status === 'running' && (
                      <IconButton
                        size="small"
                        color="warning"
                        onClick={() => handleCancel(task.id)}
                        title="キャンセル"
                      >
                        <Cancel />
                      </IconButton>
                    )}
                    {(task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') && (
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(task.id)}
                        title="削除"
                      >
                        <Delete />
                      </IconButton>
                    )}
                  </Box>
                </Box>

                {task.error_message && (
                  <Box
                    mt={2}
                    p={2}
                    bgcolor="#fff3f3"
                    border="1px solid #ffcdd2"
                    borderRadius={1}
                  >
                    <Typography variant="body2" color="#c62828" fontWeight={500}>
                      ⚠️ エラー: {task.error_message}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      {/* Create Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>新しいタスク</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="タイトル"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="説明"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={4}
              required
            />
            <TextField
              label="優先度"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
              select
              fullWidth
            >
              <MenuItem value="low">低</MenuItem>
              <MenuItem value="medium">中</MenuItem>
              <MenuItem value="high">高</MenuItem>
            </TextField>
            <TextField
              label="モード"
              value={formData.mode}
              onChange={(e) => setFormData({ ...formData, mode: e.target.value as any })}
              select
              fullWidth
            >
              <MenuItem value="manual">手動 - エージェントを指定</MenuItem>
              <MenuItem value="auto">自動 - システムが選択</MenuItem>
              <MenuItem value="team">チーム - 複数エージェント</MenuItem>
            </TextField>
            {formData.mode === 'manual' && (
              <TextField
                label="担当エージェント"
                value={formData.assigned_to}
                onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                select
                fullWidth
              >
                <MenuItem value="">未割り当て</MenuItem>
                {agents.map((agent) => (
                  <MenuItem key={agent.id} value={agent.id.toString()}>
                    {agent.name} ({agent.role || '役割なし'})
                  </MenuItem>
                ))}
              </TextField>
            )}

            {/* Task Analysis Section */}
            {formData.description && (
              <Box sx={{ mt: 2 }}>
                <TextField
                  label="LLMプロバイダー"
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  select
                  fullWidth
                  size="small"
                  sx={{ mb: 2 }}
                  helperText="タスク分析に使用するLLMを選択してください"
                >
                  {llmSettings.map((setting) => (
                    <MenuItem key={setting.provider} value={setting.provider}>
                      {setting.provider.toUpperCase()} {setting.is_active ? '(アクティブ)' : ''}
                    </MenuItem>
                  ))}
                </TextField>

                <Button
                  variant="outlined"
                  startIcon={<Build />}
                  onClick={handleAnalyzeTask}
                  disabled={analyzingTask || !selectedProvider}
                  fullWidth
                >
                  {analyzingTask ? 'タスクを分析中...' : 'タスクを分析してツールを推奨'}
                </Button>

                {analysisError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    {analysisError}
                  </Alert>
                )}

                {analysisResult && (
                  <Box sx={{ mt: 2 }}>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        タスク分析結果
                      </Typography>
                      <Typography variant="body2">
                        {analysisResult.summary}
                      </Typography>
                    </Alert>

                    {recommendedTools.length > 0 && (
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom>
                            推奨ツール ({recommendedTools.length}個)
                          </Typography>
                          <List dense>
                            {recommendedTools.map((tool: any) => (
                              <ListItem
                                key={tool.name}
                                dense
                                button
                                onClick={() => handleToggleTool(tool.name)}
                              >
                                <ListItemIcon>
                                  <Checkbox
                                    edge="start"
                                    checked={selectedTools.includes(tool.name)}
                                    tabIndex={-1}
                                    disableRipple
                                  />
                                </ListItemIcon>
                                <ListItemText
                                  primary={tool.name}
                                  secondary={tool.description}
                                />
                              </ListItem>
                            ))}
                          </List>
                          <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                            選択したツールはエージェントが使用できるようになります
                          </Typography>
                        </CardContent>
                      </Card>
                    )}
                  </Box>
                )}
              </Box>
            )}

            {/* Manual Tool Selection */}
            <Box sx={{ mt: 3 }}>
              <Button
                variant="text"
                onClick={() => setShowManualToolSelection(!showManualToolSelection)}
                fullWidth
              >
                {showManualToolSelection ? '手動ツール選択を閉じる' : '手動でツールを選択'}
              </Button>

              {showManualToolSelection && (() => {
                const { tools, totalCount, totalPages } = getFilteredAndPaginatedTools()
                return (
                  <Card variant="outlined" sx={{ mt: 2 }}>
                    <CardContent>
                      <Typography variant="subtitle2" gutterBottom>
                        利用可能なツール ({totalCount}個)
                      </Typography>
                      <Typography variant="caption" color="textSecondary" gutterBottom display="block">
                        タスクに必要なツールを選択してください
                      </Typography>

                      {/* 検索ボックス */}
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="ツール名、説明、カテゴリで検索..."
                        value={toolSearchQuery}
                        onChange={(e) => handleToolSearchChange(e.target.value)}
                        sx={{ mt: 2, mb: 2 }}
                        InputProps={{
                          startAdornment: (
                            <InputAdornment position="start">
                              <Search />
                            </InputAdornment>
                          ),
                        }}
                      />

                      {/* ツールリスト */}
                      {tools.length > 0 ? (
                        <>
                          <List dense>
                            {tools.map((tool: any) => (
                              <ListItem
                                key={tool.name}
                                dense
                                button
                                onClick={() => handleToggleTool(tool.name)}
                              >
                                <ListItemIcon>
                                  <Checkbox
                                    edge="start"
                                    checked={selectedTools.includes(tool.name)}
                                    tabIndex={-1}
                                    disableRipple
                                  />
                                </ListItemIcon>
                                <ListItemText
                                  primary={tool.name}
                                  secondary={
                                    <>
                                      {tool.description}
                                      {tool.category && (
                                        <Chip
                                          label={tool.category}
                                          size="small"
                                          sx={{ ml: 1, height: 20 }}
                                        />
                                      )}
                                    </>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>

                          {/* ページネーション */}
                          {totalPages > 1 && (
                            <Box display="flex" justifyContent="center" mt={2}>
                              <Pagination
                                count={totalPages}
                                page={toolPage}
                                onChange={(_, page) => setToolPage(page)}
                                color="primary"
                                size="small"
                              />
                            </Box>
                          )}
                        </>
                      ) : (
                        <Alert severity="info" sx={{ mt: 2 }}>
                          検索条件に一致するツールが見つかりません
                        </Alert>
                      )}

                      {selectedTools.length > 0 && (
                        <Alert severity="success" sx={{ mt: 2 }}>
                          {selectedTools.length}個のツールが選択されています
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                )
              })()}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.title || !formData.description}
          >
            作成
          </Button>
        </DialogActions>
      </Dialog>

      {/* タスク実行ログダイアログ */}
      <TaskExecutionDialog
        open={executionDialogOpen}
        task={selectedTaskForExecution}
        onClose={() => {
          setExecutionDialogOpen(false)
          setSelectedTaskForExecution(null)
        }}
      />
    </Box>
  )
}
