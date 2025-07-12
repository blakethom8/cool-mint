from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from uuid import UUID
import os
from datetime import datetime
import anthropic
import tiktoken
import json

from database.session import db_session
from database.data_models.activity_bundles import (
    ActivityBundle,
    LLMConversation,
    SavedLLMResponse,
)
from database.data_models.salesforce_data import SfActivityStructured
from schemas.llm_schema import (
    ConversationCreateRequest,
    ConversationResponse,
    ConversationListResponse,
    LLMMessage,
    LLMMessageRequest,
    SaveResponseRequest,
    SavedResponseItem,
    SavedResponsesResponse,
)

router = APIRouter()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest, session: Session = Depends(db_session)
):
    """
    Create a new LLM conversation for a bundle.

    This initializes a conversation with the specified model and
    optional system prompt.
    """
    # Verify bundle exists
    bundle = session.scalar(
        select(ActivityBundle).where(ActivityBundle.id == request.bundle_id)
    )

    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")

    # Get activities for context
    activities = session.scalars(
        select(SfActivityStructured).where(
            SfActivityStructured.salesforce_activity_id.in_(bundle.activity_ids)
        )
    ).all()

    # Build system prompt
    default_system_prompt = f"""You are analyzing a bundle of {len(activities)} activities from a healthcare/medical network organization.

Bundle Name: {bundle.name}
Bundle Description: {bundle.description or "No description provided"}

You have access to rich structured data for each activity including:
- Basic activity information (date, subject, description, owner, type/subtype)
- Detailed contact information (names, specialties, organizations, locations)
- Geographic and network classifications
- Activity metadata (settings, community connections, physician relationships)

The data is provided in a structured JSON format with:
- "basic_info": Core activity details
- "structured_context": Rich contextual data including contacts array and activity metadata

Please provide helpful insights and analysis based on the user's questions. You can analyze patterns across:
- Geographic distributions and trends
- Contact relationships and specialties
- Activity types and outcomes
- Network connections and community engagement
- Temporal patterns and seasonal trends

When referencing activities, you can use the activity_id for precise identification."""

    system_prompt = request.system_prompt or default_system_prompt

    # Create initial message list with system prompt
    messages = [
        {
            "role": "system",
            "content": system_prompt,
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]

    # Create conversation
    conversation = LLMConversation(
        bundle_id=request.bundle_id,
        model=request.model,
        messages=messages,
        total_tokens_used=0,
    )

    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Convert to response
    response = ConversationResponse.model_validate(conversation)
    response.message_count = len(conversation.messages)
    response.saved_responses_count = 0

    return response


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    bundle_id: Optional[UUID] = None, session: Session = Depends(db_session)
):
    """
    List all conversations, optionally filtered by bundle.
    """
    query = select(LLMConversation).options(
        selectinload(LLMConversation.saved_responses)
    )

    if bundle_id:
        query = query.where(LLMConversation.bundle_id == bundle_id)

    query = query.order_by(LLMConversation.created_at.desc())

    conversations = session.scalars(query).all()

    # Convert to response
    conversation_responses = []
    for conv in conversations:
        response = ConversationResponse.model_validate(conv)
        response.message_count = len(conv.messages)
        response.saved_responses_count = len(conv.saved_responses)
        conversation_responses.append(response)

    return ConversationListResponse(
        conversations=conversation_responses, total_count=len(conversations)
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID, session: Session = Depends(db_session)
):
    """
    Get a specific conversation with all messages.
    """
    conversation = session.scalar(
        select(LLMConversation)
        .where(LLMConversation.id == conversation_id)
        .options(selectinload(LLMConversation.saved_responses))
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    response = ConversationResponse.model_validate(conversation)
    response.message_count = len(conversation.messages)
    response.saved_responses_count = len(conversation.saved_responses)

    return response


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request: LLMMessageRequest,
    session: Session = Depends(db_session),
):
    """
    Send a message to the LLM and get a response.

    This endpoint sends the user's message to the LLM along with
    the conversation history and activity context.
    """
    # Get conversation with bundle
    conversation = session.scalar(
        select(LLMConversation)
        .where(LLMConversation.id == conversation_id)
        .options(selectinload(LLMConversation.bundle))
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get activities for context
    activities = session.scalars(
        select(SfActivityStructured).where(
            SfActivityStructured.salesforce_activity_id.in_(
                conversation.bundle.activity_ids
            )
        )
    ).all()

    # Build activity context using structured LLM context
    activity_context = "\n\nACTIVITY CONTEXT:\n"
    activity_context += f"The following {len(activities)} activities contain structured data with contacts, geography, and classifications.\n\n"

    for i, activity in enumerate(activities, 1):
        activity_context += f"=== Activity {i} ===\n"

        if activity.llm_context_json:
            # Use the rich structured context
            structured_activity = {
                "basic_info": {
                    "activity_id": activity.salesforce_activity_id,
                    "date": str(activity.activity_date)
                    if activity.activity_date
                    else None,
                    "subject": activity.subject,
                    "description": activity.description,
                    "owner": activity.user_name,
                    "type": activity.mno_type or activity.type,
                    "subtype": activity.mno_subtype,
                },
                "structured_context": activity.llm_context_json,
            }
            activity_context += json.dumps(structured_activity, indent=2)
        else:
            # Fallback for activities without structured context
            activity_context += f"Activity ID: {activity.salesforce_activity_id}\n"
            activity_context += f"Date: {activity.activity_date}\n"
            activity_context += f"Subject: {activity.subject}\n"
            activity_context += f"Type: {activity.mno_type or activity.type}\n"
            if activity.mno_subtype:
                activity_context += f"Subtype: {activity.mno_subtype}\n"
            if activity.description:
                activity_context += f"Description: {activity.description}\n"
            if activity.contact_names:
                activity_context += f"Contacts: {', '.join(activity.contact_names)}\n"
            if activity.contact_specialties:
                activity_context += (
                    f"Specialties: {', '.join(activity.contact_specialties)}\n"
                )
            activity_context += "Note: This activity lacks structured context data.\n"

        activity_context += "\n\n"

    # Add activity context to the first user message if this is the first user message
    user_messages = [m for m in conversation.messages if m.get("role") == "user"]
    if len(user_messages) == 0:
        # This is the first user message, include context
        full_message = request.message + activity_context
    else:
        full_message = request.message

    # Add user message to conversation
    user_msg = {
        "role": "user",
        "content": full_message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Prepare messages for API - extract system message and user/assistant messages
    api_messages = []
    system_prompt = None

    for msg in conversation.messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        else:
            api_messages.append({"role": msg["role"], "content": msg["content"]})

    api_messages.append({"role": "user", "content": full_message})

    try:
        # Call Anthropic API with system prompt as separate parameter
        response = client.messages.create(
            model=request.model or conversation.model,
            system=system_prompt,
            messages=api_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens or 4096,
        )

        # Extract response
        assistant_content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        # Add assistant message
        assistant_msg = {
            "role": "assistant",
            "content": assistant_content,
            "timestamp": datetime.utcnow().isoformat(),
            "tokens": tokens_used,
        }

        # Update conversation
        conversation.messages = conversation.messages + [user_msg, assistant_msg]
        conversation.total_tokens_used += tokens_used
        conversation.updated_at = datetime.utcnow()

        session.commit()

        return {
            "message": assistant_content,
            "tokens_used": tokens_used,
            "total_tokens": conversation.total_tokens_used,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")


@router.post("/responses/save", response_model=SavedResponseItem)
async def save_response(
    request: SaveResponseRequest, session: Session = Depends(db_session)
):
    """
    Save a specific LLM response for future reference.
    """
    # Verify conversation exists
    conversation = session.scalar(
        select(LLMConversation).where(LLMConversation.id == request.conversation_id)
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create saved response
    saved_response = SavedLLMResponse(
        conversation_id=request.conversation_id,
        prompt=request.prompt,
        response=request.response,
        note=request.note,
        response_metadata=request.response_metadata,
    )

    session.add(saved_response)
    session.commit()
    session.refresh(saved_response)

    return SavedResponseItem.model_validate(saved_response)


@router.get("/responses/saved", response_model=SavedResponsesResponse)
async def list_saved_responses(
    conversation_id: Optional[UUID] = None,
    bundle_id: Optional[UUID] = None,
    session: Session = Depends(db_session),
):
    """
    List saved responses, optionally filtered by conversation or bundle.
    """
    query = select(SavedLLMResponse)

    if conversation_id:
        query = query.where(SavedLLMResponse.conversation_id == conversation_id)
    elif bundle_id:
        # Join with conversation to filter by bundle
        query = query.join(LLMConversation).where(
            LLMConversation.bundle_id == bundle_id
        )

    query = query.order_by(SavedLLMResponse.saved_at.desc())

    responses = session.scalars(query).all()

    return SavedResponsesResponse(
        responses=[SavedResponseItem.model_validate(r) for r in responses],
        total_count=len(responses),
    )
