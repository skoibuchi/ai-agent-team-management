import { useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Chip,
  Switch,
  FormControlLabel,
} from '@mui/material'
import { Add, Edit, Delete, CheckCircle, Error as ErrorIcon } from '@mui/icons-material'
import { useStore } from '@/store'
import { api } from '@/services/api'
import type { LLMSetting } from '@/types'

const LLM_PROVIDERS = [
  { value: 'openai', label: 'OpenAI', description: 'GPT-4, GPT-3.5など' },
  { value: 'anthropic', label: 'Anthropic', description: 'Claude 3シリーズ' },
  { value: 'gemini', label: 'Google Gemini', description: 'Gemini Pro, Gemini 1.5など' },
  { value: 'watsonx', label: 'IBM watsonx.ai', description: 'エンタープライズAI' },
  { value: 'ollama', label: 'Ollama', description: 'ローカルLLM' },
]

export default function Settings() {
  const { llmSettings, loading, fetchLLMSettings, addLLMSetting, updateLLMSetting, removeLLMSetting } = useStore()
  const [openDialog, setOpenDialog] = useState(false)
  const [editingSetting, setEditingSetting] = useState<LLMSetting | null>(null)
  const [testingProvider, setTestingProvider] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [formData, setFormData] = useState({
    provider: 'openai',
    base_url: '',
    default_model: '',
    api_key: '',
    is_active: true,
    project_id: '', // watsonx用
  })

  useEffect(() => {
    fetchLLMSettings()
  }, [fetchLLMSettings])

  const handleOpenDialog = (setting?: LLMSetting) => {
    if (setting) {
      setEditingSetting(setting)
      setFormData({
        provider: setting.provider,
        base_url: setting.base_url || '',
        default_model: setting.default_model || '',
        api_key: '',
        is_active: setting.is_active,
        project_id: setting.config?.project_id || '',
      })
    } else {
      setEditingSetting(null)
      setFormData({
        provider: 'openai',
        base_url: '',
        default_model: '',
        api_key: '',
        is_active: true,
        project_id: '',
      })
    }
    setOpenDialog(true)
    setTestResult(null)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingSetting(null)
    setTestResult(null)
  }

  const handleSubmit = async () => {
    try {
      const data: any = {
        base_url: formData.base_url || undefined,
        default_model: formData.default_model || undefined,
        is_active: formData.is_active,
      }

      if (formData.api_key) {
        data.api_key = formData.api_key
      }

      // watsonx用のproject_idをconfigに追加
      if (formData.provider === 'watsonx' && formData.project_id) {
        data.config = {
          project_id: formData.project_id,
        }
      }

      if (editingSetting) {
        const response = await api.updateLLMSetting(editingSetting.provider, data)
        if (response.data) {
          updateLLMSetting(editingSetting.provider, response.data)
        }
      } else {
        data.provider = formData.provider
        const response = await api.createLLMSetting(data)
        if (response.data) {
          addLLMSetting(response.data)
        }
      }
      handleCloseDialog()
      fetchLLMSettings()
    } catch (error) {
      console.error('Failed to save LLM setting:', error)
      setTestResult({
        success: false,
        message: '設定の保存に失敗しました',
      })
    }
  }

  const handleDelete = async (provider: string) => {
    if (window.confirm('このLLM設定を削除してもよろしいですか？')) {
      try {
        await api.deleteLLMSetting(provider)
        removeLLMSetting(provider)
      } catch (error) {
        console.error('Failed to delete LLM setting:', error)
      }
    }
  }

  const handleTestConnection = async () => {
    if (!formData.provider) return

    setTestingProvider(formData.provider)
    setTestResult(null)

    try {
      // リクエストボディに設定を含める（保存前でもテスト可能）
      const testData: any = {}
      
      if (formData.api_key) {
        testData.api_key = formData.api_key
      }
      if (formData.base_url) {
        testData.base_url = formData.base_url
      }
      if (formData.default_model) {
        testData.default_model = formData.default_model
      }

      const response = await api.testLLMConnection(formData.provider, testData)
      setTestResult({
        success: true,
        message: '接続テストに成功しました',
      })
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error?.response?.data?.error || '接続テストに失敗しました',
      })
    } finally {
      setTestingProvider(null)
    }
  }

  const getProviderLabel = (provider: string) => {
    const p = LLM_PROVIDERS.find(p => p.value === provider)
    return p ? p.label : provider
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
        <Typography variant="h4">設定</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          LLM設定を追加
        </Button>
      </Box>

      <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 2 }}>
        LLMプロバイダー設定
      </Typography>

      {llmSettings.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                LLM設定がありません
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={2}>
                エージェントを使用するには、少なくとも1つのLLMプロバイダーを設定してください
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => handleOpenDialog()}
              >
                LLM設定を追加
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Box display="flex" flexDirection="column" gap={2}>
          {llmSettings.map((setting) => (
            <Card key={setting.provider}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start">
                  <Box flex={1}>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <Typography variant="h6">
                        {getProviderLabel(setting.provider)}
                      </Typography>
                      {setting.is_active ? (
                        <Chip label="有効" color="success" size="small" />
                      ) : (
                        <Chip label="無効" color="default" size="small" />
                      )}
                      {setting.has_api_key ? (
                        <Chip
                          icon={<CheckCircle />}
                          label="APIキー設定済み"
                          color="success"
                          size="small"
                          variant="outlined"
                        />
                      ) : (
                        <Chip
                          icon={<ErrorIcon />}
                          label="APIキー未設定"
                          color="warning"
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>

                    {setting.default_model && (
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        デフォルトモデル: {setting.default_model}
                      </Typography>
                    )}

                    {setting.base_url && (
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        ベースURL: {setting.base_url}
                      </Typography>
                    )}

                    <Typography variant="caption" color="textSecondary" display="block">
                      作成日: {new Date(setting.created_at).toLocaleString('ja-JP')}
                    </Typography>
                  </Box>

                  <Box display="flex" gap={1}>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(setting)}
                      color="primary"
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(setting.provider)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingSetting ? 'LLM設定を編集' : '新しいLLM設定'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="プロバイダー"
              value={formData.provider}
              onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
              select
              fullWidth
              disabled={!!editingSetting}
            >
              {LLM_PROVIDERS.map((provider) => (
                <MenuItem key={provider.value} value={provider.value}>
                  <Box>
                    <Typography variant="body1">{provider.label}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {provider.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </TextField>

            <TextField
              label="APIキー"
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              fullWidth
              placeholder={editingSetting ? '変更する場合のみ入力' : ''}
              helperText={
                formData.provider === 'ollama'
                  ? 'Ollamaの場合は不要です'
                  : 'プロバイダーのAPIキーを入力してください'
              }
            />

            <TextField
              label="ベースURL（オプション）"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              fullWidth
              placeholder="https://api.example.com"
              helperText={
                formData.provider === 'openai'
                  ? 'GitHub Models: https://models.inference.ai.azure.com, Azure OpenAI等のカスタムエンドポイント'
                  : formData.provider === 'watsonx'
                  ? 'リージョン別URL: US South (https://us-south.ml.cloud.ibm.com), EU Germany, JP Tokyo等'
                  : formData.provider === 'ollama'
                  ? 'Ollamaサーバーのアドレス（例: http://localhost:11434）'
                  : 'カスタムエンドポイントを使用する場合に指定'
              }
            />

            <TextField
              label="デフォルトモデル"
              value={formData.default_model}
              onChange={(e) => setFormData({ ...formData, default_model: e.target.value })}
              fullWidth
              placeholder={
                formData.provider === 'openai'
                  ? 'gpt-4, gpt-4o, gpt-3.5-turbo'
                  : formData.provider === 'anthropic'
                  ? 'claude-3-opus-20240229, claude-3-sonnet-20240229'
                  : formData.provider === 'gemini'
                  ? 'gemini-pro, gemini-1.5-pro, gemini-1.5-flash'
                  : formData.provider === 'watsonx'
                  ? 'ibm/granite-13b-chat-v2, meta-llama/llama-3-70b-instruct'
                  : formData.provider === 'ollama'
                  ? 'llama2, mistral, codellama'
                  : 'モデル名を入力'
              }
              helperText={
                formData.provider === 'openai'
                  ? 'GitHub Models使用時: gpt-4o, gpt-4o-mini, Phi-3-medium-128k-instruct等'
                  : formData.provider === 'gemini'
                  ? 'gemini-pro（標準）, gemini-1.5-pro（長文対応）, gemini-1.5-flash（高速）'
                  : formData.provider === 'watsonx'
                  ? 'Granite（IBM製）、Llama、Mistral等が利用可能'
                  : 'エージェント作成時に指定がない場合に使用されます'
              }
            />

            {/* watsonx用のProject IDフィールド */}
            {formData.provider === 'watsonx' && (
              <TextField
                label="Project ID（必須）"
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                fullWidth
                required
                placeholder="your-project-id-here"
                helperText="watsonx.aiプロジェクトのProject IDを入力してください"
              />
            )}

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="有効化"
            />

            {testResult && (
              <Alert severity={testResult.success ? 'success' : 'error'}>
                {testResult.message}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button
            onClick={handleTestConnection}
            disabled={testingProvider !== null}
            startIcon={testingProvider ? <CircularProgress size={16} /> : null}
          >
            接続テスト
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={!formData.provider}
          >
            {editingSetting ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
