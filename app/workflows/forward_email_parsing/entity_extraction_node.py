from typing import List, Optional
from pydantic import BaseModel, Field

from core.nodes.agent import AgentNode, AgentConfig, ModelProvider
from core.task import TaskContext
from workflows.forward_email_parsing.email_parsing_model_config import EmailParsingModelConfig
from schemas.email_parsing_schema import EmailParsingEventSchema


class Person(BaseModel):
    name: str = Field(..., description="Full name of the person")
    email: Optional[str] = Field(None, description="Email address if found")
    role: Optional[str] = Field(None, description="Role or title (e.g., 'Physical Therapist', 'MD')")
    organization: Optional[str] = Field(None, description="Organization affiliation")
    confidence: float = Field(..., description="Confidence score 0-1")


class Organization(BaseModel):
    name: str = Field(..., description="Organization name")
    type: Optional[str] = Field(None, description="Type of organization (hospital, clinic, etc.)")
    confidence: float = Field(..., description="Confidence score 0-1")


class DateMention(BaseModel):
    date: str = Field(..., description="Date mentioned (ISO format if possible)")
    context: str = Field(..., description="Context of the date mention")
    type: str = Field(..., description="Type: 'meeting', 'deadline', 'followup', 'other'")


class Location(BaseModel):
    place: str = Field(..., description="Location name")
    address: Optional[str] = Field(None, description="Address if mentioned")
    type: Optional[str] = Field(None, description="Type of location")


class EntityExtractionNode(AgentNode):
    """Extracts people, organizations, dates, and locations from email content"""
    
    def get_agent_config(self) -> AgentConfig:
        return AgentConfig(
            system_prompt="""You are an expert entity extractor for emails.
Extract all mentions of:
1. People - names, emails, roles, titles
2. Organizations - companies, hospitals, clinics
3. Dates - meetings, deadlines, follow-ups
4. Locations - places, addresses

Consider context and relationships. For example:
- "Dr. McDonald" and "Devon McDonald" likely refer to the same person
- Include confidence scores based on context clarity
- Extract roles from context (e.g., "physical therapist", "MD")""",
            output_type=self.ExtractedEntities,
            deps_type=EmailParsingEventSchema,
            model_provider=EmailParsingModelConfig.get_provider(),
            model_name=EmailParsingModelConfig.get_model('extraction')[1],
            instrument=True,
        )
    
    class ExtractedEntities(BaseModel):
        people: List[Person] = Field(default_factory=list, description="All people mentioned")
        organizations: List[Organization] = Field(default_factory=list, description="All organizations mentioned")
        dates: List[DateMention] = Field(default_factory=list, description="All dates mentioned")
        locations: List[Location] = Field(default_factory=list, description="All locations mentioned")
    
    def process(self, task_context: TaskContext) -> TaskContext:
        event: EmailParsingEventSchema = task_context.event
        
        # Get any forwarded content from previous nodes
        forwarded_data = task_context.nodes.get("ForwardedEmailExtractionNode", {})
        content = forwarded_data.get("forwarded_content", "") or event.body_plain or event.body
        
        # Extract entities
        result = self.agent.run_sync(
            user_prompt=f"""Extract all entities from this email content:

Subject: {event.subject}
From: {event.from_email} ({event.from_name})
Content: {content[:2000]}""",
            deps=event
        )
        
        # Store extracted entities
        task_context.update_node(
            node_name=self.node_name,
            results=result.output.model_dump(),
            people=[p.model_dump() for p in result.output.people],
            organizations=[o.model_dump() for o in result.output.organizations],
            dates=[d.model_dump() for d in result.output.dates],
            locations=[l.model_dump() for l in result.output.locations]
        )
        
        return task_context