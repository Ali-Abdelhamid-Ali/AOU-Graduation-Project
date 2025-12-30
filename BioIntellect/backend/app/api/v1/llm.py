"""Medical LLM Chat API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.db.supabase_client import supabase_admin
from app.api.v1.auth import get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# ============== SCHEMAS ==============

class ConversationCreateRequest(BaseModel):
    conversation_type: str = "patient_llm"  # patient_llm, doctor_llm, doctor_patient_llm
    patient_id: str
    doctor_id: Optional[str] = None
    case_id: Optional[str] = None
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    llm_model: Optional[str] = "gpt-4"

class MessageRequest(BaseModel):
    conversation_id: str
    message_content: str
    message_type: str = "text"  # text, image, document
    attachments: Optional[List[Dict[str, Any]]] = None

class ChatAccessRequestSchema(BaseModel):
    conversation_id: str
    request_reason: Optional[str] = None
    requested_duration_hours: Optional[int] = 24

class AccessResponseRequest(BaseModel):
    approved: bool
    response_notes: Optional[str] = None
    granted_duration_hours: Optional[int] = 24

# ============== HELPER FUNCTIONS ==============

def get_patient_context(patient_id: str) -> Dict[str, Any]:
    """Get patient context for LLM."""
    try:
        # Get patient info
        patient = supabase_admin.table("patients").select(
            "first_name, last_name, date_of_birth, gender, blood_type, allergies, chronic_conditions, current_medications"
        ).eq("id", patient_id).single().execute()
        
        # Get recent cases
        cases = supabase_admin.table("medical_cases").select(
            "case_number, status, diagnosis, chief_complaint, created_at"
        ).eq("patient_id", patient_id).order("created_at", desc=True).limit(5).execute()
        
        # Get recent ECG results
        ecg = supabase_admin.table("ecg_results").select(
            "heart_rate, rhythm_classification, detected_conditions, ai_interpretation, created_at"
        ).eq("patient_id", patient_id).eq("analysis_status", "completed").order("created_at", desc=True).limit(3).execute()
        
        # Get recent MRI results
        mri = supabase_admin.table("mri_segmentation_results").select(
            "detected_abnormalities, ai_interpretation, created_at"
        ).eq("patient_id", patient_id).eq("analysis_status", "completed").order("created_at", desc=True).limit(3).execute()
        
        return {
            "patient_info": patient.data if patient.data else {},
            "medical_history": cases.data if cases.data else [],
            "recent_ecg_results": ecg.data if ecg.data else [],
            "recent_mri_results": mri.data if mri.data else [],
            "context_generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get patient context error: {e}")
        return {}

async def generate_llm_response(message: str, context: Dict[str, Any], model: str = "gpt-4") -> str:
    """Generate LLM response (placeholder for actual LLM integration)."""
    # This is where you would integrate Cohere or other LLM
    # For now, return a simulated response
    
    if settings.cohere_api_key:
        # TODO: Integrate with Cohere API
        pass
    
    # Simulated medical AI response
    message_lower = message.lower()
    
    if "heart" in message_lower or "ecg" in message_lower or "cardiac" in message_lower:
        return "Based on the available ECG data, I can see the cardiac analysis results. For suspected cardiac conditions, our CNN-Transformer architecture achieves high accuracy in detecting arrhythmias. I recommend reviewing the latest lead II data and consulting with a cardiologist for comprehensive evaluation. Would you like me to explain any specific ECG findings?"
    
    elif "brain" in message_lower or "mri" in message_lower or "tumor" in message_lower:
        return "Brain tumor segmentation via our 3D U-Net model provides highly precise volumetric measurements. The MRI analysis includes detection of tumor regions, edema, and enhancing areas. For accurate interpretation, DICOM metadata analysis is essential. Would you like me to explain the segmentation results in more detail?"
    
    elif "medication" in message_lower or "drug" in message_lower:
        return "I can help review medication information. Please note that any medication changes should be discussed with and approved by your healthcare provider. What specific medication questions do you have?"
    
    elif "symptom" in message_lower or "pain" in message_lower:
        return "I understand you're experiencing symptoms. While I can provide general health information, it's important to have any new or concerning symptoms evaluated by your healthcare provider. Can you describe your symptoms in more detail so I can provide relevant information?"
    
    else:
        return "I've analyzed your query against clinical guidelines. As a medical AI assistant, I'm here to support your healthcare journey by providing information based on medical literature. However, please remember that I cannot replace professional medical advice. How can I assist you further with your health questions?"

# ============== ENDPOINTS ==============

@router.post("/conversations")
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new LLM conversation."""
    try:
        # Get hospital ID from patient
        patient = supabase_admin.table("patients").select(
            "hospital_id"
        ).eq("id", request.patient_id).single().execute()
        
        if not patient.data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        conversation_data = {
            "conversation_type": request.conversation_type,
            "patient_id": request.patient_id,
            "doctor_id": request.doctor_id,
            "case_id": request.case_id,
            "hospital_id": patient.data["hospital_id"],
            "title": request.title or "Medical Consultation",
            "system_prompt": request.system_prompt,
            "llm_model": request.llm_model,
            "is_active": True,
            "is_archived": False,
            "message_count": 0,
            "total_tokens_used": 0
        }
        
        result = supabase_admin.table("llm_conversations").insert(conversation_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        logger.info(f"✅ Conversation created: {result.data[0]['id']}")
        return {"success": True, "data": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/messages")
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message and get LLM response."""
    try:
        # Verify conversation exists and user has access
        conversation = supabase_admin.table("llm_conversations").select(
            "*, patients(id)"
        ).eq("id", request.conversation_id).single().execute()
        
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Determine sender type
        role = current_user["user_metadata"].get("role", "patient")
        sender_type = "doctor" if role in ["doctor", "administrator", "super_admin"] else "patient"
        
        # Get sender ID (profile ID, not auth ID)
        sender_id = None
        if sender_type == "patient":
            pat = supabase_admin.table("patients").select("id").eq("user_id", current_user["id"]).single().execute()
            if pat.data:
                sender_id = pat.data["id"]
        else:
            doc = supabase_admin.table("doctors").select("id").eq("user_id", current_user["id"]).single().execute()
            if doc.data:
                sender_id = doc.data["id"]
        
        # Get patient context for LLM
        patient_id = conversation.data["patient_id"]
        context = get_patient_context(patient_id)
        
        # Save user message
        user_message = {
            "conversation_id": request.conversation_id,
            "sender_type": sender_type,
            "sender_id": sender_id,
            "message_content": request.message_content,
            "message_type": request.message_type,
            "attachments": request.attachments or [],
            "llm_context_snapshot": context
        }
        
        user_msg_result = supabase_admin.table("llm_messages").insert(user_message).execute()
        
        # Generate LLM response
        llm_response = await generate_llm_response(
            request.message_content,
            context,
            conversation.data.get("llm_model", "gpt-4")
        )
        
        # Save LLM response
        llm_message = {
            "conversation_id": request.conversation_id,
            "sender_type": "llm",
            "sender_id": None,
            "message_content": llm_response,
            "message_type": "text",
            "llm_model_used": conversation.data.get("llm_model", "gpt-4"),
            "tokens_used": len(llm_response.split()) * 2,  # Rough estimate
            "llm_context_snapshot": context
        }
        
        llm_msg_result = supabase_admin.table("llm_messages").insert(llm_message).execute()
        
        # Update conversation stats
        supabase_admin.table("llm_conversations").update({
            "message_count": conversation.data.get("message_count", 0) + 2,
            "last_message_at": datetime.utcnow().isoformat()
        }).eq("id", request.conversation_id).execute()
        
        return {
            "success": True,
            "user_message": user_msg_result.data[0] if user_msg_result.data else None,
            "llm_response": llm_msg_result.data[0] if llm_msg_result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def list_conversations(
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """List conversations."""
    try:
        query = supabase_admin.table("llm_conversations").select(
            "*, patients(id, first_name, last_name), doctors(id, first_name, last_name)"
        ).eq("is_active", is_active).eq("is_archived", False)
        
        if patient_id:
            query = query.eq("patient_id", patient_id)
        if doctor_id:
            query = query.eq("doctor_id", doctor_id)
        
        query = query.order("last_message_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation with messages."""
    try:
        conversation = supabase_admin.table("llm_conversations").select(
            "*, patients(id, first_name, last_name), doctors(id, first_name, last_name)"
        ).eq("id", conversation_id).single().execute()
        
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages = supabase_admin.table("llm_messages").select(
            "*"
        ).eq("conversation_id", conversation_id).eq("is_deleted", False).order(
            "created_at", desc=False
        ).execute()
        
        conversation.data["messages"] = messages.data
        
        return {"success": True, "data": conversation.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, le=500),
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation messages."""
    try:
        result = supabase_admin.table("llm_messages").select(
            "*"
        ).eq("conversation_id", conversation_id).eq("is_deleted", False).order(
            "created_at", desc=False
        ).range(offset, offset + limit - 1).execute()
        
        return {"success": True, "data": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/access-requests")
async def request_chat_access(
    request: ChatAccessRequestSchema,
    current_user: dict = Depends(get_current_user)
):
    """Patient requests access to view doctor's conversation."""
    try:
        # Get patient ID
        patient = supabase_admin.table("patients").select("id").eq(
            "user_id", current_user["id"]
        ).single().execute()
        
        if not patient.data:
            raise HTTPException(status_code=403, detail="Only patients can request access")
        
        # Get conversation doctor
        conversation = supabase_admin.table("llm_conversations").select(
            "doctor_id, patient_id"
        ).eq("id", request.conversation_id).single().execute()
        
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if conversation.data["patient_id"] != patient.data["id"]:
            raise HTTPException(status_code=403, detail="You can only request access to conversations about yourself")
        
        access_request = {
            "patient_id": patient.data["id"],
            "conversation_id": request.conversation_id,
            "doctor_id": conversation.data["doctor_id"],
            "request_reason": request.request_reason,
            "requested_duration_hours": request.requested_duration_hours,
            "request_status": "pending"
        }
        
        result = supabase_admin.table("chat_access_requests").insert(access_request).execute()
        
        return {"success": True, "data": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request chat access error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/access-requests/{request_id}/respond")
async def respond_to_access_request(
    request_id: str,
    request: AccessResponseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Doctor approves or rejects access request."""
    try:
        # Get doctor ID
        doctor = supabase_admin.table("doctors").select("id").eq(
            "user_id", current_user["id"]
        ).single().execute()
        
        if not doctor.data:
            raise HTTPException(status_code=403, detail="Only doctors can respond to access requests")
        
        # Get access request
        access_req = supabase_admin.table("chat_access_requests").select(
            "*"
        ).eq("id", request_id).single().execute()
        
        if not access_req.data:
            raise HTTPException(status_code=404, detail="Access request not found")
        
        if access_req.data["doctor_id"] != doctor.data["id"]:
            raise HTTPException(status_code=403, detail="This request is not for your conversations")
        
        # Update request
        update_data = {
            "request_status": "approved" if request.approved else "rejected",
            "responded_at": datetime.utcnow().isoformat(),
            "response_notes": request.response_notes
        }
        
        if request.approved:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(hours=request.granted_duration_hours)
            update_data["granted_duration_hours"] = request.granted_duration_hours
            update_data["expires_at"] = expires_at.isoformat()
            
            # Create permission record
            permission = {
                "patient_id": access_req.data["patient_id"],
                "conversation_id": access_req.data["conversation_id"],
                "granted_by_doctor_id": doctor.data["id"],
                "request_id": request_id,
                "access_level": "read_only",
                "valid_until": expires_at.isoformat(),
                "is_active": True
            }
            supabase_admin.table("chat_access_permissions").insert(permission).execute()
        
        result = supabase_admin.table("chat_access_requests").update(update_data).eq(
            "id", request_id
        ).execute()
        
        return {"success": True, "data": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Respond to access request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
