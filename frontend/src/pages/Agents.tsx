import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Pagination,
  InputAdornment,
} from '@mui/material'
import { Add, Edit, Delete, SmartToy, Search } from '@mui/icons-material'
import { useStore } from '@/store'
import { api } from '@/services/api'
import type { Agent, Tool } from '@/types'

export default function Agents() {
  const { agents, loading, fetchAgents, addAgent, updateAgent, removeAgent } = useStore()
  const [openDialog, setOpenDialog] = useState(false)
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null)
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [loadingModels, setLoadingModels] = useState(false)
  const [configuredProviders, setConfiguredProviders] = useState<Array<{provider: string, default_model?: string}>>([])
  const [availableTools, setAvailableTools] = useState<Tool[]>([])
  const [toolSearchQuery, setToolSearchQuery] = useState<string>('')
  const [toolPage, setToolPage] = useState<number>(1)
  const toolsPerPage = 10
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    description: '',
    llm_provider: '',
    llm_model: '',
    tool_names: [] as string[],
    agent_type: 'worker' as 'worker' | 'supervisor',
    supervisor_id: undefined as number | undefined,
  })
  const [availableSupervisors, setAvailableSupervisors] = useState<Agent[]>([])

  useEffect(() => {
    fetchAgents()
    fetchConfiguredProviders()
    fetchAvailableTools()
    fetchAvailableSupervisors()
  }, [fetchAgents])

  // プロバイダーが変更されたらモデル一覧を取得
  useEffect(() => {
    if (formData.llm_provider && openDialog) {
      fetchAvailableModels(formData.llm_provider)
    }
  }, [formData.llm_provider, openDialog])

  const fetchConfiguredProviders = async () => {
    try {
      const response = await api.getLLMSettings()
      if (response.success && response.data) {
        // is_active=trueのプロバイダーのみ
        const activeProviders = response.data.filter((p: any) => p.is_active)
        setConfiguredProviders(activeProviders)
        
        // 初期値として最初のプロバイダーを設定
        if (activeProviders.length > 0 && !formData.llm_provider) {
          setFormData(prev => ({
            ...prev,
            llm_provider: activeProviders[0].provider
          }))
        }
      }
    } catch (error) {
      console.error('Failed to fetch configured providers:', error)
      setConfiguredProviders([])
    }
  }

  const fetchAvailableModels = async (provider: string) => {
    setLoadingModels(true)
    try {
      const response = await api.getAvailableModels(provider)
      if (response.success && response.data && Array.isArray(response.data)) {
        setAvailableModels(response.data)
        // モデルが未選択の場合、最初のモデルを選択
        if (!formData.llm_model && response.data.length > 0) {
          setFormData(prev => ({ ...prev, llm_model: response.data![0] }))
        }
      }
    } catch (error) {
      console.error('Failed to fetch available models:', error)
      setAvailableModels([])
    } finally {
      setLoadingModels(false)
    }
  }

  const fetchAvailableTools = async () => {
    try {
      const response = await api.getTools()
      if (response.success && response.data) {
        setAvailableTools(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch available tools:', error)
      setAvailableTools([])
    }
  }

  const fetchAvailableSupervisors = async () => {
    try {
      const response = await api.getSupervisors()
      if (response.success && response.data) {
        setAvailableSupervisors(response.data)
      }
    } catch (error) {
      console.error('Failed to fetch available supervisors:', error)
      setAvailableSupervisors([])
    }
  }

  const handleToggleTool = (toolName: string) => {
    setFormData(prev => ({
      ...prev,
      tool_names: prev.tool_names.includes(toolName)
        ? prev.tool_names.filter(name => name !== toolName)
        : [...prev.tool_names, toolName]
    }))
  }

  const handleToolSearchChange = (query: string) => {
    setToolSearchQuery(query)
    setToolPage(1) // Reset to first page on search
  }

  const getFilteredAndPaginatedTools = () => {
    let filtered = availableTools

    // Filter by search query
    if (toolSearchQuery) {
      const query = toolSearchQuery.toLowerCase()
      filtered = filtered.filter(tool =>
        tool.name.toLowerCase().includes(query) ||
        tool.description?.toLowerCase().includes(query) ||
        tool.category?.toLowerCase().includes(query)
      )
    }

    const totalCount = filtered.length
    const totalPages = Math.ceil(totalCount / toolsPerPage)
    const startIndex = (toolPage - 1) * toolsPerPage
    const endIndex = startIndex + toolsPerPage
    const tools = filtered.slice(startIndex, endIndex)

    return { tools, totalCount, totalPages }
  }

  const handleOpenDialog = (agent?: Agent) => {
    if (agent) {
      setEditingAgent(agent)
      setFormData({
        name: agent.name,
        role: agent.role || '',
        description: agent.description || '',
        llm_provider: agent.llm_provider,
        llm_model: agent.llm_model,
        tool_names: agent.tool_names || [],
        agent_type: agent.agent_type || 'worker',
        supervisor_id: agent.supervisor_id,
      })
    } else {
      setEditingAgent(null)
      const defaultProvider = configuredProviders.length > 0 ? configuredProviders[0].provider : ''
      setFormData({
        name: '',
        role: '',
        description: '',
        llm_provider: defaultProvider,
        llm_model: '',
        tool_names: ['human_input'], // デフォルトでhuman_inputツールを選択
        agent_type: 'worker',
        supervisor_id: undefined,
      })
    }
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingAgent(null)
  }

  const handleSubmit = async () => {
    try {
      if (editingAgent) {
        const response = await api.updateAgent(editingAgent.id, formData)
        if (response.data) {
          updateAgent(editingAgent.id, response.data)
        }
      } else {
        const response = await api.createAgent(formData)
        if (response.data) {
          addAgent(response.data)
        }
      }
      handleCloseDialog()
      fetchAgents()
    } catch (error) {
      console.error('Failed to save agent:', error)
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('このエージェントを削除してもよろしいですか？')) {
      try {
        await api.deleteAgent(id)
        removeAgent(id)
      } catch (error) {
        console.error('Failed to delete agent:', error)
      }
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success'
      case 'running':
        return 'primary'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'idle':
        return 'アイドル'
      case 'active':
        return 'アクティブ'
      case 'running':
        return '実行中'
      case 'error':
        return 'エラー'
      default:
        return status
    }
  }

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
        <Typography variant="h4">エージェント</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          新規作成
        </Button>
      </Box>

      {agents.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" gutterBottom>
                エージェントがありません
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={2}>
                新しいエージェントを作成して始めましょう
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => handleOpenDialog()}
              >
                エージェントを作成
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {agents.map((agent) => (
            <Grid item xs={12} sm={6} md={4} key={agent.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="h6" component="div">
                        {agent.name}
                      </Typography>
                      <Chip
                        label={agent.agent_type === 'supervisor' ? 'Supervisor' : 'Worker'}
                        color={agent.agent_type === 'supervisor' ? 'secondary' : 'default'}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                    <Chip
                      label={getStatusLabel(agent.status)}
                      color={getStatusColor(agent.status)}
                      size="small"
                    />
                  </Box>
                  
                  {agent.role && (
                    <Typography variant="body2" color="primary" gutterBottom>
                      役割: {agent.role}
                    </Typography>
                  )}
                  
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {agent.description || '説明なし'}
                  </Typography>
                  
                  {agent.agent_type === 'supervisor' && agent.workers_count !== undefined && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      👥 管理中のWorker: {agent.workers_count}名
                    </Typography>
                  )}
                  
                  {agent.agent_type === 'worker' && agent.supervisor && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      👤 Supervisor: {agent.supervisor.name}
                    </Typography>
                  )}
                  
                  <Box mt={2}>
                    <Typography variant="caption" color="textSecondary" display="block">
                      LLM: {agent.llm_provider} / {agent.llm_model}
                    </Typography>
                    <Typography variant="caption" color="textSecondary" display="block">
                      タスク: {agent.tasks_count} | ツール: {agent.tools_count}
                    </Typography>
                  </Box>
                </CardContent>
                
                <CardActions>
                  <IconButton
                    size="small"
                    onClick={() => handleOpenDialog(agent)}
                    color="primary"
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(agent.id)}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingAgent ? 'エージェントを編集' : '新しいエージェント'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="名前"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="役割"
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              fullWidth
              placeholder="例: データアナリスト、コンテンツライター"
            />
            <TextField
              label="説明"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <TextField
              label="エージェントタイプ"
              value={formData.agent_type}
              onChange={(e) => {
                const newType = e.target.value as 'worker' | 'supervisor'
                setFormData({
                  ...formData,
                  agent_type: newType,
                  supervisor_id: newType === 'supervisor' ? undefined : formData.supervisor_id
                })
              }}
              select
              fullWidth
              required
            >
              <MenuItem value="worker">Worker (タスク実行)</MenuItem>
              <MenuItem value="supervisor">Supervisor (チーム管理)</MenuItem>
            </TextField>
            {formData.agent_type === 'worker' && (
              <TextField
                label="スーパーバイザー"
                value={formData.supervisor_id || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  supervisor_id: e.target.value ? Number(e.target.value) : undefined
                })}
                select
                fullWidth
                helperText="このWorkerを管理するSupervisorを選択（任意）"
              >
                <MenuItem value="">なし</MenuItem>
                {availableSupervisors.map((supervisor) => (
                  <MenuItem key={supervisor.id} value={supervisor.id}>
                    {supervisor.name}
                  </MenuItem>
                ))}
              </TextField>
            )}
            <TextField
              label="LLMプロバイダー"
              value={formData.llm_provider}
              onChange={(e) => {
                setFormData({ ...formData, llm_provider: e.target.value, llm_model: '' })
              }}
              select
              fullWidth
              disabled={configuredProviders.length === 0}
              helperText={configuredProviders.length === 0 ? '設定画面でLLMプロバイダーを設定してください' : ''}
            >
              {configuredProviders.map((provider) => (
                <MenuItem key={provider.provider} value={provider.provider}>
                  {provider.provider === 'openai' && 'OpenAI'}
                  {provider.provider === 'anthropic' && 'Anthropic'}
                  {provider.provider === 'gemini' && 'Google Gemini'}
                  {provider.provider === 'watsonx' && 'IBM watsonx.ai'}
                  {provider.provider === 'ollama' && 'Ollama (ローカル)'}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="モデル"
              value={formData.llm_model}
              onChange={(e) => setFormData({ ...formData, llm_model: e.target.value })}
              select
              fullWidth
              disabled={loadingModels || availableModels.length === 0}
              helperText={loadingModels ? 'モデル一覧を読み込み中...' : ''}
            >
              {availableModels.map((model) => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </TextField>

            {/* Tool Selection Section */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                使用可能なツール ({formData.tool_names.length}個選択中)
              </Typography>
              <Typography variant="caption" color="textSecondary" gutterBottom display="block">
                未選択の場合は全てのツールが使用可能になります
              </Typography>

              {(() => {
                const { tools, totalCount, totalPages } = getFilteredAndPaginatedTools()
                return (
                  <Card variant="outlined" sx={{ mt: 1 }}>
                    <CardContent>
                      {/* 検索ボックス */}
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="ツール名、説明、カテゴリで検索..."
                        value={toolSearchQuery}
                        onChange={(e) => handleToolSearchChange(e.target.value)}
                        sx={{ mb: 2 }}
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
                            {tools.map((tool) => (
                              <ListItem
                                key={tool.name}
                                dense
                                button
                                onClick={() => handleToggleTool(tool.name)}
                              >
                                <ListItemIcon>
                                  <Checkbox
                                    edge="start"
                                    checked={formData.tool_names.includes(tool.name)}
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

                          {/* ページネーション */}
                          {totalPages > 1 && (
                            <Box display="flex" justifyContent="center" mt={2}>
                              <Pagination
                                count={totalPages}
                                page={toolPage}
                                onChange={(_, page) => setToolPage(page)}
                                size="small"
                              />
                            </Box>
                          )}
                        </>
                      ) : (
                        <Typography variant="body2" color="textSecondary" textAlign="center" py={2}>
                          {toolSearchQuery ? '検索結果がありません' : 'ツールがありません'}
                        </Typography>
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
            disabled={!formData.name || !formData.llm_provider || !formData.llm_model}
          >
            {editingAgent ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
