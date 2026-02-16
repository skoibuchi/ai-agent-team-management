"""
Approval Service
ツール追加承認を管理するサービス
"""
import time
from datetime import datetime
from typing import List, Optional
from app import db
from app.models.tool_approval import ToolApprovalRequest
from app.websocket.events import emit_tool_approval_request


class ApprovalService:
    """ツール承認サービス"""
    
    def request_tool_approval(
        self,
        agent_id: int,
        task_id: Optional[int],
        tools: List[str],
        reason: str
    ) -> int:
        """
        ツール追加の承認をリクエスト
        
        Args:
            agent_id: エージェントID
            task_id: タスクID（オプション）
            tools: 追加したいツールのリスト
            reason: 追加理由
            
        Returns:
            approval_id: 承認リクエストID
        """
        approval = ToolApprovalRequest(
            agent_id=agent_id,
            task_id=task_id,
            requested_tools=tools,
            reason=reason,
            status='pending'
        )
        db.session.add(approval)
        db.session.commit()
        
        # WebSocketで通知
        try:
            emit_tool_approval_request(approval.to_dict())
        except Exception as e:
            print(f"Failed to emit WebSocket notification: {e}")
        
        return approval.id
    
    def wait_for_approval(
        self,
        approval_id: int,
        timeout: int = 300
    ) -> bool:
        """
        承認を待つ（デフォルト5分）
        
        Args:
            approval_id: 承認リクエストID
            timeout: タイムアウト時間（秒）
            
        Returns:
            True: 承認された
            False: 拒否またはタイムアウト
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            approval = ToolApprovalRequest.query.get(approval_id)
            
            if not approval:
                return False
            
            if approval.status == 'approved':
                return True
            elif approval.status == 'rejected':
                return False
            
            # 1秒待機
            time.sleep(1)
        
        # タイムアウト
        approval = ToolApprovalRequest.query.get(approval_id)
        if approval and approval.status == 'pending':
            approval.status = 'timeout'
            approval.responded_at = datetime.utcnow()
            db.session.commit()
        
        return False
    
    def approve_request(
        self,
        approval_id: int,
        note: Optional[str] = None
    ) -> bool:
        """
        承認リクエストを承認
        
        Args:
            approval_id: 承認リクエストID
            note: 承認メモ（オプション）
            
        Returns:
            True: 成功
            False: 失敗
        """
        approval = ToolApprovalRequest.query.get(approval_id)
        
        if not approval:
            return False
        
        if approval.status != 'pending':
            return False
        
        approval.status = 'approved'
        approval.responded_at = datetime.utcnow()
        approval.response_note = note
        db.session.commit()
        
        return True
    
    def reject_request(
        self,
        approval_id: int,
        note: Optional[str] = None
    ) -> bool:
        """
        承認リクエストを拒否
        
        Args:
            approval_id: 承認リクエストID
            note: 拒否理由（オプション）
            
        Returns:
            True: 成功
            False: 失敗
        """
        approval = ToolApprovalRequest.query.get(approval_id)
        
        if not approval:
            return False
        
        if approval.status != 'pending':
            return False
        
        approval.status = 'rejected'
        approval.responded_at = datetime.utcnow()
        approval.response_note = note
        db.session.commit()
        
        return True
    
    def get_pending_requests(self, agent_id: Optional[int] = None) -> List[dict]:
        """
        保留中の承認リクエストを取得
        
        Args:
            agent_id: エージェントID（オプション、指定すると特定エージェントのみ）
            
        Returns:
            承認リクエストのリスト
        """
        query = ToolApprovalRequest.query.filter_by(status='pending')
        
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        
        requests = query.order_by(ToolApprovalRequest.requested_at.desc()).all()
        return [req.to_dict() for req in requests]
    
    def get_request(self, approval_id: int) -> Optional[dict]:
        """
        承認リクエストを取得
        
        Args:
            approval_id: 承認リクエストID
            
        Returns:
            承認リクエスト情報
        """
        approval = ToolApprovalRequest.query.get(approval_id)
        return approval.to_dict() if approval else None
