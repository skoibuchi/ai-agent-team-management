import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  Alert,
  Autocomplete,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Group as GroupIcon,
} from '@mui/icons-material'
import { teamApi, agentApi } from '../services/api'
import type { Team, Agent } from '../types'

const Teams: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    leader_agent_id: 0,
    member_ids: [] as number[],
    is_active: true,
  })

  useEffect(() => {
    loadTeams()
    loadAgents()
  }, [])

  const loadTeams = async () => {
    try {
      setLoading(true)
      const response = await teamApi.getAll()
      if (response.data.success) {
        setTeams(response.data.data || [])
      }
    } catch (err) {
      setError('チームの読み込みに失敗しました')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadAgents = async () => {
    try {
      const response = await agentApi.getAll()
      if (response.data.success) {
        setAgents(response.data.data || [])
      }
    } catch (err) {
      console.error('エージェントの読み込みに失敗しました', err)
    }
  }

  const handleOpenDialog = (team?: Team) => {
    if (team) {
      setEditingTeam(team)
      setFormData({
        name: team.name,
        description: team.description || '',
        leader_agent_id: team.leader_agent_id,
        member_ids: team.member_ids || [],
        is_active: team.is_active,
      })
    } else {
      setEditingTeam(null)
      setFormData({
        name: '',
        description: '',
        leader_agent_id: 0,
        member_ids: [],
        is_active: true,
      })
    }
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setEditingTeam(null)
  }

  const handleSave = async () => {
    try {
      if (!formData.name.trim()) {
        setError('チーム名を入力してください')
        return
      }
      if (!formData.leader_agent_id) {
        setError('リーダーエージェントを選択してください')
        return
      }
      if (formData.member_ids.length === 0) {
        setError('少なくとも1人のメンバーを選択してください')
        return
      }

      const data = {
        name: formData.name,
        description: formData.description,
        leader_agent_id: formData.leader_agent_id,
        member_ids: formData.member_ids,
        is_active: formData.is_active,
      }

      if (editingTeam) {
        await teamApi.update(editingTeam.id, data)
      } else {
        await teamApi.create(data)
      }

      handleCloseDialog()
      loadTeams()
      setError(null)
    } catch (err: any) {
      setError(err.response?.data?.message || 'チームの保存に失敗しました')
      console.error(err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('このチームを削除してもよろしいですか？')) {
      return
    }

    try {
      await teamApi.delete(id)
      loadTeams()
    } catch (err: any) {
      setError(err.response?.data?.message || 'チームの削除に失敗しました')
      console.error(err)
    }
  }

  const handleToggleActive = async (team: Team) => {
    try {
      await teamApi.update(team.id, { is_active: !team.is_active })
      loadTeams()
    } catch (err: any) {
      setError(err.response?.data?.message || 'ステータスの更新に失敗しました')
      console.error(err)
    }
  }

  const getAgentName = (agentId: number) => {
    const agent = agents.find((a) => a.id === agentId)
    return agent ? agent.name : `Agent #${agentId}`
  }

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>読み込み中...</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          <GroupIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          チーム管理
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          新規チーム作成
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {teams.map((team) => (
          <Grid item xs={12} md={6} lg={4} key={team.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="h2">
                    {team.name}
                  </Typography>
                  <Box>
                    <IconButton size="small" onClick={() => handleOpenDialog(team)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(team.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Box>

                {team.description && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {team.description}
                  </Typography>
                )}

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    リーダー:
                  </Typography>
                  <Chip
                    label={team.leader_agent?.name || getAgentName(team.leader_agent_id)}
                    size="small"
                    color="primary"
                  />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    メンバー ({team.member_ids?.length || 0}人):
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {team.members?.map((member) => (
                      <Chip key={member.id} label={member.name} size="small" />
                    )) ||
                      team.member_ids?.map((id) => (
                        <Chip key={id} label={getAgentName(id)} size="small" />
                      ))}
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip
                    label={team.is_active ? 'アクティブ' : '非アクティブ'}
                    color={team.is_active ? 'success' : 'default'}
                    size="small"
                  />
                  <Switch
                    checked={team.is_active}
                    onChange={() => handleToggleActive(team)}
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {teams.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <GroupIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            チームがまだ作成されていません
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            「新規チーム作成」ボタンから最初のチームを作成しましょう
          </Typography>
        </Box>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingTeam ? 'チーム編集' : '新規チーム作成'}</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="チーム名"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              required
            />

            <TextField
              label="説明"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />

            <FormControl fullWidth required>
              <InputLabel>リーダーエージェント</InputLabel>
              <Select
                value={formData.leader_agent_id}
                onChange={(e) => setFormData({ ...formData, leader_agent_id: Number(e.target.value) })}
                label="リーダーエージェント"
              >
                <MenuItem value={0}>選択してください</MenuItem>
                {agents.map((agent) => (
                  <MenuItem key={agent.id} value={agent.id}>
                    {agent.name} {agent.role && `(${agent.role})`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Autocomplete
              multiple
              options={agents}
              getOptionLabel={(option) => `${option.name}${option.role ? ` (${option.role})` : ''}`}
              value={agents.filter((a) => formData.member_ids.includes(a.id))}
              onChange={(_, newValue) => {
                setFormData({ ...formData, member_ids: newValue.map((a) => a.id) })
              }}
              renderInput={(params) => (
                <TextField {...params} label="メンバー" placeholder="エージェントを選択" required />
              )}
            />

            <FormControl fullWidth>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography>アクティブ</Typography>
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              </Box>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button onClick={handleSave} variant="contained" color="primary">
            {editingTeam ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Teams
