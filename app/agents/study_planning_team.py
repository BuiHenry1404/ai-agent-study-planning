import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

from app.services.tools.agent_tools import save_schedule_json, load_schedule_json

class StudyPlanningTeam:
    """Study Planning Team using autogen framework with planner and calendar agents"""

    def __init__(self, llm_client: OpenAIChatCompletionClient, max_turns: int = 5):  # Giảm max_turns
        self.llm_client = llm_client
        self.max_turns = max_turns
        self.cancellation_token = CancellationToken()
        self.conversation_history: List[Dict[str, Any]] = []

        # Create agents & team
        self._create_agents()
        self._create_team()

    def _create_agents(self):
        """Create the PlannerAgent and CalendarAgent"""
        self.planner_agent = AssistantAgent(
            name="PlannerAgent",
            model_client=self.llm_client,
            tools=[save_schedule_json],
            system_message="""
You are an AI specialized in creating study plans.

1. Ask the user about their learning goals, subjects, and available time.
2. Then, generate a study schedule and present it in natural language (DO NOT show JSON).
3. If the user agrees → immediately call the `save_schedule_json` tool with JSON format like:

{
  "events": [
    {
      "summary": "Learn Math",
      "start": "2025-07-25T08:00:00",
      "end": "2025-07-25T09:30:00",
      "timeZone": "Asia/Ho_Chi_Minh",
      "description": "Review integrals"
    },
    ...
  ]
}

After calling `save_schedule_json`, do NOT say anything further and DO NOT print the json format for user. 
Wait for the CalendarAgent to handle syncing.
"""
        )

        self.calendar_agent = AssistantAgent(
            name="CalendarAgent",
            model_client=self.llm_client,
            tools=[load_schedule_json],
            system_message="""
You are a background agent that never communicates with the user.

Your only responsibility is:
- When the tool `save_schedule_json` has just been called and returned, immediately call `load_schedule_json` to sync the plan to Google Calendar.

Do not reply, explain, or display anything to the user. Just sync, then finish.
If syncing is successful, return: "Study plan synced to Google Calendar." and print link to the calendar.
If syncing fails, return: "Failed to sync study plan to Google Calendar."
"""
        )

        self.user_proxy = UserProxyAgent(
            name="User",
            input_func=self._get_user_input
        )

    def _create_team(self):
        """Create the selector group chat"""
        selector_prompt = """
Select the most appropriate agent to respond next.

Roles:
- PlannerAgent: Chats with the user, creates a study plan, and calls `save_schedule_json` when ready.
- CalendarAgent: If `save_schedule_json` was successfully called → calls `load_schedule_json` to sync to Google Calendar.
- User: Provides input, requests, or confirms changes to the plan.

Current conversation context:
{history}

Rules:
1. If the User is requesting or editing a study plan → select PlannerAgent
2. If PlannerAgent has not yet called `save_schedule_json` → keep PlannerAgent
3. If PlannerAgent just called the tool, or "✅ JSON SAVED" is in the history → select CalendarAgent
4. If CalendarAgent just finished syncing → select User
5. If unsure → select User
"""

        self.team = SelectorGroupChat(
            participants=[self.user_proxy, self.planner_agent, self.calendar_agent],
            model_client=self.llm_client,
            selector_prompt=selector_prompt,
            termination_condition=TextMentionTermination("EXIT"),
            allow_repeated_speaker=True,
            max_turns=self.max_turns
        )

    def _get_user_input(self, prompt: str) -> str:
        """Return the initial user message"""
        return self.initial_message

    async def run_conversation(self, user_message: str) -> Dict[str, Any]:
        """Run the study planning conversation"""
        try:
            self.initial_message = user_message
            self.conversation_history = []

            async for message in self.team.run_stream(
                task=user_message,
                cancellation_token=self.cancellation_token
            ):
                self.conversation_history.append({
                    "agent": getattr(message, "name", "Unknown"),
                    "content": getattr(message, "content", ""),  
                    "timestamp": datetime.now().isoformat(),
                    "type": "message"
                })

            return {
                "conversation_history": self.conversation_history,
                "final_message": self.conversation_history[-1] if self.conversation_history else None,
                "total_messages": len(self.conversation_history)
            }

        except Exception as e:
            return {"error": str(e), "conversation_history": self.conversation_history}

    async def run_conversation_with_socket(
        self,
        user_message: str,
        user_sid: str,
        task_id: str,
        socketio_service=None,
        output_stats: bool = True
    ) -> Dict[str, Any]:
        """Run the study planning conversation with Socket.IO streaming"""
        from autogen_agentchat.messages import TextMessage
        try:
            self.initial_message = user_message
            self.conversation_history = []

            async for message in self.team.run_stream(
                task=TextMessage(content=user_message, source="User"),
                cancellation_token=self.cancellation_token
            ):
                self.conversation_history.append({
                    "agent": getattr(message, "name", "Unknown"),
                    "content": getattr(message, "content", ""),
                    "timestamp": datetime.now().isoformat(),
                    "type": "message"
                })
                if socketio_service and hasattr(message, "content"):
                    await socketio_service.sio.emit('task_message', {
                        'task_id': task_id,
                        'type': 'stream',
                        'data': {
                            'message': str(getattr(message, "content", "")),
                            'agent': getattr(message, 'name', 'system')
                        }
                    }, room=user_sid)

            if socketio_service:
                await socketio_service.sio.emit('task_message', {
                    'task_id': task_id,
                    'type': 'complete',
                    'data': {
                        'message': 'Study planning conversation completed'
                    }
                }, room=user_sid)

            return {
                "success": True,
                "conversation_history": self.conversation_history,
                "final_message": self.conversation_history[-1] if self.conversation_history else None,
                "total_messages": len(self.conversation_history)
            }
        except Exception as e:
            import logging
            logging.error(f"Error in study planning conversation: {str(e)}")
            if socketio_service:
                await socketio_service.sio.emit('task_message', {
                    'task_id': task_id,
                    'type': 'error',
                    'data': {
                        'message': f"Error in conversation: {str(e)}"
                    }
                }, room=user_sid)
            return {
                "error": str(e),
                "conversation_history": self.conversation_history
            }

    async def save_state(self) -> Dict[str, Any]:
        """Save team state"""
        try:
            return await self.team.save_state()
        except Exception as e:
            return {"error": f"Failed to save state: {str(e)}"}

    async def load_state(self, state: Dict[str, Any]) -> bool:
        """Load saved team state"""
        try:
            await self.team.load_state(state)
            return True
        except Exception as e:
            print(f"Failed to load state: {str(e)}")
            return False

    def cancel_conversation(self):
        """Cancel conversation"""
        self.cancellation_token.cancel()





class StudyPlanningTeamManager:
    """Manager for StudyPlanningTeam instances"""

    def __init__(self):
        self.active_teams: Dict[str, StudyPlanningTeam] = {}

    def create_team(self, task_id: str, llm_client: OpenAIChatCompletionClient, max_turns: int = 10) -> StudyPlanningTeam:
        team = StudyPlanningTeam(llm_client, max_turns)
        self.active_teams[task_id] = team
        return team

    def get_team(self, task_id: str) -> Optional[StudyPlanningTeam]:
        return self.active_teams.get(task_id)

    def remove_team(self, task_id: str):
        if task_id in self.active_teams:
            del self.active_teams[task_id]

    def get_all_teams(self) -> Dict[str, StudyPlanningTeam]:
        return self.active_teams.copy()


# Global manager
study_planning_manager = StudyPlanningTeamManager()
