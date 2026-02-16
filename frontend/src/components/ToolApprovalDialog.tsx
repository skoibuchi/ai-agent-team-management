import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  List,
  ListItem,
  ListItemText,
  TextField,
  Box,
  Chip,
  Alert,
} from '@mui/material'
import { CheckCircle, Cancel } from '@mui/icons-material'

interface ToolApprovalRequest {
  id: number
  agent_id: number
  agent_name?: string
  task_id?: number
  task_title?: string
  requested_tools: string[]
  reason: string
  status: string
  requested_at: string
}

interface ToolApprovalDialogProps {
  open: boolean
  request: ToolApprovalRequest | null
  onClose: () => void
  onApprove: (id: number, note?: string) => Promise<void>
  onReject: (id: number, note?: string) => Promise<void>
}

export default function ToolApprovalDialog({
  open,
  request,
  onClose,
  onApprove,
  onReject,
}: ToolApprovalDialogProps) {
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)

  const handleApprove = async () => {
    if (!request) return
    
    setLoading(true)
    try {
      await onApprove(request.id, note)
      setNote('')
      onClose()
    } catch (error) {
      console.error('Failed to approve request:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    if (!request) return
    
    setLoading(true)
    try {
      await onReject(request.id, note)
      setNote('')
      onClose()
    } catch (error) {
      console.error('Failed to reject request:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setNote('')
    onClose()
  }

  if (!request) return null

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>ツール追加の承認リクエスト</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            エージェントがタスク実行中に新しいツールを必要としています
          </Alert>

          <Typography variant="subtitle2" gutterBottom>
            エージェント
          </Typography>
          <Typography variant="body1" sx={{ mb: 2 }}>
            {request.agent_name || `Agent #${request.agent_id}`}
          </Typography>

          {request.task_title && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                タスク
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {request.task_title}
              </Typography>
            </>
          )}

          <Typography variant="subtitle2" gutterBottom>
            要求されたツール
          </Typography>
          <List dense sx={{ mb: 2 }}>
            {request.requested_tools.map((tool, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip label={tool} size="small" color="primary" />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Typography variant="subtitle2" gutterBottom>
            理由
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            {request.reason}
          </Typography>

          <Typography variant="subtitle2" gutterBottom>
            リクエスト日時
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            {new Date(request.requested_at).toLocaleString('ja-JP')}
          </Typography>

          <TextField
            label="メモ（オプション）"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            fullWidth
            multiline
            rows={2}
            placeholder="承認/拒否の理由を記入できます"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          キャンセル
        </Button>
        <Button
          onClick={handleReject}
          color="error"
          startIcon={<Cancel />}
          disabled={loading}
        >
          拒否
        </Button>
        <Button
          onClick={handleApprove}
          variant="contained"
          color="primary"
          startIcon={<CheckCircle />}
          disabled={loading}
        >
          承認
        </Button>
      </DialogActions>
    </Dialog>
  )
}
