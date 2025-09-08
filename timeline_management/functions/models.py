from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ProcessStep:
    stepId: str
    title: str
    description: str
    status: str
    estimatedStartDate: str
    estimatedEndDate: str
    dependencies: List[str] = field(default_factory=list)

@dataclass
class TimelineProposal:
    targetStepId: str
    newEstimatedEndDate: Optional[str] = None
    newDescription: Optional[str] = None
    newStatus: Optional[str] = None
    reason: str

@dataclass
class AgentFinding:
    journeyId: str
    agentId: str
    sourceUri: str
    summary: str
    retrievedAt: str
    sourceCredibility: float
    proposal: Optional[TimelineProposal] = None

@dataclass
class JourneyEvent:
    journeyId: str
    findingId: str
    status: str
    createdAt: str
    processedAt: Optional[str] = None
    notes: Optional[str] = None
    
@dataclass
class ProposalPayload:
    shiftDays: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None

@dataclass
class Proposal:
    targetStepKey: str
    action: str  # e.g., "UPDATE_DATES", "UPDATE_STATUS"
    payload: ProposalPayload
    reason: str

@dataclass
class DataPoint:
    dataType: str  # "INFORMATIONAL" or "PROPOSAL"
    sourceType: str
    sourceURI: str
    retrievedAt: str
    rawContent: str
    confidenceScore: float
    proposal: Optional[Proposal] = None