import os
import uuid
import json
import random
import re
from typing import List, TypedDict, Optional, Dict, Any, Literal
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from pathlib import Path
from math import ceil

import dateparser
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


# ─────────────────────────────────────────────────────────────
# 1) Secure model setup
# ─────────────────────────────────────────────────────────────

GOOGLE_API_KEY = ""
MODEL_ID = "gemini-2.0-flash"

llm = ChatGoogleGenerativeAI(
    model=MODEL_ID,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3,
)


# ─────────────────────────────────────────────────────────────
# 2) Typed state with break management AND academic events
# ─────────────────────────────────────────────────────────────

class BlockType:
    CLASS = "class"
    STUDY = "study"
    BREAK = "break"
    MEAL = "meal"
    PERSONAL = "personal"
    EXERCISE = "exercise"
    # Academic event types (for blocks if user wants to schedule study time for them)
    EXAM = "exam_study"
    TEST = "test_study"
    QUIZ = "quiz_study"
    VIVA = "viva_study"
    PROJECT = "project_work"
    DEADLINE = "deadline_work"

class AcademicEventType:
    EXAM = "exam"
    TEST = "test"
    QUIZ = "quiz"
    VIVA = "viva"
    PROJECT = "project"
    DEADLINE = "deadline"
    PRESENTATION = "presentation"
    ASSIGNMENT = "assignment"

class Block(TypedDict):
    id: str
    task: str
    start_iso: str
    end_iso: str
    block_type: str
    priority: Optional[int]

class AcademicEvent(TypedDict):
    id: str
    title: str
    event_type: str
    date_iso: str
    importance: str
    subject: Optional[str]
    notes: Optional[str]
    reminder_days: Optional[int]

class AppState(TypedDict):
    blocks: List[Block]
    timezone: str
    break_preferences: Dict[str, Any]
    academic_events: List[AcademicEvent]  # NEW: For tracking exams, tests, deadlines

# Initialize with default break settings
state: AppState = {
    "blocks": [], 
    "timezone": "Asia/Kolkata",
    "break_preferences": {
        "study_break_ratio": 0.2,
        "min_break_duration": 5,
        "max_study_block": 90,
        "break_activities": ["walk", "stretch", "water", "snack", "eyes", "breathe"]
    },
    "academic_events": []  # NEW: Initialize empty academic events list
}


# ─────────────────────────────────────────────────────────────
# 3) State persistence manager
# ─────────────────────────────────────────────────────────────

class PersistentStateManager:
    def __init__(self, user_id: str, file_path: str = "timetable_state"):
        # Create user-specific file path
        self.file_path = Path(f"{file_path}_{user_id}.json")
        self.user_id = user_id
        self.load_state()
    
    def load_state(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    if "blocks" in data:
                        state["blocks"] = data["blocks"]
                    if "timezone" in data:
                        state["timezone"] = data["timezone"]
                    if "break_preferences" in data:
                        state["break_preferences"].update(data["break_preferences"])
                    if "academic_events" in data:
                        state["academic_events"] = data["academic_events"]
            except Exception as e:
                print(f"Error loading state: {e}")
        else:
            # Initialize empty state for new user
            state["blocks"] = []
            state["academic_events"] = []
    
    def save_state(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")




# ─────────────────────────────────────────────────────────────
# 4) Helpers with break management AND academic events
# ─────────────────────────────────────────────────────────────

def _get_tz() -> ZoneInfo:
    """Return the user's configured ZoneInfo."""
    try:
        return ZoneInfo(state["timezone"])
    except Exception:
        return ZoneInfo("UTC")

def _parse_span(start_text: str, duration_min: int, tz: str) -> tuple[datetime, datetime]:
    """Parse a natural-language start time and compute the end time with duration."""
    settings = {
        "TIMEZONE": tz,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }
    start_dt = dateparser.parse(start_text, settings=settings)
    if not start_dt:
        raise ValueError(f"Could not parse start time from: {start_text!r}")
    end_dt = start_dt + timedelta(minutes=duration_min)
    return start_dt, end_dt

def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Return True if [a_start, a_end) overlaps [b_start, b_end)."""
    return max(a_start, b_start) < min(a_end, b_end)

def _has_overlap(s: datetime, e: datetime, blocks: List[Block]) -> bool:
    """Check new span [s, e) against all existing blocks."""
    for b in blocks:
        bs = datetime.fromisoformat(b["start_iso"])
        be = datetime.fromisoformat(b["end_iso"])
        if _overlaps(s, e, bs, be):
            return True
    return False

def _fmt_local(dt: datetime, tz: ZoneInfo) -> str:
    """Format a datetime in the given timezone for display."""
    local = dt.astimezone(tz)
    return local.strftime("%a %Y-%m-%d %H:%M")

def _fmt_range(block: Block, tz: ZoneInfo) -> str:
    """Return a human-friendly local time range for a block."""
    s = datetime.fromisoformat(block["start_iso"]).astimezone(tz)
    e = datetime.fromisoformat(block["end_iso"]).astimezone(tz)
    day = s.strftime("%a %Y-%m-%d")
    return f"{day} {s.strftime('%H:%M')}–{e.strftime('%H:%M')}"

def _sort_blocks_in_place():
    state["blocks"].sort(key=lambda b: b["start_iso"])

def _calculate_optimal_breaks(study_duration: int) -> List[Dict]:
    """Calculate optimal break schedule based on study duration."""
    break_prefs = state["break_preferences"]
    min_break = break_prefs["min_break_duration"]
    max_study = break_prefs["max_study_block"]
    
    breaks = []
    
    # If study session is longer than max allowed, split it
    if study_duration > max_study:
        num_sessions = ceil(study_duration / max_study)
        session_duration = study_duration / num_sessions
        break_duration = max(min_break, session_duration * break_prefs["study_break_ratio"])
        
        for i in range(num_sessions - 1):
            breaks.append({
                "duration": break_duration,
                "type": "break",
                "activity": random.choice(break_prefs["break_activities"])
            })
    
    return breaks

def _schedule_with_breaks(task: str, start: datetime, total_duration: int) -> List[Block]:
    """Schedule a study session with built-in breaks."""
    breaks = _calculate_optimal_breaks(total_duration)
    blocks = []
    current_time = start
    
    if not breaks:
        # Short session, no breaks needed
        end_time = current_time + timedelta(minutes=total_duration)
        blocks.append({
            "id": str(uuid.uuid4())[:8],
            "task": task,
            "start_iso": current_time.isoformat(),
            "end_iso": end_time.isoformat(),
            "block_type": BlockType.STUDY,
            "priority": 2
        })
        return blocks
    
    # Split into study blocks with breaks
    study_blocks = len(breaks) + 1
    study_duration_per_block = total_duration // study_blocks
    
    for i in range(study_blocks):
        # Study block
        end_study = current_time + timedelta(minutes=study_duration_per_block)
        blocks.append({
            "id": str(uuid.uuid4())[:8],
            "task": f"{task} (Part {i+1}/{study_blocks})",
            "start_iso": current_time.isoformat(),
            "end_iso": end_study.isoformat(),
            "block_type": BlockType.STUDY,
            "priority": 2
        })
        
        # Break block (if not the last iteration)
        if i < len(breaks):
            break_info = breaks[i]
            current_time = end_study
            end_break = current_time + timedelta(minutes=break_info["duration"])
            blocks.append({
                "id": str(uuid.uuid4())[:8],
                "task": f"Break: {break_info['activity']}",
                "start_iso": current_time.isoformat(),
                "end_iso": end_break.isoformat(),
                "block_type": BlockType.BREAK,
                "priority": 3
            })
            current_time = end_break
    
    return blocks

def _find_available_slots(desired_start: datetime, desired_duration: int, 
                         search_range_hours: int = 6) -> List[datetime]:
    """Find available time slots near the desired time."""
    tz = _get_tz()
    available_slots = []
    
    # Check before and after the desired time
    for hours_offset in range(-search_range_hours, search_range_hours + 1, 1):
        if hours_offset == 0:
            continue
            
        test_start = desired_start + timedelta(hours=hours_offset)
        test_end = test_start + timedelta(minutes=desired_duration)
        
        if not _has_overlap(test_start, test_end, state["blocks"]):
            available_slots.append(test_start)
    
    return available_slots

def _validate_time_input(start_text: str, duration_min: int) -> List[str]:
    """Validate time inputs and return error messages."""
    errors = []
    
    if duration_min < 1:
        errors.append("Duration must be at least 1 minute")
    
    if duration_min > 480:  # 8 hours
        errors.append("Duration cannot exceed 8 hours for a single block")
    
    # Test if dateparser can understand the input
    test_parse = dateparser.parse(start_text, settings={"PREFER_DATES_FROM": "future"})
    if not test_parse:
        errors.append(f"Could not understand the time: '{start_text}'")
    
    return errors

def _preprocess_input(user_input: str) -> str:
    """Pre-process user input to handle common patterns and multiple commands."""
    input_lower = user_input.lower()
    
    # Handle greetings
    if input_lower in ["hello", "hi", "hey"]:
        return "hello"
    
    # Handle timetable requests
    if any(phrase in input_lower for phrase in ["timetable", "schedule", "show my", "what's my", "give the timetable"]):
        return "show my timetable"
    
    # Handle academic calendar requests
    if any(phrase in input_lower for phrase in ["exam", "test", "quiz", "viva", "project", "deadline", "academic calendar"]):
        return "show academic calendar"
    
    # Handle remove commands - try to extract block ID
    if "remove" in input_lower or "delete" in input_lower:
        # Look for ID patterns like "id=abc123" or similar
        id_match = re.search(r'id[=:]\s*(\w+)', input_lower)
        if id_match:
            return f"remove block with id {id_match.group(1)}"
        else:
            return "I want to remove a block but need the ID. Can you show the timetable first?"
    
    # Handle add commands
    if "add" in input_lower or "schedule" in input_lower:
        return user_input
    
    # Handle the specific case from your example
    if "revised schedule" in input_lower or "like this" in input_lower:
        return "I see you mentioned a schedule. What specific changes would you like to make to your timetable?"
    
    return user_input

# NEW: Academic event helpers
def _get_upcoming_events(days: int = 30) -> List[AcademicEvent]:
    """Get academic events happening in the next specified days."""
    tz = _get_tz()
    now = datetime.now(tz)
    future = now + timedelta(days=days)
    
    upcoming_events = []
    for event in state["academic_events"]:
        event_date = datetime.fromisoformat(event["date_iso"]).astimezone(tz)
        if now <= event_date <= future:
            upcoming_events.append(event)
    
    # Sort by date
    upcoming_events.sort(key=lambda e: datetime.fromisoformat(e["date_iso"]))
    return upcoming_events

def _get_events_by_subject(subject: str) -> List[AcademicEvent]:
    """Get academic events for a specific subject."""
    subject_lower = subject.lower()
    return [e for e in state["academic_events"] 
            if e.get("subject") and subject_lower in e["subject"].lower()]

def _check_event_conflicts(event_date: datetime, event_type: str) -> List[Block]:
    """Check if there are scheduling conflicts with existing events."""
    tz = _get_tz()
    event_date_only = event_date.date()
    
    conflicts = []
    for block in state["blocks"]:
        block_start = datetime.fromisoformat(block["start_iso"]).astimezone(tz)
        if block_start.date() == event_date_only:
            conflicts.append(block)
    
    return conflicts


# ─────────────────────────────────────────────────────────────
# 5) Structured tools with break management AND academic events
# ─────────────────────────────────────────────────────────────

class ShowArgs(BaseModel):
    pass

@tool("show_timetable", args_schema=ShowArgs)
def show_timetable() -> str:
    """Show the current timetable with break awareness."""
    try:
        if not state["blocks"]:
            return "⏳ Your timetable is empty. Use 'add_block' to schedule something!"
        
        tz = _get_tz()
        now = datetime.now(tz)
        
        lines = ["📅 Your Current Timetable:"]
        lines.append("Time | Duration | Type | Task | ID")
        lines.append("-" * 60)
        
        total_study = 0
        total_break = 0
        
        for b in state["blocks"]:
            start = datetime.fromisoformat(b["start_iso"]).astimezone(tz)
            end = datetime.fromisoformat(b["end_iso"]).astimezone(tz)
            duration = (end - start).total_seconds() / 60
            
            # Track totals by type
            if b.get("block_type") == BlockType.STUDY:
                total_study += duration
            elif b.get("block_type") == BlockType.BREAK:
                total_break += duration
            
            # Determine status and emoji
            status_emoji = "📚" if b.get("block_type") == BlockType.STUDY else "☕"
            if "break" in b.get("block_type", "").lower():
                status_emoji = "☕"
            elif "class" in b.get("block_type", "").lower():
                status_emoji = "🎓"
            
            lines.append(
                f"{_fmt_range(b, tz)} | {duration:.0f}min | {b.get('block_type', 'task')} | {status_emoji} {b['task']} | id={b['id']}"
            )
        
        lines.append("-" * 60)
        
        # Add study-break ratio analysis
        if total_study > 0:
            actual_ratio = total_break / total_study if total_study > 0 else 0
            target_ratio = state["break_preferences"]["study_break_ratio"]
            
            ratio_status = "✅ Good balance" if abs(actual_ratio - target_ratio) < 0.05 else \
                          "⚠️ Needs more breaks" if actual_ratio < target_ratio else "⚠️ Many breaks"
            
            lines.append(f"Study: {total_study:.0f}min, Breaks: {total_break:.0f}min, Ratio: {actual_ratio:.2f} ({ratio_status})")
        
        # NEW: Add upcoming academic events notice
        upcoming_events = _get_upcoming_events(7)  # Next 7 days
        if upcoming_events:
            lines.append("\n📢 Upcoming Academic Events (next 7 days):")
            for event in upcoming_events[:3]:  # Show max 3
                event_date = datetime.fromisoformat(event["date_iso"]).astimezone(tz)
                days_until = (event_date.date() - now.date()).days
                lines.append(f"   {event_date.strftime('%a %m/%d')}: {event['title']} ({days_until} days)")
            if len(upcoming_events) > 3:
                lines.append(f"   ... and {len(upcoming_events) - 3} more events")
        
        lines.append("💡 To remove a block, use: 'remove id=YOUR_BLOCK_ID'")
        lines.append("💡 To add a block, use: 'add [task] at [time] for [duration] minutes'")
        lines.append("💡 To view academic events, use: 'show academic calendar'")
        
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error showing timetable: {str(e)}"


class AddArgs(BaseModel):
    task: str = Field(..., description="Task name")
    start: str = Field(..., description="Natural-language start time, e.g. 'tomorrow 9 am' or '2025-08-28 09:30'")
    duration_min: int = Field(..., ge=1, le=1440, description="Duration in minutes (1..1440)")
    block_type: str = Field(BlockType.STUDY, description="Type of block: study, class, break, meal, personal, exercise")

@tool("add_block", args_schema=AddArgs)
def add_block(task: str, start: str, duration_min: int, block_type: str = BlockType.STUDY) -> str:
    """Insert a new block with automatic break scheduling for study sessions."""
    # Validate first
    errors = _validate_time_input(start, duration_min)
    if errors:
        return "❌ " + ". ".join(errors)
    
    try:
        tz_name = state["timezone"]
        s, e = _parse_span(start, duration_min, tz_name)
        
        # NEW: Check for academic event conflicts
        if block_type == BlockType.STUDY:
            # Check if this study session conflicts with important academic events
            event_conflicts = _check_event_conflicts(s, block_type)
            if event_conflicts:
                conflict_info = []
                for conflict in event_conflicts:
                    conflict_start = datetime.fromisoformat(conflict["start_iso"]).astimezone(_get_tz())
                    conflict_info.append(f"{conflict['task']} at {conflict_start.strftime('%H:%M')}")
                
                return f"❌ This time conflicts with: {', '.join(conflict_info)}. Consider another time."
        
        # Check for overlaps with all proposed blocks
        if block_type == BlockType.STUDY and duration_min > 45:
            # For longer study sessions, schedule with breaks
            study_blocks = _schedule_with_breaks(task, s, duration_min)
            
            # Check if all blocks can be placed without overlap
            all_blocks_valid = True
            for block in study_blocks:
                block_start = datetime.fromisoformat(block["start_iso"])
                block_end = datetime.fromisoformat(block["end_iso"])
                if _has_overlap(block_start, block_end, state["blocks"]):
                    all_blocks_valid = False
                    break
            
            if not all_blocks_valid:
                # Find alternative times
                alternatives = _find_available_slots(s, duration_min)
                if alternatives:
                    tz = _get_tz()
                    alt_str = ", ".join([_fmt_local(alt, tz) for alt in alternatives[:3]])
                    return f"❌ Cannot schedule study session - conflicts with existing blocks. Try these times: {alt_str}"
                return "❌ Cannot schedule study session - conflicts with existing blocks. No nearby available times found."
            
            # Add all blocks
            for block in study_blocks:
                state["blocks"].append(block)
            
            _sort_blocks_in_place()
            state_manager.save_state()
            
            tz = _get_tz()
            response = f"✅ Scheduled '{task}' with built-in breaks:\n"
            for block in study_blocks:
                if block["block_type"] == BlockType.STUDY:
                    response += f"   📚 {_fmt_range(block, tz)} - {block['task']}\n"
                else:
                    response += f"   ☕ {_fmt_range(block, tz)} - {block['task']}\n"
            return response
        
        else:
            # Regular block addition (non-study or short study)
            if _has_overlap(s, e, state["blocks"]):
                # Find alternative times
                alternatives = _find_available_slots(s, duration_min)
                if alternatives:
                    tz = _get_tz()
                    alt_str = ", ".join([_fmt_local(alt, tz) for alt in alternatives[:3]])
                    return f"❌ Overlaps with existing block. Try these times: {alt_str}"
                return "❌ Overlaps with an existing block. No nearby available times found."
            
            newb: Block = {
                "id": str(uuid.uuid4())[:8],
                "task": task,
                "start_iso": s.isoformat(),
                "end_iso": e.isoformat(),
                "block_type": block_type,
                "priority": 1 if block_type == BlockType.CLASS else 2
            }
            state["blocks"].append(newb)
            _sort_blocks_in_place()
            state_manager.save_state()
            
            tz = _get_tz()
            return f"✅ Added '{task}' at {_fmt_local(s, tz)}–{e.astimezone(tz).strftime('%H:%M')} ({state['timezone']}). ID={newb['id']}"
    
    except Exception as ex:
        return f"❌ Add failed: {ex}"


class RemoveArgs(BaseModel):
    id: str = Field(..., description="Block ID to remove")

@tool("remove_block", args_schema=RemoveArgs)
def remove_block(id: str) -> str:
    """Remove a block by its ID."""
    before = len(state["blocks"])
    state["blocks"] = [b for b in state["blocks"] if b["id"] != id]
    after = len(state["blocks"])
    if after < before:
        state_manager.save_state()
        return "🗑️ Removed."
    return "No block with that ID."


class UpdateArgs(BaseModel):
    id: str = Field(..., description="Block ID to update")
    new_start: Optional[str] = Field(None, description="New natural-language start time")
    new_duration_min: Optional[int] = Field(None, ge=1, le=1440, description="New duration in minutes")
    new_task: Optional[str] = Field(None, description="Rename the task to this value")
    new_block_type: Optional[str] = Field(None, description="Change the block type")

@tool("update_block", args_schema=UpdateArgs)
def update_block(id: str, new_start: Optional[str] = None, new_duration_min: Optional[int] = None, 
                new_task: Optional[str] = None, new_block_type: Optional[str] = None) -> str:
    """Update a block by ID: start time, duration, task name, and/or block type."""
    try:
        target = None
        for b in state["blocks"]:
            if b["id"] == id:
                target = b
                break
        if not target:
            return "No block with that ID."

        # Preserve existing values if not provided
        tz_name = state["timezone"]
        s = (
            dateparser.parse(new_start, settings={"TIMEZONE": tz_name, "RETURN_AS_TIMEZONE_AWARE": True, "PREFER_DATES_FROM": "future"})
            if new_start
            else datetime.fromisoformat(target["start_iso"])
        )
        current_duration_min = int(
            (datetime.fromisoformat(target["end_iso"]) - datetime.fromisoformat(target["start_iso"]))
            .total_seconds() // 60
        )
        dur = new_duration_min or current_duration_min
        e = s + timedelta(minutes=dur)

        # Check overlap excluding the target itself
        others = [x for x in state["blocks"] if x["id"] != id]
        for b in others:
            bs = datetime.fromisoformat(b["start_iso"])
            be = datetime.fromisoformat(b["end_iso"])
            if _overlaps(s, e, bs, be):
                return "❌ Update would overlap another block."

        target["start_iso"] = s.isoformat()
        target["end_iso"] = e.isoformat()
        if new_task:
            target["task"] = new_task
        if new_block_type:
            target["block_type"] = new_block_type
        
        _sort_blocks_in_place()
        state_manager.save_state()
        tz = _get_tz()
        return f"✏️ Updated: {_fmt_range(target, tz)}  |  {target['task']}  |  id={target['id']}"
    except Exception as ex:
        return f"❌ Update failed: {ex}"


class SetTZArgs(BaseModel):
    timezone: str = Field(..., description="IANA timezone, e.g. 'Asia/Kolkata', 'Europe/London', 'UTC'")

@tool("set_timezone", args_schema=SetTZArgs)
def set_timezone(timezone: str) -> str:
    """Set the default IANA timezone for parsing and displaying times."""
    try:
        _ = ZoneInfo(timezone)  # validate
        state["timezone"] = timezone
        state_manager.save_state()
        return f"🌐 Timezone set to {timezone}."
    except Exception:
        return "❌ Invalid timezone. Please provide a valid IANA timezone (e.g., 'Asia/Kolkata', 'UTC')."


class ExportIcsArgs(BaseModel):
    path: Optional[str] = Field(None, description="Optional file path to save the ICS calendar. If omitted, returns ICS text.")

@tool("export_ics", args_schema=ExportIcsArgs)
def export_ics(path: Optional[str] = None) -> str:
    """Export the current timetable as an iCalendar (.ics) string or save to a file."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//College Companion//Timetable Agent//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    
    for b in state["blocks"]:
        uid = f"{b['id']}@college-companion"
        dtstart = datetime.fromisoformat(b["start_iso"])
        dtend = datetime.fromisoformat(b["end_iso"])
        dtstart_utc = dtstart.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        dtend_utc = dtend.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        summary = b["task"].replace("\n", " ")
        created = datetime.now().astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART:{dtstart_utc}",
            f"DTEND:{dtend_utc}",
            f"SUMMARY:{summary}",
            f"DTSTAMP:{created}",
            f"CREATED:{created}",
            f"LAST-MODIFIED:{created}",
            "SEQUENCE:0",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "END:VEVENT",
        ]
    
    # NEW: Add academic events to ICS export
    for event in state["academic_events"]:
        uid = f"{event['id']}@college-companion-event"
        dtstart = datetime.fromisoformat(event["date_iso"]).replace(hour=9, minute=0, second=0)  # Default to 9 AM
        dtend = dtstart + timedelta(hours=2)  # Default 2-hour event
        dtstart_utc = dtstart.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        dtend_utc = dtend.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        summary = f"{event['event_type'].upper()}: {event['title']}"
        created = datetime.now().astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
        
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;VALUE=DATE:{dtstart.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(dtstart + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{summary}",
            f"DTSTAMP:{created}",
            f"CREATED:{created}",
            f"LAST-MODIFIED:{created}",
            "SEQUENCE:0",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",  # All-day event
            "END:VEVENT",
        ]
    
    lines.append("END:VCALENDAR")
    ics_text = "\n".join(lines)
    
    if path:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(ics_text)
            return f"📤 ICS calendar exported to {path}"
        except Exception as ex:
            return f"❌ Failed to write ICS: {ex}"
    
    return f"📅 Here's your timetable in ICS format:\n\n{ics_text}"


class SetBreakPreferencesArgs(BaseModel):
    study_break_ratio: Optional[float] = Field(None, ge=0.1, le=0.4, description="Break time as ratio of study time (0.1-0.4)")
    min_break_duration: Optional[int] = Field(None, ge=5, le=30, description="Minimum break duration in minutes (5-30)")
    max_study_block: Optional[int] = Field(None, ge=30, le=120, description="Maximum study block duration (30-120 minutes)")

@tool("set_break_preferences", args_schema=SetBreakPreferencesArgs)
def set_break_preferences(study_break_ratio: Optional[float] = None, 
                         min_break_duration: Optional[int] = None,
                         max_study_block: Optional[int] = None) -> str:
    """Configure your break preferences for optimal studying."""
    prefs = state["break_preferences"]
    
    if study_break_ratio:
        prefs["study_break_ratio"] = study_break_ratio
    if min_break_duration:
        prefs["min_break_duration"] = min_break_duration
    if max_study_block:
        prefs["max_study_block"] = max_study_block
    
    state_manager.save_state()
    return f"✅ Break preferences updated: {prefs}"


class SuggestBreakArgs(BaseModel):
    current_focus: Optional[str] = Field(None, description="What you're currently working on")

@tool("suggest_break", args_schema=SuggestBreakArgs)
def suggest_break(current_focus: Optional[str] = None) -> str:
    """Get a personalized break suggestion based on your current activity."""
    prefs = state["break_preferences"]
    activity = random.choice(prefs["break_activities"])
    
    suggestions = {
        "walk": "Take a 5-minute walk outside to refresh your mind and get some sunlight.",
        "stretch": "Do some quick stretches to relieve muscle tension and improve circulation.",
        "water": "Hydrate yourself! Drink a glass of water to stay focused and energized.",
        "snack": "Have a healthy snack like nuts or fruit to replenish your energy.",
        "eyes": "Rest your eyes by looking at something 20 feet away for 20 seconds.",
        "breathe": "Practice deep breathing for 1 minute to reduce stress and improve focus."
    }
    
    base_suggestion = suggestions.get(activity, "Take a short break to refresh yourself.")
    
    if current_focus:
        focus_specific = {
            "math": "Math can be mentally taxing. " + base_suggestion,
            "reading": "Reading for long periods strains eyes. " + base_suggestion,
            "coding": "Coding requires intense focus. " + base_suggestion,
            "writing": "Writing benefits from fresh perspectives. " + base_suggestion
        }
        return focus_specific.get(current_focus.lower(), base_suggestion)
    
    return base_suggestion


class RecommendStudyArgs(BaseModel):
    subject: str = Field(..., description="Subject to study")
    priority: str = Field("medium", description="Priority: low, medium, high")
    desired_duration: int = Field(60, description="Desired total study time in minutes")

@tool("recommend_study_session", args_schema=RecommendStudyArgs)
def recommend_study_session(subject: str, priority: str = "medium", desired_duration: int = 60) -> str:
    """Get smart recommendations for when to schedule a study session."""
    # NEW: Check for upcoming events for this subject
    subject_events = _get_events_by_subject(subject)
    upcoming_events = [e for e in subject_events 
                      if datetime.fromisoformat(e["date_iso"]).date() >= datetime.now().date()]
    
    # For simplicity, just find the next available slot
    tz = _get_tz()
    now = datetime.now(tz)
    
    # Look for slots in the next 3 days
    for day_offset in range(0, 3):
        test_date = now + timedelta(days=day_offset)
        
        # Try morning (9 AM), afternoon (2 PM), and evening (7 PM)
        for hour in [9, 14, 19]:
            test_time = test_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            test_end = test_time + timedelta(minutes=desired_duration)
            
            if test_time > now and not _has_overlap(test_time, test_end, state["blocks"]):
                response = (
                    f"📚 Recommended study time for {subject}:\n"
                    f"   ⏰ {test_time.strftime('%A at %H:%M')}\n"
                    f"   🕒 {desired_duration} minutes with built-in breaks\n"
                )
                
                # NEW: Add event information if relevant
                if upcoming_events:
                    next_event = min(upcoming_events, key=lambda e: datetime.fromisoformat(e["date_iso"]))
                    event_date = datetime.fromisoformat(next_event["date_iso"]).astimezone(tz)
                    days_until = (event_date.date() - now.date()).days
                    
                    response += (
                        f"\n📢 Upcoming {next_event['event_type']}: {next_event['title']} "
                        f"in {days_until} days on {event_date.strftime('%A, %b %d')}\n"
                    )
                
                response += "   💡 Use 'add_block' to schedule this session"
                return response
    
    return "❌ No suitable time slots found in the next 3 days. Consider rescheduling other activities."


class HelpArgs(BaseModel):
    pass

@tool("help", args_schema=HelpArgs)
def help_command() -> str:
    """Show help information for using the timetable agent."""
    return """
🤖 **Timetable Agent Help**

**Basic Commands:**
- `show timetable` - View your current schedule
- `add [task] at [time] for [duration]` - Add a new block (e.g., "add study at 9am for 60 minutes")
- `remove id=[block_id]` - Remove a block by ID
- `show academic calendar` - View your exams, tests, and deadlines
- `add academic event` - Add an exam, test, or deadline
- `help` - Show this help message

**Examples:**
- "add Android Studio at 6am for 90 minutes"
- "remove id=abc123"
- "show my timetable"
- "add academic event: Math Final Exam on December 15"
- "what's scheduled for tomorrow?"

**Pro Tips:**
- I automatically add breaks for study sessions longer than 45 minutes
- Use natural language for times: "tomorrow 9am", "next monday 2pm"
- Block IDs are shown in the timetable display
- I'll warn you about conflicts with upcoming exams and deadlines

What would you like to do?
"""


class ResetArgs(BaseModel):
    pass

@tool("reset", args_schema=ResetArgs)
def reset_timetable() -> str:
    """Completely reset the timetable and start fresh."""
    state["blocks"] = []
    state["academic_events"] = []  # NEW: Also reset academic events
    state_manager.save_state()
    return "✅ Timetable completely reset. You now have an empty schedule."


# NEW: Academic event tools
class AddAcademicEventArgs(BaseModel):
    title: str = Field(..., description="Title of the academic event (e.g., 'Math Final Exam')")
    event_type: Literal["exam", "test", "quiz", "viva", "project", "deadline", "presentation", "assignment"] = Field(..., description="Type of academic event")
    date: str = Field(..., description="Date of the event in natural language (e.g., 'next monday', 'december 15')")
    importance: Literal["high", "medium", "low"] = Field("medium", description="Importance level of the event")
    subject: Optional[str] = Field(None, description="Subject or course this event relates to")
    notes: Optional[str] = Field(None, description="Additional notes about the event")
    reminder_days: Optional[int] = Field(7, description="How many days before the event to remind you")

@tool("add_academic_event", args_schema=AddAcademicEventArgs)
def add_academic_event(title: str, event_type: str, date: str, importance: str = "medium", 
                      subject: Optional[str] = None, notes: Optional[str] = None, 
                      reminder_days: Optional[int] = 7) -> str:
    """Add an academic event (exam, test, deadline) to your calendar."""
    try:
        tz_name = state["timezone"]
        parsed_date = dateparser.parse(date, settings={
            "TIMEZONE": tz_name,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future"
        })
        
        if not parsed_date:
            return "❌ Could not understand the date. Please try again with a different format."
        
        event: AcademicEvent = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "event_type": event_type,
            "date_iso": parsed_date.isoformat(),
            "importance": importance,
            "subject": subject,
            "notes": notes,
            "reminder_days": reminder_days
        }
        
        state["academic_events"].append(event)
        state_manager.save_state()
        
        tz = _get_tz()
        event_date = parsed_date.astimezone(tz)
        days_until = (event_date.date() - datetime.now(tz).date()).days
        
        # Check for conflicts
        conflicts = _check_event_conflicts(parsed_date, event_type)
        conflict_msg = ""
        if conflicts:
            conflict_msg = f"\n⚠️ Note: This conflicts with {len(conflicts)} existing schedule item(s)."
        
        return (f"✅ Added academic event: {title} ({event_type}) on {event_date.strftime('%A, %B %d')} "
                f"(in {days_until} days).{conflict_msg}")
    
    except Exception as e:
        return f"❌ Failed to add academic event: {str(e)}"


class ShowAcademicCalendarArgs(BaseModel):
    timeframe: Literal["week", "month", "all"] = Field("month", description="Timeframe to show events for")

@tool("show_academic_calendar", args_schema=ShowAcademicCalendarArgs)
def show_academic_calendar(timeframe: str = "month") -> str:
    """Show your academic calendar with exams, tests, and deadlines."""
    if not state["academic_events"]:
        return "📅 Your academic calendar is empty. Add events using 'add_academic_event'."
    
    tz = _get_tz()
    now = datetime.now(tz)
    
    # Filter events based on timeframe
    if timeframe == "week":
        end_date = now + timedelta(days=7)
        filtered_events = [e for e in state["academic_events"] 
                          if now.date() <= datetime.fromisoformat(e["date_iso"]).date() <= end_date.date()]
        timeframe_desc = "next 7 days"
    elif timeframe == "month":
        end_date = now + timedelta(days=30)
        filtered_events = [e for e in state["academic_events"] 
                          if now.date() <= datetime.fromisoformat(e["date_iso"]).date() <= end_date.date()]
        timeframe_desc = "next 30 days"
    else:  # all
        filtered_events = state["academic_events"]
        timeframe_desc = "all upcoming"
    
    if not filtered_events:
        return f"📅 No academic events found for the {timeframe_desc}."
    
    # Sort by date
    filtered_events.sort(key=lambda x: x["date_iso"])
    
    lines = [f"📅 Academic Calendar ({timeframe_desc}):"]
    lines.append("Date | Type | Title | Importance | Days Left")
    lines.append("-" * 70)
    
    for event in filtered_events:
        event_date = datetime.fromisoformat(event["date_iso"]).astimezone(tz)
        days_left = (event_date.date() - now.date()).days
        
        # Emoji based on event type
        type_emoji = {
            "exam": "📝", "test": "🧪", "quiz": "❓", "viva": "🎤",
            "project": "📁", "deadline": "⏰", "presentation": "📊", "assignment": "📄"
        }.get(event["event_type"], "📅")
        
        # Color based on importance
        importance_emoji = {
            "high": "🔴", "medium": "🟡", "low": "🟢"
        }.get(event["importance"], "⚪")
        
        lines.append(
            f"{event_date.strftime('%m/%d')} | {type_emoji} {event['event_type']} | "
            f"{event['title']} | {importance_emoji} {event['importance']} | "
            f"{days_left} day(s)"
        )
    
    lines.append("-" * 70)
    lines.append("💡 Use 'add_academic_event' to add new exams or deadlines")
    lines.append("💡 Use 'recommend_study_session' for study planning around these events")
    
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 6) Agent and prompt with break awareness AND academic events
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a smart timetable assistant with break management and academic event tracking.

**NEW: Academic Event Awareness**
- You now track exams, tests, quizzes, vivas, projects, and deadlines
- Consider these events when scheduling study sessions
- Warn users about conflicts with important academic events
- Provide study recommendations based on upcoming events

**Key Principles:**
1. Always respond to the user's immediate request first
2. If user refers to previous context, acknowledge it but focus on the current command
3. Use the appropriate tools for each request
4. If multiple commands are given, handle them sequentially

**Command Handling:**
- Greetings: Respond politely and offer help
- "timetable" or "schedule": Show current timetable
- "calendar" or "events": Show academic calendar
- "add exam" or "add deadline": Use add_academic_event tool
- "remove [something]": Use remove_block tool
- "add [something]": Use add_block tool
- "help": Show help information
- "reset": Clear all schedule data

**Academic Event Management:**
- Track exams, tests, projects, and deadlines
- Avoid scheduling intensive study sessions right before important events
- Provide study recommendations based on event proximity and importance

**Break Management:**
- Humans cannot study effectively for more than 90 minutes without breaks
- Schedule breaks automatically for study sessions longer than 45 minutes
- Ideal study-break ratio is 20-25%

**Error Recovery:**
- If confused, ask for clarification
- If multiple commands, handle the first clear one
- Always maintain polite, helpful tone

Use the tools to maintain healthy study habits and academic success.
"""

TOOLS = [
    show_timetable, 
    add_block, 
    remove_block, 
    update_block, 
    set_timezone, 
    export_ics,
    set_break_preferences,
    suggest_break,
    recommend_study_session,
    help_command,
    reset_timetable,
    add_academic_event,  # NEW
    show_academic_calendar  # NEW
]

memory = MemorySaver()
agent = create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT, checkpointer=memory)


# ─────────────────────────────────────────────────────────────
# 7) Enhanced CLI loop with better input handling
# ─────────────────────────────────────────────────────────────

def main(user_input,user_id):
    global state_manager
    state_manager = PersistentStateManager(user_id)
    print("Timetable agent ready. Type 'exit' to quit.")
    print("I now understand human cognitive limits and will schedule breaks automatically!")
    print("I also track academic events like exams, tests, and deadlines.")
    print("Type 'help' for assistance or 'reset' to start over.")
    
    messages = [("system", SYSTEM_PROMPT)]
    thread_config = {"configurable": {"thread_id": user_id}}

    while True:
        try:
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                processed_input = _preprocess_input("""
You are an assistant that outputs a timetable. Return ONLY valid JSON — no explanations, no markdown, no backticks, no extra text, no "json" prefixes.

The JSON must have exactly these fields and structure:

{
  "timetable": [
    {
      "time": "Tue 2025-09-23 09:00–10:30",
      "duration": "90min",
      "type": "study",
      "task": "📚 Morning Study - Math",
      "id": "2206eba8"
    },
    {
      "time": "Tue 2025-09-23 12:30–13:30",
      "duration": "60min",
      "type": "meal",
      "task": "☕ Lunch",
      "id": "66a2f210"
    },
    {
      "time": "Tue 2025-09-23 14:00–15:00",
      "duration": "60min",
      "type": "exercise",
      "task": "☕ Exercise - Gym",
      "id": "1fd8479b"
    },
    {
      "time": "Tue 2025-09-23 18:00–18:45",
      "duration": "45min",
      "type": "personal",
      "task": "☕ Reading - Novel",
      "id": "ead5c698"
    }
  ],
  "summary": {
    "study_time": "90min",
    "break_time": "0min",
    "study_break_ratio": "0.00",
    "warning": "Needs more breaks"
  }
}

- Keep all keys exactly as above; do not generalize them.
- Fill in the timetable with actual times, durations, tasks, and IDs as required.
- Keep the summary with the exact same fields.
- Only return JSON that is fully parseable by Python's json.loads().
- Do not include extra characters, explanations, or formatting.

Now generate the timetable JSON.
""")

                messages.append(("user", processed_input))
                result = agent.invoke({"messages": messages}, thread_config)
                assistant_text = result["messages"][-1].content
                return assistant_text                
                break

            # Pre-process the input to handle common patterns
            processed_input = _preprocess_input(user_input)
            
            messages.append(("user", processed_input))
            result = agent.invoke({"messages": messages}, thread_config)
            
            # The agent returns a messages list; last content is the assistant reply
            assistant_text = result["messages"][-1].content
            print("Assistant:", assistant_text)
            return  assistant_text
            messages = result["messages"]
            
        except KeyboardInterrupt:
            print("\nAssistant: Goodbye! 👋")
            break
        except Exception as ex:
            print(f"Error: {ex}")
            # Reset conversation if there's an error
            messages = [("system", SYSTEM_PROMPT)]
            print("Assistant: I encountered an error. Let's start fresh. How can I help with your timetable?")


if __name__ == "__main__":

    main()
