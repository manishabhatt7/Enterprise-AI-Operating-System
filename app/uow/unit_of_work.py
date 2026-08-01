from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.repositories.agent import AgentRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.document import DocumentRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

        self.organizations = OrganizationRepository(session)
        self.users = UserRepository(session)
        self.agents = AgentRepository(session)
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)
        self.knowledge_bases = KnowledgeBaseRepository(session)
        self.documents = DocumentRepository(session)
        
    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def refresh(self, instance):
        await self.session.refresh(instance)
