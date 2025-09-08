from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class Status(str, Enum):
    Queued = "Queued"
    Processed = "Processed"
    Started = "Started"
    Conflicted = "Conflicted"
    Completed = "Completed"


class Processingstatus(BaseModel):
    OverallStatus: Optional[Status] = None
    Phases: Dict[str, Status] = Field(default_factory=dict)


class Extractedentities(BaseModel):
    originCountry: Optional[str] = None
    destinationCountry: Optional[str] = None
    processType: Optional[str] = None
    institution: Optional[str] = None
    programStartDate: Optional[str] = None


class Llmanalysis(BaseModel):
    detectedIntent: Optional[str] = None
    extractedEntities: Optional[Extractedentities] = None
    summary: Optional[str] = None


class Keydates(BaseModel):
    programStartDate: Optional[str] = None
    earliestEntryDate: Optional[str] = None
    estimatedVisaInterviewDate: Optional[str] = None
    idealFlightBookingWindowStart: Optional[str] = None
    idealFlightBookingWindowEnd: Optional[str] = None


class Plannedtimeline(BaseModel):
    journeyId: Optional[str] = None
    keyDates: Optional[Keydates] = None
    summary: Optional[str] = None


class Agentannotations(BaseModel):
    proposedTemplateId: Optional[str] = None
    requiresManualReview: Optional[bool] = None
    notes: Optional[str] = None


class Groundedsearchresult(BaseModel):
    sourceURI: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    retrievedAt: Optional[datetime] = None


class Extractedmilestone(BaseModel):
    milestoneKey: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Extractedtimeline(BaseModel):
    timelineKey: Optional[str] = None
    description: Optional[str] = None
    value: Optional[int] = None
    unit: Optional[str] = None


class Parseddocument(BaseModel):
    documentId: Optional[str] = None
    sourceURI: Optional[str] = None
    documentType: Optional[str] = None
    llmSummary: Optional[str] = None
    extractedChecklistItems: Optional[List[str]] = None
    extractedMilestones: Optional[List[Extractedmilestone]] = None
    extractedTimelines: Optional[List[Extractedtimeline]] = None


class Nexttask(BaseModel):
    agentId: Optional[str] = None
    trigger: Optional[str] = None


class Agenttask(BaseModel):
    taskId: Optional[str] = None
    agentId: Optional[str] = None
    status: Optional[str] = None
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    output: Optional[str] = None
    nextTask: Optional[Nexttask] = None


class Resource(BaseModel):
    link: Optional[str] = None
    linkType: Optional[str] = None
    description: Optional[str] = None


class Reminder(BaseModel):
    daysBefore: Optional[int] = None
    channel: Optional[str] = None


class Notifications(BaseModel):
    enabled: Optional[bool] = None
    reminders: Optional[List[Reminder]] = None


class Event(BaseModel):
    eventId: Optional[str] = None
    stepKey: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    status: Optional[str] = None
    resources: Optional[List[Resource]] = None
    notifications: Optional[Notifications] = None


class Timeline(BaseModel):
    timelineId: Optional[str] = None
    userId: Optional[str] = None
    journeyId: Optional[str] = None
    title: Optional[str] = None
    lastUpdatedAt: Optional[datetime] = None
    events: Optional[List[Event]] = None


class SessionStorageItem(BaseModel):
    sessionId: Optional[str] = None
    userId: Optional[str] = None
    createdAt: Optional[datetime] = None
    lastUpdatedAt: Optional[datetime] = None
    processingStatus: Optional[Processingstatus] = None
    initialQuery: Optional[str] = None
    llmAnalysis: Optional[Llmanalysis] = None
    groundedSearchResults: Optional[List[Groundedsearchresult]] = None
    parsedDocuments: Optional[List[Parseddocument]] = None
    plannedTimeline: Optional[Plannedtimeline] = None
    ActualTimeline: Optional[Timeline] = None
    agentTasks: Optional[List[Agenttask]] = None
    agentAnnotations: Optional[Agentannotations] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
