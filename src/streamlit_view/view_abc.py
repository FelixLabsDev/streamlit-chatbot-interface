from abc import ABC, abstractmethod


class BaseView(ABC):
    
    @abstractmethod
    def run(self) -> None:
        pass
    
    @abstractmethod
    def send_message(self, chat_id: str, message: str) -> None:
        pass


class RedisEnabledMixin:
    """Mixin for views that require Redis to store and retrieve messages."""
    use_redis = True

    def set_redis_client(self, redis_client):
        self.redis = redis_client

