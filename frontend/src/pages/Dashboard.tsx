import { useEffect } from 'react'
import { Box, Grid, Paper, Typography, Card, CardContent, CircularProgress } from '@mui/material'
import { SmartToy, Assignment, CheckCircle, Error as ErrorIcon } from '@mui/icons-material'
import { useStore } from '@/store'

export default function Dashboard() {
  const { agents, tasks, loading, fetchAgents, fetchTasks } = useStore()

  useEffect(() => {
    fetchAgents()
    fetchTasks()
  }, [fetchAgents, fetchTasks])

  // 統計情報の計算
  const stats = {
    totalAgents: agents.length,
    activeAgents: agents.filter(a => a.status === 'active').length,
    totalTasks: tasks.length,
    completedTasks: tasks.filter(t => t.status === 'completed').length,
    runningTasks: tasks.filter(t => t.status === 'running').length,
    failedTasks: tasks.filter(t => t.status === 'failed').length,
  }

  const statCards = [
    {
      title: 'エージェント',
      value: stats.totalAgents,
      subtitle: `アクティブ: ${stats.activeAgents}`,
      icon: <SmartToy sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: 'タスク',
      value: stats.totalTasks,
      subtitle: `実行中: ${stats.runningTasks}`,
      icon: <Assignment sx={{ fontSize: 40 }} />,
      color: '#2e7d32',
    },
    {
      title: '完了',
      value: stats.completedTasks,
      subtitle: `成功率: ${stats.totalTasks > 0 ? Math.round((stats.completedTasks / stats.totalTasks) * 100) : 0}%`,
      icon: <CheckCircle sx={{ fontSize: 40 }} />,
      color: '#388e3c',
    },
    {
      title: '失敗',
      value: stats.failedTasks,
      subtitle: `失敗率: ${stats.totalTasks > 0 ? Math.round((stats.failedTasks / stats.totalTasks) * 100) : 0}%`,
      icon: <ErrorIcon sx={{ fontSize: 40 }} />,
      color: '#d32f2f',
    },
  ]

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        ダッシュボード
      </Typography>

      {/* 統計カード */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.title}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div">
                      {stat.value}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {stat.subtitle}
                    </Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>
                    {stat.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 最近のタスク */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          最近のタスク
        </Typography>
        {tasks.length === 0 ? (
          <Typography color="textSecondary">タスクがありません</Typography>
        ) : (
          <Box>
            {tasks.slice(0, 5).map((task) => (
              <Box
                key={task.id}
                sx={{
                  p: 2,
                  mb: 1,
                  border: '1px solid #e0e0e0',
                  borderRadius: 1,
                  '&:hover': { bgcolor: '#f5f5f5' },
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="subtitle1">{task.title}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {task.description}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography
                      variant="caption"
                      sx={{
                        px: 1,
                        py: 0.5,
                        borderRadius: 1,
                        bgcolor:
                          task.status === 'completed'
                            ? '#e8f5e9'
                            : task.status === 'running'
                            ? '#e3f2fd'
                            : task.status === 'failed'
                            ? '#ffebee'
                            : '#f5f5f5',
                        color:
                          task.status === 'completed'
                            ? '#2e7d32'
                            : task.status === 'running'
                            ? '#1976d2'
                            : task.status === 'failed'
                            ? '#c62828'
                            : '#616161',
                      }}
                    >
                      {task.status === 'pending' && '待機中'}
                      {task.status === 'running' && '実行中'}
                      {task.status === 'completed' && '完了'}
                      {task.status === 'failed' && '失敗'}
                      {task.status === 'cancelled' && 'キャンセル'}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </Paper>

      {/* アクティブなエージェント */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          アクティブなエージェント
        </Typography>
        {agents.filter(a => a.status === 'active').length === 0 ? (
          <Typography color="textSecondary">アクティブなエージェントがありません</Typography>
        ) : (
          <Grid container spacing={2}>
            {agents
              .filter(a => a.status === 'active')
              .slice(0, 6)
              .map((agent) => (
                <Grid item xs={12} sm={6} md={4} key={agent.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {agent.name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        {agent.description}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        役割: {agent.role}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
          </Grid>
        )}
      </Paper>
    </Box>
  )
}
