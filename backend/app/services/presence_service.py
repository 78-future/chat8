from db.models import User
from db.database import SessionLocal
from datetime import datetime

# 内存缓存存储P2P能力信息
p2p_capabilities = {}

def set_status(user_id: int, status: str):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.status = status
        if status == 'online':
            user.last_seen = datetime.utcnow()
        db.commit()
    db.close()
    return True

def get_contacts_status(user_ids: list):
    db = SessionLocal()
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    result = [
        {
            "userId": str(u.id),
            "username": u.username,
            "status": getattr(u, "status", "offline"),
            "lastSeen": u.last_seen,
        } for u in users
    ]
    db.close()
    return result

def heartbeat(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_seen = datetime.utcnow()
        db.commit()
    db.close()
    return {"nextHeartbeat": 30000}

def set_p2p_capability(user_id: int, supports_p2p: bool, capabilities: list):
    """设置用户的P2P能力"""
    p2p_capabilities[user_id] = {
        'supportsP2P': supports_p2p,
        'capabilities': capabilities,
        'timestamp': datetime.utcnow()
    }
    return True

def get_user_status(user_id: int):
    """获取用户的完整状态信息"""
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        db.close()
        return {'online': False, 'supportsP2P': False, 'lastSeen': None}
    
    # 判断用户是否在线（最近5分钟内有活动）
    is_online = False
    if user.last_seen:
        time_diff = datetime.utcnow() - user.last_seen
        is_online = time_diff.total_seconds() < 300  # 5分钟
    
    # 获取P2P能力
    p2p_info = p2p_capabilities.get(user_id, {'supportsP2P': False})
    
    result = {
        'online': is_online,
        'supportsP2P': p2p_info.get('supportsP2P', False),
        'lastSeen': user.last_seen.isoformat() if user.last_seen else None
    }
    
    db.close()
    return result