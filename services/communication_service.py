import uuid
from datetime import datetime
from typing import Dict
import logging
from database import get_database
from models import ContactRequest, FeedbackRequest

class CommunicationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def submit_contact_form(self, contact_data: ContactRequest, user_id: str = None) -> Dict:
        try:
            database = await get_database()
            collection = database["contact_submissions"]
            
            ticket_id = f"contact_{uuid.uuid4().hex[:12]}"
            
            submission_data = {
                "ticket_id": ticket_id,
                "user_id": user_id,
                "name": contact_data.name,
                "email": contact_data.email,
                "subject": contact_data.subject,
                "message": contact_data.message,
                "status": "new",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await collection.insert_one(submission_data)
            
            self.logger.info(f"Contact form submitted: {ticket_id}")
            
            
            return {
                "success": True,
                "message": "Thank you for your message! We'll get back to you within 24-48 hours.",
                "ticket_id": ticket_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to submit contact form: {e}")
            return {
                "success": False,
                "message": "Failed to submit your message. Please try again later.",
                "ticket_id": None
            }

    async def submit_feedback(self, feedback_data: FeedbackRequest, user_id: str = None) -> Dict:
        try:
            database = await get_database()
            collection = database["feedback_submissions"]
            
            feedback_id = f"feedback_{uuid.uuid4().hex[:12]}"
            
            submission_data = {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "name": feedback_data.name,
                "email": feedback_data.email,
                "feedback_type": feedback_data.feedback_type,
                "title": feedback_data.title,
                "description": feedback_data.description,
                "priority": feedback_data.priority,
                "status": "new",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await collection.insert_one(submission_data)
            
            self.logger.info(f"Feedback submitted: {feedback_id} - Type: {feedback_data.feedback_type}")
            
            # TODO: Send notification based on priority and type
            # await self._send_feedback_notification(submission_data)
            
            response_message = self._get_feedback_response_message(feedback_data.feedback_type, feedback_data.priority)
            
            return {
                "success": True,
                "message": response_message,
                "feedback_id": feedback_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to submit feedback: {e}")
            return {
                "success": False,
                "message": "Failed to submit your feedback. Please try again later.",
                "feedback_id": None
            }

    def _get_feedback_response_message(self, feedback_type: str, priority: str) -> str:
        if feedback_type == "bug":
            if priority in ["high", "urgent"]:
                return "Thank you for reporting this bug! High priority issues are reviewed within 6-12 hours."
            else:
                return "Thank you for the bug report! We'll investigate this issue and get back to you soon."
        elif feedback_type == "feature":
            return "Thank you for your feature suggestion! We review all feature requests and prioritize them based on user demand and feasibility."
        else:
            return "Thank you for your feedback! We appreciate you taking the time to help us improve WebUnpack."

    async def get_user_submissions(self, user_id: str) -> Dict:
        try:
            database = await get_database()
            
            contact_collection = database["contact_submissions"]
            feedback_collection = database["feedback_submissions"]
            
            contact_submissions = await contact_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(10).to_list(length=10)
            
            feedback_submissions = await feedback_collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(10).to_list(length=10)
            
            # Clean up ObjectId for JSON serialization
            for submission in contact_submissions + feedback_submissions:
                submission["id"] = str(submission["_id"])
                del submission["_id"]
            
            return {
                "success": True,
                "contact_submissions": contact_submissions,
                "feedback_submissions": feedback_submissions
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user submissions: {e}")
            return {
                "success": False,
                "contact_submissions": [],
                "feedback_submissions": []
            }

communication_service = CommunicationService()
