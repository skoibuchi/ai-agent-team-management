import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Paper,
  Chip,
  Divider,
  TextField,
  IconButton,
  Switch,
  FormControlLabel,
  CircularProgress,
} from '@mui/material'
import {
  Psychology as ThinkingIcon,
  Build as ToolIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  HelpOutline as QuestionIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { Task } from '../types'
import { TaskInteraction, InteractionType } from '../types/interaction'
import api from '../services/api'
// import websocketService from '../services/websocket'

interface TaskExecutionDialogProps {
  open: boolean
  task: Task | null
  onClose: () => void
}

// インタラクションリストを別コンポーネントに分離（React.memoで最適化）
const InteractionList = React.memo<{ interactions: TaskInteraction[] }>(({ interactions }) => {
  const getInteractionIcon = (type: InteractionType) => {
    switch (type) {
      case 'agent_thinking':
        return <ThinkingIcon color="primary" />
      case 'tool_call':
        return <ToolIcon color="secondary" />
      case 'tool_result':
        return <CheckCircleIcon color="success" />
      case 'error':
        return <ErrorIcon color="error" />
      case 'result':
        return <CheckCircleIcon color="success" />
      case 'question':
        return <QuestionIcon color="warning" />
      case 'user_response':
        return <SendIcon color="info" />
      default:
        return <InfoIcon color="info" />
    }
  }

  const getInteractionColor = (type: InteractionType) => {
    switch (type) {
      case 'agent_thinking':
        return 'primary'
      case 'tool_call':
        return 'secondary'
      case 'tool_result':
        return 'success'
      case 'error':
        return 'error'
      case 'result':
        return 'success'
      default:
        return 'default'
    }
  }

  const getInteractionLabel = (type: InteractionType) => {
    switch (type) {
      case 'agent_thinking':
        return 'エージェントの思考'
      case 'tool_call':
        return 'ツール呼び出し'
      case 'tool_result':
        return 'ツール実行結果'
      case 'error':
        return 'エラー'
      case 'result':
        return '最終結果'
      case 'question':
        return '質問'
      case 'user_response':
        return 'ユーザー応答'
      default:
        return '情報'
    }
  }

  if (interactions.length === 0) {
    return (
      <Typography color="text.secondary" align="center">
        実行ログがありません
      </Typography>
    )
  }

  return (
    <>
      {interactions.map((interaction) => (
        <Paper
          key={interaction.id}
          elevation={1}
          sx={{
            p: 2,
            mb: 2,
            borderLeft: 4,
            borderColor: `${getInteractionColor(interaction.interaction_type)}.main`,
          }}
        >
          <Box display="flex" alignItems="center" mb={1}>
            {getInteractionIcon(interaction.interaction_type)}
            <Chip
              label={getInteractionLabel(interaction.interaction_type)}
              color={getInteractionColor(interaction.interaction_type) as any}
              size="small"
              sx={{ ml: 1 }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
              {new Date(interaction.created_at).toLocaleTimeString('ja-JP')}
            </Typography>
          </Box>

          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {interaction.content}
          </Typography>

          {/* メタデータ表示（ツール呼び出しの場合） */}
          {interaction.interaction_type === 'tool_call' && interaction.metadata?.tool_calls && (
            <Box mt={2}>
              <Divider sx={{ mb: 1 }} />
              <Typography variant="caption" color="text.secondary">
                ツール詳細:
              </Typography>
              {interaction.metadata.tool_calls.map((tc: any, idx: number) => (
                <Box key={idx} sx={{ mt: 1, pl: 2 }}>
                  <Typography variant="body2">
                    <strong>{tc.name}</strong>
                  </Typography>
                  <Typography variant="caption" component="pre" sx={{ fontSize: '0.75rem' }}>
                    {JSON.stringify(tc.args, null, 2)}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}

          {/* ツール名表示（ツール結果の場合） */}
          {interaction.interaction_type === 'tool_result' && interaction.metadata?.tool_name && (
            <Box mt={1}>
              <Typography variant="caption" color="text.secondary">
                ツール: {interaction.metadata.tool_name}
              </Typography>
            </Box>
          )}
        </Paper>
      ))}
    </>
  )
})

InteractionList.displayName = 'InteractionList'

const TaskExecutionDialog: React.FC<TaskExecutionDialogProps> = ({ open, task, onClose }) => {
  const [interactions, setInteractions] = useState<TaskInteraction[]>([])
  const [loading, setLoading] = useState(false)
  const [responseText, setResponseText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [autoMode, setAutoMode] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)
  const prevInteractionsLengthRef = useRef(0)

  // モード切り替えハンドラー
  const handleToggleAutoMode = async () => {
    if (!task) return
    
    try {
      await api.toggleTaskAutoMode(task.id)
      setAutoMode(!autoMode)
    } catch (error) {
      console.error('Failed to toggle auto mode:', error)
      alert('モード切り替えに失敗しました')
    }
  }

  // 応答が必要なインタラクションを取得
  const getPendingQuestion = (): TaskInteraction | null => {
    return interactions.find(i => i.interaction_type === 'question' && !i.response) || null
  }

  // 応答送信またはメッセージ送信
  const handleSubmitResponse = async () => {
    if (!task || !responseText.trim()) return
    
    const pendingQuestion = getPendingQuestion()

    try {
      setSubmitting(true)
      
      if (pendingQuestion) {
        // 質問への応答
        await api.respondToInteraction(task.id, pendingQuestion.id, { response: responseText })
      } else {
        // 自由なメッセージ送信
        await api.sendUserMessage(task.id, responseText)
      }
      
      setResponseText('')
      // インタラクションを再取得
      await fetchInteractions()
    } catch (error) {
      console.error('Failed to send message:', error)
      alert('メッセージの送信に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  // インタラクション履歴を取得（初回は全件、以降は差分のみ）
  const fetchInteractions = useCallback(async () => {
    if (!task) return

    try {
      setLoading(true)
      const response = await api.getTaskInteractions(task.id)
      setInteractions(response.interactions)
    } catch (error) {
      console.error('Failed to fetch interactions:', error)
    } finally {
      setLoading(false)
    }
  }, [task])

  // 差分のみを取得（ポーリング用）
  const fetchNewInteractions = useCallback(async () => {
    if (!task || interactions.length === 0) return

    try {
      const lastId = interactions[interactions.length - 1]?.id
      if (!lastId) return

      const response = await api.getTaskInteractions(task.id, { since: lastId })
      if (response.interactions && response.interactions.length > 0) {
        setInteractions(prev => [...prev, ...response.interactions])
      }
    } catch (error) {
      console.error('Failed to fetch new interactions:', error)
    }
  }, [task, interactions])

  // 初回読み込み
  useEffect(() => {
    if (!open || !task) {
      setInteractions([])
      return
    }

    fetchInteractions()
  }, [open, task, fetchInteractions])

  // ポーリング（タスク実行中のみ、3秒ごとに差分取得）
  useEffect(() => {
    if (!open || !task || task.status !== 'running') return

    const interval = setInterval(() => {
      fetchNewInteractions()
    }, 3000) // 3秒ごと

    return () => clearInterval(interval)
  }, [open, task, fetchNewInteractions])

  // スクロール位置の監視
  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
    // 下から50px以内にいる場合は自動スクロールを有効化
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 50
    setShouldAutoScroll(isNearBottom)
  }, [])

  // 自動スクロール（新しいインタラクションが追加されたとき、かつユーザーが下部にいる場合のみ）
  useEffect(() => {
    if (interactions.length > prevInteractionsLengthRef.current && shouldAutoScroll && scrollRef.current) {
      // requestAnimationFrameを使用してスムーズにスクロール
      requestAnimationFrame(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
      })
    }
    prevInteractionsLengthRef.current = interactions.length
  }, [interactions.length, shouldAutoScroll])

  // タスク情報の取得
  useEffect(() => {
    if (task) {
      setAutoMode(task.auto_mode || false)
    }
  }, [task])

  if (!task) return null

  const pendingQuestion = getPendingQuestion()

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">タスク実行ログ</Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoMode}
                  onChange={handleToggleAutoMode}
                  color="primary"
                />
              }
              label={autoMode ? '自動モード' : '対話モード'}
            />
            <IconButton onClick={fetchInteractions} size="small" title="手動更新">
              <RefreshIcon />
            </IconButton>
          </Box>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {task.title}
        </Typography>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0, display: 'flex', flexDirection: 'column', height: '70vh' }}>
        {/* メッセージ表示エリア */}
        <Box
          ref={scrollRef}
          onScroll={handleScroll}
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 2,
          }}
        >
          {loading && interactions.length === 0 ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <InteractionList interactions={interactions} />
          )}
        </Box>

        {/* 入力欄（下部固定） - 常に表示 */}
        {!autoMode && (
          <Box
            sx={{
              borderTop: 1,
              borderColor: 'divider',
              p: 2,
              bgcolor: 'background.paper',
            }}
          >
            <Box display="flex" gap={1} alignItems="flex-end">
              <TextField
                fullWidth
                multiline
                maxRows={4}
                value={responseText}
                onChange={(e) => setResponseText(e.target.value)}
                placeholder={pendingQuestion ? "応答を入力してください..." : "メッセージを入力してください..."}
                disabled={submitting}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    if (responseText.trim() && !submitting) {
                      handleSubmitResponse()
                    }
                  }
                }}
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleSubmitResponse}
                disabled={!responseText.trim() || submitting}
                sx={{ minWidth: '80px', height: '56px' }}
              >
                {submitting ? <CircularProgress size={20} /> : <SendIcon />}
              </Button>
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  )
}

export default TaskExecutionDialog
