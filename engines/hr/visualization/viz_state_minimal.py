"""
Visualization State Management - Minimal and Turn-Scoped
=======================================================
Clean implementation following corrected architecture:
- Minimal state (only essential data)
- Turn-scoped (tied to conversation turns)
- TTL-based expiry (30 minutes)
- No complex session management
- No god object patterns

State ownership: viz_handlers module
State scope: Single conversation turn only
State lifecycle: Created on offer, expires automatically
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

# Redis for production, dict for development
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class VizTurnState:
    """
    MINIMAL visualization state for a single conversation turn
    
    IMMUTABILITY GUARANTEE:
    - data_snapshot is NEVER mutated after creation
    - All transformations operate on copies
    - Required for auditability: must replay exact same data
    - Violation would break: audit trails, deterministic behavior, compliance
    
    TURN-SCOPED LIFECYCLE:
    - State tied to single conversation turn only
    - Auto-expires via TTL (30 minutes)
    - CANNOT survive across conversation turns
    - Session-scoped viz is FORBIDDEN for compliance reasons
    """
    conversation_id: str
    turn_id: str
    data_snapshot: Dict[str, Any]  # IMMUTABLE: columns, rows, metadata
    current_step: str  # 'offered', 'recommended', 'rendered'
    chart_options: list = None  # Available after recommend step
    selected_chart: Dict[str, Any] = None  # Available after render step
    created_at: datetime = None
    expires_at: datetime = None
    _immutable_snapshot: bool = False  # Internal flag to enforce immutability
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(minutes=30)  # 30 min TTL
        if self.chart_options is None:
            self.chart_options = []
        
        # IMMUTABILITY ENFORCEMENT: Mark data_snapshot as immutable after creation
        # This prevents accidental mutation that would break auditability
        self._immutable_snapshot = True
    
    def get_data_copy(self) -> Dict[str, Any]:
        """
        SAFETY METHOD: Get immutable copy of data_snapshot
        
        WHY REQUIRED:
        - Original data_snapshot must NEVER be mutated
        - All transformations must operate on copies
        - Ensures audit trail integrity and deterministic behavior
        
        WHAT BREAKS IF VIOLATED:
        - Cannot replay exact visualization decisions
        - Audit logs become inconsistent
        - Compliance violations in regulated environments
        """
        import copy
        return copy.deepcopy(self.data_snapshot)
    
    def validate_immutability(self) -> bool:
        """
        SAFETY CHECK: Validate data_snapshot has not been mutated
        
        Returns True if data is still immutable, False if corrupted
        Used for defensive programming and audit validation
        """
        return self._immutable_snapshot and self.data_snapshot is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VizTurnState':
        """Create from stored dictionary"""
        # Convert ISO strings back to datetime objects
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if state has expired"""
        return datetime.now() > self.expires_at


class VizStateManager:
    """
    MINIMAL state manager for visualization turns
    
    Responsibilities:
    - Store/retrieve turn-scoped viz state
    - Enforce TTL expiry
    - Clean up expired state
    
    NOT responsible for:
    - Complex session management
    - User preference storage
    - Chart logic
    - Business rules
    """
    
    def __init__(self, redis_url: str = None, ttl_minutes: int = 30):
        self.ttl_seconds = ttl_minutes * 60
        
        # Use Redis if available, fallback to in-memory
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.storage_type = 'redis'
                logger.info("VizStateManager using Redis storage")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, falling back to memory")
                self.redis_client = None
                self.storage_type = 'memory'
                self._memory_store = {}
        else:
            self.redis_client = None
            self.storage_type = 'memory'
            self._memory_store = {}
            logger.info("VizStateManager using in-memory storage")
    
    def store_turn_state(self, viz_state: VizTurnState) -> bool:
        """
        Store visualization state for a turn
        
        Args:
            viz_state: VizTurnState to store
            
        Returns:
            bool: Success status
        """
        try:
            key = self._get_state_key(viz_state.turn_id)
            state_data = viz_state.to_dict()
            
            if self.storage_type == 'redis':
                # Store with TTL in Redis
                self.redis_client.setex(
                    key, 
                    self.ttl_seconds,
                    json.dumps(state_data)
                )
            else:
                # Store in memory with expiry check
                self._memory_store[key] = state_data
            
            logger.info(f"Stored viz state for turn {viz_state.turn_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store viz state for turn {viz_state.turn_id}: {str(e)}")
            return False
    
    def get_turn_state(self, turn_id: str) -> Optional[VizTurnState]:
        """
        Retrieve visualization state for a turn
        
        Args:
            turn_id: Turn identifier
            
        Returns:
            VizTurnState or None if not found/expired
        """
        try:
            key = self._get_state_key(turn_id)
            
            if self.storage_type == 'redis':
                # Redis handles TTL automatically
                state_json = self.redis_client.get(key)
                if not state_json:
                    return None
                
                state_data = json.loads(state_json)
            else:
                # Memory storage needs manual expiry check
                if key not in self._memory_store:
                    return None
                
                state_data = self._memory_store[key]
                
                # Check expiry manually for memory storage
                if state_data.get('expires_at'):
                    expires_at = datetime.fromisoformat(state_data['expires_at'])
                    if datetime.now() > expires_at:
                        del self._memory_store[key]
                        logger.info(f"Expired viz state removed for turn {turn_id}")
                        return None
            
            viz_state = VizTurnState.from_dict(state_data)
            
            # Double-check expiry (defensive programming)
            if viz_state.is_expired():
                self._delete_turn_state(turn_id)
                return None
            
            logger.debug(f"Retrieved viz state for turn {turn_id}")
            return viz_state
            
        except Exception as e:
            logger.error(f"Failed to retrieve viz state for turn {turn_id}: {str(e)}")
            return None
    
    def delete_turn_state(self, turn_id: str) -> bool:
        """
        Manually delete visualization state for a turn
        
        Args:
            turn_id: Turn identifier
            
        Returns:
            bool: Success status
        """
        return self._delete_turn_state(turn_id)
    
    def _delete_turn_state(self, turn_id: str) -> bool:
        """Internal delete method"""
        try:
            key = self._get_state_key(turn_id)
            
            if self.storage_type == 'redis':
                self.redis_client.delete(key)
            else:
                self._memory_store.pop(key, None)
            
            logger.debug(f"Deleted viz state for turn {turn_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete viz state for turn {turn_id}: {str(e)}")
            return False
    
    def cleanup_expired_states(self) -> int:
        """
        Clean up expired states (mainly for memory storage)
        
        Returns:
            int: Number of expired states cleaned up
        """
        if self.storage_type == 'redis':
            # Redis handles TTL automatically
            return 0
        
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, state_data in self._memory_store.items():
                if state_data.get('expires_at'):
                    expires_at = datetime.fromisoformat(state_data['expires_at'])
                    if current_time > expires_at:
                        expired_keys.append(key)
            
            # Remove expired states
            for key in expired_keys:
                del self._memory_store[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired viz states")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Error during expired state cleanup: {str(e)}")
            return 0
    
    def invalidate_turn_states_for_conversation(self, conversation_id: str, 
                                                current_turn_id: str) -> int:
        """
        TURN-SCOPED ENFORCEMENT: Invalidate all viz states when new turn starts
        
        WHY REQUIRED:
        - Visualization MUST NOT survive across conversation turns
        - Each turn gets fresh viz state with NO carryover
        - Prevents stale visualizations from previous queries
        
        WHY SESSION-SCOPED VIZ IS FORBIDDEN:
        - Breaks audit trail (cannot trace viz to specific query)
        - Creates confusion about which data is being visualized  
        - Violates principle of turn-based conversation flow
        
        Args:
            conversation_id: Conversation to clean up
            current_turn_id: New turn ID (will be preserved)
            
        Returns:
            Number of invalidated states
        """
        try:
            invalidated_count = 0
            
            if self.storage_type == 'redis':
                # Get all viz state keys
                pattern = self._get_state_key('*')
                viz_keys = self.redis_client.keys(pattern)
                
                for key in viz_keys:
                    try:
                        state_json = self.redis_client.get(key)
                        if state_json:
                            state_data = json.loads(state_json)
                            if (state_data.get('conversation_id') == conversation_id and 
                                state_data.get('turn_id') != current_turn_id):
                                self.redis_client.delete(key)
                                invalidated_count += 1
                    except Exception:
                        continue
            else:
                # Memory storage
                keys_to_delete = []
                for key, state_data in self._memory_store.items():
                    if (state_data.get('conversation_id') == conversation_id and 
                        state_data.get('turn_id') != current_turn_id):
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self._memory_store[key]
                    invalidated_count += 1
            
            if invalidated_count > 0:
                logger.info(f"Invalidated {invalidated_count} viz states for conversation {conversation_id}")
            
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate turn states: {str(e)}")
            return 0
    
    def validate_turn_state_freshness(self, turn_id: str) -> Dict[str, Any]:
        """
        STRICT TTL VALIDATION: Validate viz state is still fresh and valid
        
        WHY REQUIRED:
        - TTL enforcement prevents stale visualizations
        - Turn-scoped validation ensures no cross-turn pollution
        - Audit requirement: must validate state integrity
        
        Returns validation status with explicit reasoning
        """
        try:
            viz_state = self.get_turn_state(turn_id)
            
            if not viz_state:
                return {
                    'valid': False,
                    'reason': 'No visualization state found',
                    'expired': True
                }
            
            # Check TTL expiry
            if viz_state.is_expired():
                self._delete_turn_state(turn_id)
                return {
                    'valid': False,
                    'reason': 'Visualization state expired (TTL exceeded)',
                    'expired': True,
                    'expired_at': viz_state.expires_at.isoformat()
                }
            
            # Check immutability
            if not viz_state.validate_immutability():
                return {
                    'valid': False,
                    'reason': 'Data snapshot integrity compromised',
                    'expired': False,
                    'corrupted': True
                }
            
            return {
                'valid': True,
                'reason': 'Visualization state is fresh and valid',
                'expires_in_seconds': (viz_state.expires_at - datetime.now()).total_seconds()
            }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'State validation error: {str(e)}',
                'error': True
            }
    def _get_state_key(self, turn_id: str) -> str:
        """Generate Redis/memory key for turn state"""
        return f"viz_state:turn:{turn_id}"


# Global instance for application use
# In production, initialize with Redis URL
_viz_state_manager = None

def get_viz_state_manager(redis_url: str = None) -> VizStateManager:
    """
    Get global VizStateManager instance
    
    Args:
        redis_url: Redis connection URL (for production)
        
    Returns:
        VizStateManager instance
    """
    global _viz_state_manager
    
    if _viz_state_manager is None:
        _viz_state_manager = VizStateManager(redis_url=redis_url)
    
    return _viz_state_manager


# Export main classes
__all__ = ['VizTurnState', 'VizStateManager', 'get_viz_state_manager']


# Global instance for application use
# In production, initialize with Redis URL
_viz_state_manager = None

def get_viz_state_manager(redis_url: str = None) -> VizStateManager:
    """
    Get global VizStateManager instance
    
    Args:
        redis_url: Redis connection URL (for production)
        
    Returns:
        VizStateManager instance
    """
    global _viz_state_manager
    
    if _viz_state_manager is None:
        _viz_state_manager = VizStateManager(redis_url=redis_url)
    
    return _viz_state_manager


# Export main classes
__all__ = ['VizTurnState', 'VizStateManager', 'get_viz_state_manager']