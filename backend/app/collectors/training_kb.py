"""Training knowledge base collector.

This module provides knowledge base management for training content with
efficient search and relationship mapping capabilities.

This module uses the following DSA concepts from app.core.dsa:
- Graph: Content relationship mapping and dependency tracking
- HashMap: Content storage and metadata indexing for O(1) lookups
- Trie: Text search and keyword matching for content discovery
- AVLTree: Timestamp-based content indexing for chronological queries
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dsa.graph import Graph
from core.dsa.hashmap import HashMap
from core.dsa.trie import Trie
from core.dsa.avl_tree import AVLTree


class DifficultyLevel(Enum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


class ContentType(Enum):
    ARTICLE = "article"
    VIDEO = "video"
    QUIZ = "quiz"
    LAB = "lab"
    SCENARIO = "scenario"
    TEMPLATE = "template"
    CHECKLIST = "checklist"


class SECategory(Enum):
    
    PHISHING = "phishing"
    VISHING = "vishing"
    SMISHING = "smishing"
    PRETEXTING = "pretexting"
    BAITING = "baiting"
    TAILGATING = "tailgating"
    QUID_PRO_QUO = "quid_pro_quo"
    IMPERSONATION = "impersonation"
    DUMPSTER_DIVING = "dumpster_diving"
    SHOULDER_SURFING = "shoulder_surfing"
    WATERING_HOLE = "watering_hole"
    SPEAR_PHISHING = "spear_phishing"
    WHALING = "whaling"
    BEC = "business_email_compromise"


@dataclass
class TrainingContent:
    
    content_id: str
    title: str
    description: str
    category: SECategory
    content_type: ContentType
    difficulty: DifficultyLevel
    duration_minutes: int
    content_body: str
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    related_content: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    view_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "content_id": self.content_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "content_type": self.content_type.value,
            "difficulty": self.difficulty.name,
            "duration_minutes": self.duration_minutes,
            "tags": self.tags,
            "prerequisites": self.prerequisites,
            "view_count": self.view_count
        }


@dataclass
class PhishingTemplate:
    
    template_id: str
    name: str
    category: SECategory
    difficulty: DifficultyLevel
    subject_line: str
    sender_name: str
    sender_email: str
    html_body: str
    text_body: str
    indicators: List[str]
    learning_points: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "category": self.category.value,
            "difficulty": self.difficulty.name,
            "subject_line": self.subject_line,
            "sender_name": self.sender_name,
            "indicators_count": len(self.indicators)
        }


@dataclass
class LabScenario:
    
    scenario_id: str
    title: str
    description: str
    category: SECategory
    difficulty: DifficultyLevel
    duration_minutes: int
    objectives: List[str]
    setup_instructions: str
    steps: List[Dict[str, str]]
    success_criteria: List[str]
    hints: List[str]
    solution: str
    
    def to_dict(self) -> Dict:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.name,
            "duration_minutes": self.duration_minutes,
            "objectives": self.objectives,
            "steps_count": len(self.steps)
        }


@dataclass
class QuizQuestion:
    
    question_id: str
    question_text: str
    options: List[str]
    correct_answer: int
    explanation: str
    category: SECategory
    difficulty: DifficultyLevel
    points: int = 10


@dataclass
class TraineeProgress:
    
    trainee_id: str
    completed_content: List[str]
    quiz_scores: Dict[str, float]
    lab_completions: Dict[str, bool]
    total_points: int
    current_level: DifficultyLevel
    badges: List[str]
    last_activity: datetime
    
    def to_dict(self) -> Dict:
        return {
            "trainee_id": self.trainee_id,
            "completed_content_count": len(self.completed_content),
            "average_quiz_score": sum(self.quiz_scores.values()) / len(self.quiz_scores) if self.quiz_scores else 0,
            "labs_completed": sum(self.lab_completions.values()),
            "total_points": self.total_points,
            "current_level": self.current_level.name,
            "badges": self.badges
        }


class TrainingKB:
    
    
    def __init__(self):

        self.content_graph = Graph(directed=True)
        

        self.content = HashMap()
        self.templates = HashMap() 
        self.labs = HashMap()  
        self.quizzes = HashMap() 
        

        self.trainees = HashMap()
        

        self.search_trie = Trie()
        

        self.content_by_difficulty = AVLTree()
        

        self.stats = {
            "total_content": 0,
            "total_templates": 0,
            "total_labs": 0,
            "total_trainees": 0,
            "content_views": 0
        }
        

        self._init_sample_content()
    
    def _generate_id(self, prefix: str, data: str) -> str:
        
        return f"{prefix}_{hashlib.md5(data.encode()).hexdigest()[:8]}"
    
    def _init_sample_content(self):
        

        self.add_content(TrainingContent(
            content_id=self._generate_id("content", "phishing_basics"),
            title="Phishing 101: Understanding Email-Based Attacks",
            description="Learn the fundamentals of phishing attacks and how to identify them.",
            category=SECategory.PHISHING,
            content_type=ContentType.ARTICLE,
            difficulty=DifficultyLevel.BEGINNER,
            duration_minutes=15,
            content_body="""
# Phishing 101

## What is Phishing?
Phishing is a social engineering attack where attackers masquerade as 
trusted entities to trick victims into revealing sensitive information.

## Common Indicators
1. **Suspicious sender address** - Check the actual email domain
2. **Urgency and pressure** - "Act now or lose access!"
3. **Generic greetings** - "Dear Customer" instead of your name
4. **Spelling and grammar errors** - Professional organizations proofread
5. **Suspicious links** - Hover before clicking
6. **Unexpected attachments** - Verify with sender

## Prevention Tips
- Always verify unexpected requests through official channels
- Enable multi-factor authentication
- Report suspicious emails to IT security
- Never enter credentials from email links
            """,
            tags=["phishing", "email", "security-awareness", "beginner"]
        ))
        

        self.add_content(TrainingContent(
            content_id=self._generate_id("content", "vishing_defense"),
            title="Vishing Defense: Protecting Against Phone Scams",
            description="Learn to recognize and defend against voice phishing attacks.",
            category=SECategory.VISHING,
            content_type=ContentType.ARTICLE,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_minutes=20,
            content_body="""
# Vishing Defense

## What is Vishing?
Vishing (voice phishing) uses phone calls to manipulate victims.
Attackers may impersonate IT support, banks, or government agencies.

## Red Flags
- Unsolicited calls requesting personal information
- Caller creates sense of urgency
- Requests for passwords or OTP codes
- Caller ID spoofing (looks like legitimate number)
- Threatening consequences for non-compliance

## Defense Strategies
1. Never give sensitive info to inbound callers
2. Call back using official numbers
3. Verify caller identity through other channels
4. Document suspicious calls
5. Report to security team
            """,
            tags=["vishing", "phone", "social-engineering"],
            prerequisites=["phishing_basics"]
        ))
        

        self.add_template(PhishingTemplate(
            template_id=self._generate_id("template", "password_reset"),
            name="Password Reset Urgency",
            category=SECategory.PHISHING,
            difficulty=DifficultyLevel.BEGINNER,
            subject_line="URGENT: Your password expires in 24 hours",
            sender_name="IT Security Team",
            sender_email="security@company-support.net",
            html_body="""
<html>
<body style="font-family: Arial, sans-serif;">
<div style="max-width: 600px; margin: 0 auto;">
    <img src="company-logo.png" alt="Company Logo">
    <h2>Password Expiration Notice</h2>
    <p>Dear Employee,</p>
    <p>Your network password will expire in <strong>24 hours</strong>.</p>
    <p>To avoid losing access to your account, please reset your password immediately:</p>
    <p><a href="http://company-support.net/reset" style="background: #0066cc; color: white; padding: 10px 20px; text-decoration: none;">Reset Password Now</a></p>
    <p>If you do not reset your password, you will be locked out.</p>
    <p>IT Security Team</p>
</div>
</body>
</html>
            """,
            text_body="Your password expires in 24 hours. Reset at: http://company-support.net/reset",
            indicators=[
                "Generic greeting ('Dear Employee')",
                "Suspicious domain (company-support.net instead of company.com)",
                "Urgency and threat of account lockout",
                "Lack of personalization",
                "HTTP instead of HTTPS link"
            ],
            learning_points=[
                "Always check the sender's actual email domain",
                "Legitimate IT teams don't send password reset links",
                "Contact IT directly through known channels",
                "Check URLs before clicking"
            ]
        ))
        

        self.add_lab(LabScenario(
            scenario_id=self._generate_id("lab", "phishing_analysis"),
            title="Phishing Email Analysis Lab",
            description="Analyze a suspicious email and identify all indicators of phishing.",
            category=SECategory.PHISHING,
            difficulty=DifficultyLevel.INTERMEDIATE,
            duration_minutes=30,
            objectives=[
                "Identify phishing indicators in email headers",
                "Analyze suspicious URLs without clicking",
                "Document findings in incident report format"
            ],
            setup_instructions="""
1. Open the provided email sample in the sandbox environment
2. Use the header analysis tool to examine email metadata
3. Use URL inspection tool to analyze links
4. Fill out the incident report template
            """,
            steps=[
                {"step": 1, "instruction": "Examine the sender address", "hint": "Look at the full email header"},
                {"step": 2, "instruction": "Analyze the email body for red flags", "hint": "Check greeting, urgency, errors"},
                {"step": 3, "instruction": "Hover over links to inspect URLs", "hint": "Don't click, just hover"},
                {"step": 4, "instruction": "Check for SPF/DKIM/DMARC results", "hint": "Look in authentication headers"},
                {"step": 5, "instruction": "Complete the incident report", "hint": "Include all findings"}
            ],
            success_criteria=[
                "Identified fake sender domain",
                "Found at least 3 red flags in body",
                "Correctly analyzed malicious URL",
                "Completed incident report with all sections"
            ],
            hints=[
                "The sender domain looks similar but isn't quite right",
                "Check the greeting and signature",
                "The link doesn't go where the text says"
            ],
            solution="The email is from support@comp4ny.com (4 instead of a), uses generic greeting, creates urgency, and links to a different domain than displayed."
        ))
        

        quiz_id = self._generate_id("quiz", "phishing_basics")
        self.quizzes.put(quiz_id, [
            QuizQuestion(
                question_id=f"{quiz_id}_1",
                question_text="Which of the following is the MOST reliable indicator of a phishing email?",
                options=[
                    "The email contains spelling errors",
                    "The sender's email domain doesn't match the organization",
                    "The email was unexpected",
                    "The email asks you to click a link"
                ],
                correct_answer=1,
                explanation="While all can be indicators, checking the sender's actual email domain is the most reliable way to verify authenticity.",
                category=SECategory.PHISHING,
                difficulty=DifficultyLevel.BEGINNER,
                points=10
            ),
            QuizQuestion(
                question_id=f"{quiz_id}_2",
                question_text="An email claims to be from your CEO asking for an urgent wire transfer. What should you do?",
                options=[
                    "Complete the transfer immediately since it's from the CEO",
                    "Reply to the email to confirm",
                    "Call the CEO using a known phone number to verify",
                    "Forward it to a colleague to decide"
                ],
                correct_answer=2,
                explanation="Always verify unusual or urgent requests through an independent channel like a known phone number. This is Business Email Compromise (BEC).",
                category=SECategory.BEC,
                difficulty=DifficultyLevel.INTERMEDIATE,
                points=15
            )
        ])
    
    def add_content(self, content: TrainingContent) -> str:
        """Add training content to knowledge base.
        
        DSA-USED:
        - HashMap: Content storage
        - Graph: Content relationship mapping and prerequisite edges
        - Trie: Search index for title and tag matching
        - AVLTree: Difficulty-based indexing
        
        Args:
            content: TrainingContent instance to add
        
        Returns:
            Content identifier
        """
        self.content.put(content.content_id, content)  # DSA-USED: HashMap
        

        self.content_graph.add_node(
            content.content_id,
            label=content.title,
            node_type="content",
            data={
                "type": "content",
                "category": content.category.value,
                "difficulty": content.difficulty.value
            }
        )  # DSA-USED: Graph
        

        for prereq in content.prerequisites:
            if self.content_graph.has_vertex(prereq):  # DSA-USED: Graph
                self.content_graph.add_edge(prereq, content.content_id)  # DSA-USED: Graph
        

        for word in content.title.lower().split():
            self.search_trie.insert(word)  # DSA-USED: Trie
        for tag in content.tags:
            self.search_trie.insert(tag.lower())  # DSA-USED: Trie
        

        self.content_by_difficulty.insert(
            content.difficulty.value * 1000 + hash(content.content_id) % 1000,
            content.content_id
        )  # DSA-USED: AVLTree
        
        self.stats["total_content"] += 1
        return content.content_id
    
    def add_template(self, template: PhishingTemplate) -> str:
        
        self.templates.put(template.template_id, template)  # DSA-USED: HashMap
        self.stats["total_templates"] += 1
        return template.template_id
    
    def add_lab(self, lab: LabScenario) -> str:
        
        self.labs.put(lab.scenario_id, lab)  # DSA-USED: HashMap
        self.stats["total_labs"] += 1
        return lab.scenario_id
    
    def get_content(self, content_id: str) -> Optional[TrainingContent]:
        
        content = self.content.get(content_id)  # DSA-USED: HashMap
        if content:
            content.view_count += 1
            self.stats["content_views"] += 1
        return content
    
    def search_content(self, query: str) -> List[TrainingContent]:
        
        results = []
        query_lower = query.lower()
        
        for content_id in self.content.keys():  # DSA-USED: HashMap
            content = self.content.get(content_id)  # DSA-USED: HashMap  # DSA-USED: HashMap
            if not content:
                continue
            

            if query_lower in content.title.lower():
                results.append(content)
            elif any(query_lower in tag for tag in content.tags):
                results.append(content)
        
        return results
    
    def get_content_by_category(
        self,
        category: SECategory,
        difficulty: Optional[DifficultyLevel] = None
    ) -> List[TrainingContent]:
        
        results = []
        
        for content_id in self.content.keys():  # DSA-USED: HashMap
            content = self.content.get(content_id)  # DSA-USED: HashMap  # DSA-USED: HashMap
            if not content:
                continue
            
            if content.category != category:
                continue
            
            if difficulty and content.difficulty != difficulty:
                continue
            
            results.append(content)
        
        return sorted(results, key=lambda c: c.difficulty.value)
    
    def get_learning_path(
        self,
        category: SECategory,
        current_level: DifficultyLevel = DifficultyLevel.BEGINNER
    ) -> List[TrainingContent]:
        
        path = []
        

        category_content = self.get_content_by_category(category)
        

        for content in category_content:
            if content.difficulty.value >= current_level.value:
                path.append(content)
        

        return sorted(path, key=lambda c: (c.difficulty.value, c.duration_minutes))
    
    def get_templates_by_difficulty(
        self,
        difficulty: DifficultyLevel
    ) -> List[PhishingTemplate]:
        
        results = []
        
        for template_id in self.templates.keys():
            template = self.templates.get(template_id)
            if template and template.difficulty == difficulty:
                results.append(template)
        
        return results
    
    def get_labs_by_category(
        self,
        category: SECategory
    ) -> List[LabScenario]:
        
        results = []
        
        for lab_id in self.labs.keys():
            lab = self.labs.get(lab_id)
            if lab and lab.category == category:
                results.append(lab)
        
        return sorted(results, key=lambda l: l.difficulty.value)
    
    def register_trainee(self, trainee_id: str) -> TraineeProgress:
        
        progress = TraineeProgress(
            trainee_id=trainee_id,
            completed_content=[],
            quiz_scores={},
            lab_completions={},
            total_points=0,
            current_level=DifficultyLevel.BEGINNER,
            badges=[],
            last_activity=datetime.now()
        )
        self.trainees.put(trainee_id, progress)  # DSA-USED: HashMap
        self.stats["total_trainees"] += 1
        return progress
    
    def record_content_completion(
        self,
        trainee_id: str,
        content_id: str
    ) -> TraineeProgress:
        
        progress = self.trainees.get(trainee_id)  # DSA-USED: HashMap
        if not progress:
            progress = self.register_trainee(trainee_id)
        
        if content_id not in progress.completed_content:
            progress.completed_content.append(content_id)
            
            content = self.content.get(content_id)  # DSA-USED: HashMap
            if content:
                progress.total_points += content.difficulty.value * 10
        
        progress.last_activity = datetime.now()
        self._update_trainee_level(progress)
        
        return progress
    
    def record_quiz_score(
        self,
        trainee_id: str,
        quiz_id: str,
        score: float
    ) -> TraineeProgress:
        
        progress = self.trainees.get(trainee_id)  # DSA-USED: HashMap
        if not progress:
            progress = self.register_trainee(trainee_id)
        
        progress.quiz_scores[quiz_id] = score
        progress.total_points += int(score * 10)
        progress.last_activity = datetime.now()
        self._update_trainee_level(progress)
        
        return progress
    
    def record_lab_completion(
        self,
        trainee_id: str,
        lab_id: str,
        success: bool
    ) -> TraineeProgress:
        
        progress = self.trainees.get(trainee_id)  # DSA-USED: HashMap
        if not progress:
            progress = self.register_trainee(trainee_id)
        
        progress.lab_completions[lab_id] = success
        if success:
            lab = self.labs.get(lab_id)
            if lab:
                progress.total_points += lab.difficulty.value * 25
        
        progress.last_activity = datetime.now()
        self._update_trainee_level(progress)
        
        return progress
    
    def _update_trainee_level(self, progress: TraineeProgress):
        
        if progress.total_points >= 500:
            progress.current_level = DifficultyLevel.EXPERT
            if "Expert" not in progress.badges:
                progress.badges.append("Expert")
        elif progress.total_points >= 250:
            progress.current_level = DifficultyLevel.ADVANCED
            if "Advanced" not in progress.badges:
                progress.badges.append("Advanced")
        elif progress.total_points >= 100:
            progress.current_level = DifficultyLevel.INTERMEDIATE
            if "Intermediate" not in progress.badges:
                progress.badges.append("Intermediate")
    
    def get_trainee_progress(self, trainee_id: str) -> Optional[TraineeProgress]:
        
        return self.trainees.get(trainee_id)
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        
        trainees = []
        
        for tid in self.trainees.keys():
            progress = self.trainees.get(tid)
            if progress:
                trainees.append({
                    "trainee_id": tid,
                    "total_points": progress.total_points,
                    "level": progress.current_level.name,
                    "badges": len(progress.badges),
                    "content_completed": len(progress.completed_content)
                })
        
        return sorted(trainees, key=lambda t: t["total_points"], reverse=True)[:limit]
    
    def get_category_overview(self) -> Dict[str, Dict[str, int]]:
        
        overview = {}
        
        for category in SECategory:
            overview[category.value] = {
                "articles": 0,
                "labs": 0,
                "templates": 0
            }
        
        for cid in self.content.keys():
            content = self.content.get(cid)
            if content:
                cat = content.category.value
                if content.content_type == ContentType.ARTICLE:
                    overview[cat]["articles"] += 1
        
        for lid in self.labs.keys():
            lab = self.labs.get(lid)
            if lab:
                overview[lab.category.value]["labs"] += 1
        
        for tid in self.templates.keys():
            template = self.templates.get(tid)
            if template:
                overview[template.category.value]["templates"] += 1
        
        return overview
    
    def get_statistics(self) -> Dict[str, Any]:
        
        return {
            **self.stats,
            "categories": len(SECategory),
            "search_terms": self.search_trie.word_count(),
            "content_graph_nodes": self.content_graph.vertex_count()
        }
    
    def export_content(self, format: str = "json") -> str:
        
        data = {
            "exported_at": datetime.now().isoformat(),
            "content": [self.content.get(cid).to_dict() for cid in self.content.keys() if self.content.get(cid)],
            "templates": [self.templates.get(tid).to_dict() for tid in self.templates.keys() if self.templates.get(tid)],
            "labs": [self.labs.get(lid).to_dict() for lid in self.labs.keys() if self.labs.get(lid)],
            "statistics": self.get_statistics()
        }
        return json.dumps(data, indent=2)


if __name__ == "__main__":
    kb = TrainingKB()
    

    results = kb.search_content("phishing")
    print(f"Found {len(results)} content items for 'phishing'")
    

    path = kb.get_learning_path(SECategory.PHISHING)
    print(f"\nPhishing learning path ({len(path)} items):")
    for content in path:
        print(f"  - {content.title} ({content.difficulty.name})")
    

    kb.register_trainee("user123")
    kb.record_content_completion("user123", path[0].content_id if path else "")
    progress = kb.get_trainee_progress("user123")
    print(f"\nTrainee progress: {progress.to_dict() if progress else 'None'}")
    
    print(f"\nStatistics: {kb.get_statistics()}")


