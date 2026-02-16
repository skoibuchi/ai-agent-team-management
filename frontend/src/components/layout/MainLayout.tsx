import { ReactNode, useEffect, useState } from 'react'
import { Box, AppBar, Toolbar, Typography, IconButton, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Badge } from '@mui/material'
import { Menu as MenuIcon, Dashboard as DashboardIcon, SmartToy as AgentIcon, Assignment as TaskIcon, Build as ToolIcon, Settings as SettingsIcon, Notifications as NotificationsIcon } from '@mui/icons-material'
import { useNavigate, useLocation } from 'react-router-dom'
import { useStore } from '@/store'
import { api } from '@/services/api'
import ToolApprovalDialog from '@/components/ToolApprovalDialog'

interface MainLayoutProps {
  children: ReactNode
}

const drawerWidth = 240

const menuItems = [
  { text: 'ダッシュボード', icon: <DashboardIcon />, path: '/' },
  { text: 'エージェント', icon: <AgentIcon />, path: '/agents' },
  { text: 'タスク', icon: <TaskIcon />, path: '/tasks' },
  { text: 'ツール', icon: <ToolIcon />, path: '/tools' },
  { text: '設定', icon: <SettingsIcon />, path: '/settings' },
]

export default function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarOpen, setSidebarOpen } = useStore()
  const [pendingApprovals, setPendingApprovals] = useState<any[]>([])
  const [selectedApproval, setSelectedApproval] = useState<any>(null)
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false)

  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const fetchPendingApprovals = async () => {
    try {
      const response = await api.getPendingApprovals()
      setPendingApprovals(response.data || [])
    } catch (error) {
      console.error('Failed to fetch pending approvals:', error)
    }
  }

  const handleApprove = async (id: number, note?: string) => {
    try {
      await api.approveToolRequest(id, note)
      await fetchPendingApprovals()
    } catch (error) {
      console.error('Failed to approve request:', error)
      throw error
    }
  }

  const handleReject = async (id: number, note?: string) => {
    try {
      await api.rejectToolRequest(id, note)
      await fetchPendingApprovals()
    } catch (error) {
      console.error('Failed to reject request:', error)
      throw error
    }
  }

  const handleNotificationClick = () => {
    if (pendingApprovals.length > 0) {
      setSelectedApproval(pendingApprovals[0])
      setApprovalDialogOpen(true)
    }
  }

  const handleApprovalDialogClose = () => {
    setApprovalDialogOpen(false)
    setSelectedApproval(null)
  }

  useEffect(() => {
    // 初回のみ承認待ちを取得（ポーリングは削除）
    fetchPendingApprovals()
  }, [])

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* AppBar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            AI Agent Team Manager
          </Typography>
          <IconButton
            color="inherit"
            onClick={handleNotificationClick}
            disabled={pendingApprovals.length === 0}
          >
            <Badge badgeContent={pendingApprovals.length} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant="persistent"
        open={sidebarOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => navigate(item.path)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${sidebarOpen ? drawerWidth : 0}px)` },
          ml: sidebarOpen ? 0 : `-${drawerWidth}px`,
          transition: (theme) =>
            theme.transitions.create(['margin', 'width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
        }}
      >
        <Toolbar />
        {children}
      </Box>

      {/* Tool Approval Dialog */}
      <ToolApprovalDialog
        open={approvalDialogOpen}
        request={selectedApproval}
        onClose={handleApprovalDialogClose}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </Box>
  )
}
