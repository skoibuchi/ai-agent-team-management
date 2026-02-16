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
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  MenuItem,
} from '@mui/material'
import { Add, Build, PlayArrow, Info, AutoAwesome, Code } from '@mui/icons-material'
import { useStore } from '@/store'
import { api } from '@/services/api'
import type { Tool } from '@/types'

export default function Tools() {
  const { tools, loading, fetchTools } = useStore()
  const [testDialog, setTestDialog] = useState<{ open: boolean; tool: Tool | null }>({
    open: false,
    tool: null,
  })
  const [testParams, setTestParams] = useState<string>('{}')
  const [testResult, setTestResult] = useState<any>(null)
  const [testError, setTestError] = useState<string>('')
  
  // ツール生成ダイアログ（AI）
  const [generateDialog, setGenerateDialog] = useState(false)
  const [toolDescription, setToolDescription] = useState('')
  const [toolCategory, setToolCategory] = useState('custom')
  const [toolProvider, setToolProvider] = useState('')
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState('')
  const [llmProviders, setLlmProviders] = useState<Array<{provider: string, is_active: boolean}>>([])
  
  // ツール登録ダイアログ（手動）
  const [registerDialog, setRegisterDialog] = useState(false)
  const [toolCode, setToolCode] = useState('')
  const [registerCategory, setRegisterCategory] = useState('custom')
  const [registering, setRegistering] = useState(false)
  const [registerError, setRegisterError] = useState('')

  useEffect(() => {
    fetchTools()
    fetchLLMProviders()
  }, [fetchTools])

  const fetchLLMProviders = async () => {
    try {
      const response = await api.getLLMSettings()
      if (response.success) {
        setLlmProviders(response.data.filter((p: any) => p.is_active))
      }
    } catch (error) {
      console.error('Failed to fetch LLM providers:', error)
    }
  }

  const handleOpenTestDialog = (tool: Tool) => {
    setTestDialog({ open: true, tool })
    setTestParams('{}')
    setTestResult(null)
    setTestError('')
  }

  const handleCloseTestDialog = () => {
    setTestDialog({ open: false, tool: null })
    setTestParams('{}')
    setTestResult(null)
    setTestError('')
  }

  const handleTestTool = async () => {
    if (!testDialog.tool) return

    try {
      setTestError('')
      const params = JSON.parse(testParams)
      const response = await api.testTool(testDialog.tool.id, params)
      setTestResult(response.data)
    } catch (error: any) {
      setTestError(error.message || 'テスト実行に失敗しました')
    }
  }

  const handleOpenGenerateDialog = () => {
    setGenerateDialog(true)
    setToolDescription('')
    setToolCategory('custom')
    setToolProvider('')
    setGenerateError('')
  }

  const handleCloseGenerateDialog = () => {
    setGenerateDialog(false)
    setToolDescription('')
    setToolCategory('custom')
    setToolProvider('')
    setGenerateError('')
  }

  const handleGenerateTool = async () => {
    if (!toolDescription.trim()) {
      setGenerateError('ツールの説明を入力してください')
      return
    }

    try {
      setGenerating(true)
      setGenerateError('')
      
      const payload: any = {
        description: toolDescription,
        category: toolCategory,
      }
      if (toolProvider) {
        payload.provider = toolProvider
      }
      
      await api.generateTool(payload)
      
      // ツール一覧を再取得
      await fetchTools()
      
      handleCloseGenerateDialog()
    } catch (error: any) {
      setGenerateError(error.message || 'ツール生成に失敗しました')
    } finally {
      setGenerating(false)
    }
  }

  const handleOpenRegisterDialog = () => {
    setRegisterDialog(true)
    setToolCode('')
    setRegisterCategory('custom')
    setRegisterError('')
  }

  const handleCloseRegisterDialog = () => {
    setRegisterDialog(false)
    setToolCode('')
    setRegisterCategory('custom')
    setRegisterError('')
  }

  const handleRegisterTool = async () => {
    if (!toolCode.trim()) {
      setRegisterError('ツールコードを入力してください')
      return
    }

    try {
      setRegistering(true)
      setRegisterError('')
      
      await api.registerTool({
        code: toolCode,
        category: registerCategory,
      })
      
      // ツール一覧を再取得
      await fetchTools()
      
      handleCloseRegisterDialog()
    } catch (error: any) {
      setRegisterError(error.message || 'ツール登録に失敗しました')
    } finally {
      setRegistering(false)
    }
  }

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      research: '調査・検索',
      file_operations: 'ファイル操作',
      code: 'コード実行',
      api: 'API連携',
      mcp: 'MCP',
      general: '一般',
    }
    return labels[category] || category
  }

  const getCategoryColor = (category: string) => {
    const colors: Record<string, any> = {
      research: 'primary',
      file_operations: 'success',
      code: 'warning',
      api: 'info',
      mcp: 'secondary',
      general: 'default',
    }
    return colors[category] || 'default'
  }

  // カテゴリーごとにツールをグループ化
  const groupedTools = tools.reduce((acc, tool) => {
    const category = tool.category || 'general'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(tool)
    return acc
  }, {} as Record<string, Tool[]>)

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
        <Box>
          <Typography variant="h4">ツール</Typography>
          <Typography variant="body2" color="textSecondary" mt={1}>
            LangChain標準ツールとMCPツールを管理
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            startIcon={<AutoAwesome />}
            onClick={handleOpenGenerateDialog}
            color="primary"
          >
            AIでツール生成
          </Button>
          <Button
            variant="contained"
            startIcon={<Code />}
            onClick={handleOpenRegisterDialog}
            color="secondary"
          >
            コードで登録
          </Button>
          <Button
            variant="outlined"
            startIcon={<Add />}
            disabled
            title="MCPツール追加機能は準備中です"
          >
            MCPツールを追加（準備中）
          </Button>
        </Box>
      </Box>

      {tools.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <Build sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" gutterBottom>
                ツールがありません
              </Typography>
              <Typography variant="body2" color="textSecondary">
                システムの初期化中です
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Box>
          {Object.entries(groupedTools).map(([category, categoryTools]) => (
            <Box key={category} mb={4}>
              <Box display="flex" alignItems="center" mb={2}>
                <Typography variant="h6" sx={{ mr: 2 }}>
                  {getCategoryLabel(category)}
                </Typography>
                <Chip
                  label={`${categoryTools.length}個`}
                  size="small"
                  color={getCategoryColor(category)}
                />
              </Box>
              <Grid container spacing={3}>
                {categoryTools.map((tool) => (
                  <Grid item xs={12} sm={6} md={4} key={tool.name}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                          <Typography variant="h6" component="div">
                            {tool.name}
                          </Typography>
                          <Box>
                            {tool.is_builtin && (
                              <Chip
                                label="組み込み"
                                color="primary"
                                size="small"
                                sx={{ mr: 0.5 }}
                              />
                            )}
                            {tool.is_mcp && (
                              <Chip
                                label="MCP"
                                color="secondary"
                                size="small"
                              />
                            )}
                          </Box>
                        </Box>

                        <Typography variant="body2" color="textSecondary" paragraph>
                          {tool.description || '説明なし'}
                        </Typography>

                        <Box mt={2}>
                          <Chip
                            label={tool.is_active ? '有効' : '無効'}
                            color={tool.is_active ? 'success' : 'default'}
                            size="small"
                          />
                        </Box>
                      </CardContent>

                      <CardActions>
                        <IconButton
                          size="small"
                          color="primary"
                          title="ツール情報"
                        >
                          <Info />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="success"
                          title="テスト実行"
                          onClick={() => handleOpenTestDialog(tool)}
                        >
                          <PlayArrow />
                        </IconButton>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ))}
        </Box>
      )}

      {/* Test Dialog */}
      <Dialog open={testDialog.open} onClose={handleCloseTestDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          ツールテスト: {testDialog.tool?.name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Alert severity="info">
              ツールのパラメータをJSON形式で入力してください
            </Alert>
            
            <TextField
              label="パラメータ (JSON)"
              value={testParams}
              onChange={(e) => setTestParams(e.target.value)}
              fullWidth
              multiline
              rows={4}
              placeholder='{"query": "test", "num_results": 5}'
            />

            {testError && (
              <Alert severity="error">{testError}</Alert>
            )}

            {testResult && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  実行結果:
                </Typography>
                <TextField
                  value={JSON.stringify(testResult, null, 2)}
                  fullWidth
                  multiline
                  rows={8}
                  InputProps={{
                    readOnly: true,
                  }}
                />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTestDialog}>閉じる</Button>
          <Button
            onClick={handleTestTool}
            variant="contained"
            color="success"
          >
            テスト実行
          </Button>
        </DialogActions>
      </Dialog>

      {/* Generate Tool Dialog */}
      <Dialog open={generateDialog} onClose={handleCloseGenerateDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <AutoAwesome color="primary" />
            AIでツール生成
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Alert severity="info">
              作りたいツールを自然言語で説明してください。AIが自動的にツールを生成します。
            </Alert>
            
            <TextField
              label="ツールの説明"
              value={toolDescription}
              onChange={(e) => setToolDescription(e.target.value)}
              fullWidth
              multiline
              rows={6}
              placeholder="例: 指定されたURLからHTMLを取得して、タイトルとメタディスクリプションを抽出するツール"
              helperText="できるだけ具体的に、入力パラメータと期待される出力を含めて説明してください"
            />

            <Box display="flex" gap={2}>
              <TextField
                select
                label="カテゴリ"
                value={toolCategory}
                onChange={(e) => setToolCategory(e.target.value)}
                fullWidth
              >
                <MenuItem value="custom">カスタム</MenuItem>
                <MenuItem value="research">調査・検索</MenuItem>
                <MenuItem value="file_operations">ファイル操作</MenuItem>
                <MenuItem value="code">コード実行</MenuItem>
                <MenuItem value="api">API連携</MenuItem>
              </TextField>

              <TextField
                select
                label="LLMプロバイダー"
                value={toolProvider}
                onChange={(e) => setToolProvider(e.target.value)}
                fullWidth
                helperText="空欄の場合はデフォルトを使用"
              >
                <MenuItem value="">デフォルト</MenuItem>
                {llmProviders.map((p) => (
                  <MenuItem key={p.provider} value={p.provider}>
                    {p.provider.charAt(0).toUpperCase() + p.provider.slice(1)}
                  </MenuItem>
                ))}
              </TextField>
            </Box>

            {generateError && (
              <Alert severity="error">{generateError}</Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseGenerateDialog} disabled={generating}>
            キャンセル
          </Button>
          <Button
            onClick={handleGenerateTool}
            variant="contained"
            color="primary"
            disabled={generating || !toolDescription.trim()}
            startIcon={generating ? <CircularProgress size={20} /> : <AutoAwesome />}
          >
            {generating ? '生成中...' : 'ツールを生成'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Register Tool Dialog (Manual) */}
      <Dialog open={registerDialog} onClose={handleCloseRegisterDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Code color="secondary" />
            ツールコードを登録
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
            <Alert severity="info">
              LangChain標準のBaseToolを継承したPythonコードを入力してください。
            </Alert>
            
            <TextField
              label="ツールコード"
              value={toolCode}
              onChange={(e) => setToolCode(e.target.value)}
              fullWidth
              multiline
              rows={16}
              placeholder={`class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "My custom tool description"
    
    def _run(self, query: str) -> str:
        """Tool implementation"""
        # Your code here
        return "result"`}
              helperText="BaseToolを継承し、name、description、_runメソッドを実装してください"
              sx={{ fontFamily: 'monospace' }}
            />

            <TextField
              select
              label="カテゴリ"
              value={registerCategory}
              onChange={(e) => setRegisterCategory(e.target.value)}
              fullWidth
            >
              <MenuItem value="custom">カスタム</MenuItem>
              <MenuItem value="research">調査・検索</MenuItem>
              <MenuItem value="file_operations">ファイル操作</MenuItem>
              <MenuItem value="code">コード実行</MenuItem>
              <MenuItem value="api">API連携</MenuItem>
            </TextField>

            {registerError && (
              <Alert severity="error">{registerError}</Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseRegisterDialog} disabled={registering}>
            キャンセル
          </Button>
          <Button
            onClick={handleRegisterTool}
            variant="contained"
            color="secondary"
            disabled={registering || !toolCode.trim()}
            startIcon={registering ? <CircularProgress size={20} /> : <Code />}
          >
            {registering ? '登録中...' : 'ツールを登録'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
