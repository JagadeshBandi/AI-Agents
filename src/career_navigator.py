"""
CareerNavigator AI - Specialized UK and USA Job Hunting Agent
Advanced automation for CV optimization, LinkedIn enhancement, and job search
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import re
import asyncio

from src.agent import AIAgent
from src.config import settings


class CareerNavigatorAI:
    """Specialized AI agent for UK and USA job hunting"""
    
    def __init__(self):
        self.job_market_data = self._load_job_market_data()
        self.cv_analyzer = CVAnalyzer()
        self.linkedin_optimizer = LinkedInOptimizer()
        self.job_search_automation = JobSearchAutomation()
        self.freelance_guide = FreelancingGuide()
        self.recruiter_connector = RecruiterConnectionGuide()
    
    def _load_job_market_data(self) -> Dict[str, Any]:
        """Load comprehensive job market data for UK and USA"""
        return {
            "uk": {
                "job_boards": [
                    {"name": "Indeed UK", "url": "indeed.co.uk", "type": "general"},
                    {"name": "Reed", "url": "reed.co.uk", "type": "general"},
                    {"name": "Totaljobs", "url": "totaljobs.com", "type": "general"},
                    {"name": "CV-Library", "url": "cv-library.co.uk", "type": "general"},
                    {"name": "LinkedIn", "url": "linkedin.com", "type": "professional"},
                    {"name": "Guardian Jobs", "url": "jobs.theguardian.com", "type": "professional"},
                    {"name": "Glassdoor UK", "url": "glassdoor.co.uk", "type": "reviews"},
                    {"name": "CWJobs", "url": "cwjobs.co.uk", "type": "tech"},
                    {"name": "Technojobs", "url": "technojobs.co.uk", "type": "tech"}
                ],
                "recruitment_agencies": [
                    "Hays", "Michael Page", "Robert Half", "Adecco", "Manpower",
                    "Reed Specialist Recruitment", "Randstad", "Robert Walters"
                ],
                "cv_format": {
                    "length": "2 pages maximum",
                    "photo": "Not required unless specifically requested",
                    "personal_statement": "Essential - 3-4 lines at top",
                    "education_order": "Reverse chronological",
                    "work_experience": "Reverse chronological with achievements",
                    "references": "Available upon request"
                },
                "application_tips": [
                    "Tailor CV and cover letter for each application",
                    "Use British English spelling throughout",
                    "Include personal statement highlighting career goals",
                    "Quantify achievements with specific metrics",
                    "Follow up 1-2 weeks after application",
                    "Research company culture and values",
                    "Prepare for competency-based interviews",
                    "Dress formally for interviews"
                ],
                "networking_platforms": [
                    "LinkedIn", "Meetup", "Eventbrite", "Professional associations",
                    "Alumni networks", "Industry conferences"
                ],
                "visa_requirements": {
                    "skilled_worker": "Points-based system, job offer from licensed sponsor",
                    "graduate_route": "2 years post-study work visa",
                    "healthcare_surcharge": "Required for NHS access",
                    "english_requirement": "IELTS or equivalent proof"
                }
            },
            "usa": {
                "job_boards": [
                    {"name": "Indeed", "url": "indeed.com", "type": "general"},
                    {"name": "LinkedIn", "url": "linkedin.com", "type": "professional"},
                    {"name": "Glassdoor", "url": "glassdoor.com", "type": "reviews"},
                    {"name": "Monster", "url": "monster.com", "type": "general"},
                    {"name": "CareerBuilder", "url": "careerbuilder.com", "type": "general"},
                    {"name": "ZipRecruiter", "url": "ziprecruiter.com", "type": "general"},
                    {"name": "Dice", "url": "dice.com", "type": "tech"},
                    {"name": "AngelList", "url": "angel.co", "type": "startups"},
                    {"name": "USAJobs", "url": "usajobs.gov", "type": "government"}
                ],
                "recruitment_agencies": [
                    "Robert Half", "Kelly Services", "Aerotek", "Randstad USA",
                    "Adecco", "ManpowerGroup", "Kforce", "TEKsystems"
                ],
                "cv_format": {
                    "length": "1-2 pages maximum",
                    "photo": "Not recommended",
                    "summary": "Professional summary at top",
                    "education": "Include GPA if recent graduate and above 3.0",
                    "achievements": "Quantified results emphasized",
                    "skills": "Technical skills section prominent"
                },
                "application_tips": [
                    "Optimize resume for ATS systems with keywords",
                    "Create achievement-focused content with metrics",
                    "Network extensively - referrals are crucial",
                    "Follow up within 1 week of application",
                    "Research company thoroughly before interview",
                    "Prepare for behavioral questions using STAR method",
                    "Send thank-you email within 24 hours of interview",
                    "Business casual or business formal for interviews"
                ],
                "networking_platforms": [
                    "LinkedIn", "Meetup", "Eventbrite", "Professional associations",
                    "Alumni networks", "Industry conferences", "Slack communities"
                ],
                "visa_requirements": {
                    "h1b": "Specialty occupations, lottery system, employer sponsored",
                    "l1": "Intra-company transfer visa",
                    "o1": "Extraordinary ability in field",
                    "green_card": "Employment-based permanent residency"
                }
            }
        }
    
    async def analyze_cv_for_job(self, cv_content: str, job_description: str, 
                                  target_country: str) -> Dict[str, Any]:
        """Analyze CV against specific job description and provide match score"""
        return await self.cv_analyzer.match_cv_to_job(cv_content, job_description, target_country)
    
    async def optimize_cv_for_market(self, cv_content: str, target_country: str, 
                                      target_role: str, target_industry: str) -> Dict[str, Any]:
        """Optimize CV for specific market and provide detailed suggestions"""
        return await self.cv_analyzer.optimize_for_market(
            cv_content, target_country, target_role, target_industry
        )
    
    async def get_job_search_strategy(self, profile: Dict[str, Any], 
                                       target_country: str) -> Dict[str, Any]:
        """Get comprehensive job search strategy"""
        return await self.job_search_automation.create_strategy(profile, target_country)
    
    async def get_recruiter_connection_guide(self, industry: str, 
                                              target_country: str) -> Dict[str, Any]:
        """Get detailed guide on connecting with recruiters"""
        return await self.recruiter_connector.get_connection_strategy(industry, target_country)
    
    async def optimize_linkedin(self, profile_data: Dict[str, Any], 
                                 target_country: str) -> Dict[str, Any]:
        """Optimize LinkedIn profile for job search"""
        return await self.linkedin_optimizer.optimize(profile_data, target_country)
    
    async def get_freelancing_strategy(self, skills: List[str], 
                                        experience_level: str) -> Dict[str, Any]:
        """Get freelancing strategy and platform recommendations"""
        return await self.freelance_guide.create_strategy(skills, experience_level)


class CVAnalyzer:
    """Advanced ATS-friendly CV analysis and optimization"""
    
    def __init__(self):
        self.ats_keywords = self._load_ats_keywords()
        self.action_verbs = [
            "achieved", "managed", "developed", "implemented", "increased", "reduced",
            "created", "led", "designed", "improved", "optimized", "delivered",
            "established", "launched", "transformed", "streamlined", "coordinated",
            "executed", "generated", "initiated", "negotiated", "resolved"
        ]
    
    def _load_ats_keywords(self) -> Dict[str, List[str]]:
        """Load ATS-friendly keywords by industry"""
        return {
            "tech": [
                "Python", "Java", "JavaScript", "AWS", "Docker", "Kubernetes",
                "React", "Node.js", "SQL", "Git", "Agile", "Scrum", "CI/CD",
                "Machine Learning", "Data Analysis", "Cloud Computing"
            ],
            "finance": [
                "Financial Analysis", "Excel", "Risk Management", "Compliance",
                "Financial Modeling", "Bloomberg", "Investment", "Portfolio Management",
                "Accounting", "Auditing", "Budgeting", "Forecasting"
            ],
            "healthcare": [
                "Patient Care", "Clinical", "Medical Records", "HIPAA", "Healthcare",
                "Nursing", "Medical Terminology", "Electronic Health Records",
                "Patient Safety", "Quality Improvement"
            ],
            "engineering": [
                "AutoCAD", "Project Management", "Technical Drawing", "Quality Assurance",
                "CAD", "Design", "Testing", "Manufacturing", "Process Improvement",
                "Six Sigma", "Lean Manufacturing"
            ],
            "marketing": [
                "Digital Marketing", "SEO", "SEM", "Social Media", "Content Marketing",
                "Analytics", "Google Analytics", "Campaign Management", "Brand Strategy",
                "Market Research", "Email Marketing"
            ]
        }
    
    async def match_cv_to_job(self, cv_content: str, job_description: str, 
                               target_country: str) -> Dict[str, Any]:
        """Match CV to job description and provide detailed scoring"""
        
        cv_keywords = self._extract_keywords(cv_content)
        job_keywords = self._extract_keywords(job_description)
        
        keyword_match = self._calculate_keyword_match(cv_keywords, job_keywords)
        skills_match = self._calculate_skills_match(cv_content, job_description)
        experience_match = self._assess_experience_match(cv_content, job_description)
        ats_score = self._calculate_ats_score(cv_content, target_country)
        
        overall_score = (
            keyword_match * 0.3 +
            skills_match * 0.3 +
            experience_match * 0.2 +
            ats_score * 0.2
        )
        
        return {
            "overall_match_score": round(overall_score, 1),
            "keyword_match": round(keyword_match, 1),
            "skills_match": round(skills_match, 1),
            "experience_match": round(experience_match, 1),
            "ats_compatibility": round(ats_score, 1),
            "matching_keywords": list(set(cv_keywords) & set(job_keywords)),
            "missing_keywords": list(set(job_keywords) - set(cv_keywords)),
            "recommendations": self._generate_match_recommendations(
                cv_content, job_description, overall_score, target_country
            ),
            "should_apply": overall_score >= 60,
            "confidence_level": "High" if overall_score >= 75 else "Medium" if overall_score >= 60 else "Low"
        }
    
    async def optimize_for_market(self, cv_content: str, target_country: str,
                                   target_role: str, target_industry: str) -> Dict[str, Any]:
        """Optimize CV for specific market with detailed suggestions"""
        
        ats_analysis = self._analyze_ats_compatibility(cv_content, target_country)
        format_analysis = self._analyze_format(cv_content, target_country)
        content_analysis = self._analyze_content_quality(cv_content, target_industry)
        keyword_analysis = self._analyze_keywords(cv_content, target_industry)
        
        return {
            "current_score": self._calculate_overall_cv_score(cv_content, target_country),
            "ats_compatibility": ats_analysis,
            "format_suggestions": format_analysis,
            "content_improvements": content_analysis,
            "keyword_optimization": keyword_analysis,
            "market_specific_tips": self._get_market_tips(target_country, target_role),
            "action_plan": self._create_optimization_action_plan(
                cv_content, target_country, target_role, target_industry
            )
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        words = re.findall(r'\b[A-Za-z][A-Za-z+#.]{2,}\b', text)
        return [word.lower() for word in words if len(word) > 2]
    
    def _calculate_keyword_match(self, cv_keywords: List[str], 
                                   job_keywords: List[str]) -> float:
        """Calculate keyword match percentage"""
        if not job_keywords:
            return 0.0
        
        matching = len(set(cv_keywords) & set(job_keywords))
        return (matching / len(set(job_keywords))) * 100
    
    def _calculate_skills_match(self, cv_content: str, job_description: str) -> float:
        """Calculate skills match score"""
        cv_lower = cv_content.lower()
        job_lower = job_description.lower()
        
        technical_skills = [
            "python", "java", "javascript", "sql", "aws", "docker", "kubernetes",
            "react", "angular", "vue", "node", "git", "agile", "scrum"
        ]
        
        cv_skills = [skill for skill in technical_skills if skill in cv_lower]
        job_skills = [skill for skill in technical_skills if skill in job_lower]
        
        if not job_skills:
            return 70.0
        
        matching_skills = len(set(cv_skills) & set(job_skills))
        return (matching_skills / len(job_skills)) * 100
    
    def _assess_experience_match(self, cv_content: str, job_description: str) -> float:
        """Assess experience level match"""
        
        years_required = self._extract_years_experience(job_description)
        years_in_cv = self._extract_years_experience(cv_content)
        
        if years_required == 0:
            return 80.0
        
        if years_in_cv >= years_required:
            return 100.0
        elif years_in_cv >= years_required * 0.75:
            return 80.0
        elif years_in_cv >= years_required * 0.5:
            return 60.0
        else:
            return 40.0
    
    def _extract_years_experience(self, text: str) -> int:
        """Extract years of experience from text"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+)\+?\s*years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        
        return 0
    
    def _calculate_ats_score(self, cv_content: str, target_country: str) -> float:
        """Calculate ATS compatibility score"""
        score = 0
        max_score = 100
        
        if not any(char in cv_content for char in ['|', '/', '\\']):
            score += 20
        
        if len(re.findall(r'\d+%|\d+\s*percent', cv_content)) > 0:
            score += 15
        
        action_verb_count = sum(1 for verb in self.action_verbs if verb in cv_content.lower())
        if action_verb_count >= 5:
            score += 20
        elif action_verb_count >= 3:
            score += 10
        
        if len(cv_content.split()) > 300:
            score += 15
        
        if re.search(r'\b\d{4}\s*-\s*\d{4}\b|\b\d{4}\s*-\s*Present\b', cv_content):
            score += 15
        
        if target_country == "uk" and "personal statement" in cv_content.lower():
            score += 15
        elif target_country == "usa" and ("summary" in cv_content.lower() or "objective" in cv_content.lower()):
            score += 15
        
        return min(score, max_score)
    
    def _generate_match_recommendations(self, cv_content: str, job_description: str,
                                         score: float, target_country: str) -> List[str]:
        """Generate specific recommendations for improving match"""
        recommendations = []
        
        cv_keywords = set(self._extract_keywords(cv_content))
        job_keywords = set(self._extract_keywords(job_description))
        missing = job_keywords - cv_keywords
        
        if missing:
            top_missing = list(missing)[:5]
            recommendations.append(
                f"Add these keywords from job description: {', '.join(top_missing)}"
            )
        
        if score < 60:
            recommendations.append(
                "Consider gaining more relevant experience or skills before applying"
            )
        
        action_verb_count = sum(1 for verb in self.action_verbs if verb in cv_content.lower())
        if action_verb_count < 5:
            recommendations.append(
                "Use more action verbs to describe achievements"
            )
        
        if not re.search(r'\d+%|\d+\s*percent|\d+x', cv_content):
            recommendations.append(
                "Quantify achievements with specific numbers and percentages"
            )
        
        if target_country == "uk" and "personal statement" not in cv_content.lower():
            recommendations.append(
                "Add a personal statement at the top for UK market"
            )
        
        return recommendations
    
    def _analyze_ats_compatibility(self, cv_content: str, target_country: str) -> Dict[str, Any]:
        """Detailed ATS compatibility analysis"""
        issues = []
        strengths = []
        
        if any(char in cv_content for char in ['|', '/', '\\']):
            issues.append("Remove special characters that may confuse ATS systems")
        else:
            strengths.append("No problematic special characters detected")
        
        if not re.search(r'\b\d{4}\s*-\s*\d{4}\b|\b\d{4}\s*-\s*Present\b', cv_content):
            issues.append("Add clear date ranges for work experience (YYYY-YYYY format)")
        else:
            strengths.append("Clear date formatting for work history")
        
        action_verb_count = sum(1 for verb in self.action_verbs if verb in cv_content.lower())
        if action_verb_count < 5:
            issues.append(f"Use more action verbs (currently {action_verb_count}, aim for 8+)")
        else:
            strengths.append(f"Good use of action verbs ({action_verb_count} found)")
        
        return {
            "score": self._calculate_ats_score(cv_content, target_country),
            "issues": issues,
            "strengths": strengths,
            "ats_friendly": len(issues) <= 2
        }
    
    def _analyze_format(self, cv_content: str, target_country: str) -> Dict[str, Any]:
        """Analyze CV format for target country"""
        suggestions = []
        
        word_count = len(cv_content.split())
        
        if target_country == "uk":
            if word_count > 1000:
                suggestions.append("UK CVs should be max 2 pages (around 800-1000 words)")
            if "personal statement" not in cv_content.lower():
                suggestions.append("Add a personal statement at the top (3-4 lines)")
            if "references" not in cv_content.lower():
                suggestions.append("Add 'References available upon request' at bottom")
        
        elif target_country == "usa":
            if word_count > 800:
                suggestions.append("US resumes should be 1-2 pages (around 600-800 words)")
            if not any(word in cv_content.lower() for word in ["summary", "objective", "profile"]):
                suggestions.append("Add a professional summary at the top")
        
        return {
            "word_count": word_count,
            "suggestions": suggestions,
            "format_score": 100 - (len(suggestions) * 15)
        }
    
    def _analyze_content_quality(self, cv_content: str, industry: str) -> Dict[str, Any]:
        """Analyze content quality and relevance"""
        improvements = []
        
        quantification_count = len(re.findall(r'\d+%|\d+\s*percent|\d+x|\$\d+', cv_content))
        if quantification_count < 3:
            improvements.append(
                "Add more quantified achievements (percentages, numbers, dollar amounts)"
            )
        
        if industry in self.ats_keywords:
            industry_keywords = self.ats_keywords[industry]
            found_keywords = [kw for kw in industry_keywords if kw.lower() in cv_content.lower()]
            if len(found_keywords) < len(industry_keywords) * 0.3:
                missing = [kw for kw in industry_keywords if kw.lower() not in cv_content.lower()]
                improvements.append(
                    f"Add more industry-specific keywords: {', '.join(missing[:5])}"
                )
        
        return {
            "quantification_score": min(quantification_count * 20, 100),
            "improvements": improvements
        }
    
    def _analyze_keywords(self, cv_content: str, industry: str) -> Dict[str, Any]:
        """Analyze keyword optimization"""
        if industry not in self.ats_keywords:
            return {"message": "Industry not in database", "score": 50}
        
        industry_keywords = self.ats_keywords[industry]
        cv_lower = cv_content.lower()
        
        found = [kw for kw in industry_keywords if kw.lower() in cv_lower]
        missing = [kw for kw in industry_keywords if kw.lower() not in cv_lower]
        
        score = (len(found) / len(industry_keywords)) * 100
        
        return {
            "score": round(score, 1),
            "found_keywords": found,
            "missing_keywords": missing[:10],
            "recommendation": f"Add {len(missing)} more industry keywords to improve ATS score"
        }
    
    def _get_market_tips(self, target_country: str, target_role: str) -> List[str]:
        """Get market-specific tips"""
        tips = {
            "uk": [
                "Use British English spelling (e.g., 'organisation', 'colour')",
                "Include a personal statement at the top",
                "Keep to 2 pages maximum",
                "List education in reverse chronological order",
                "Include professional memberships if relevant",
                "No need to include photo unless requested",
                "Add 'References available upon request'"
            ],
            "usa": [
                "Use American English spelling (e.g., 'organization', 'color')",
                "Start with a professional summary",
                "Keep to 1-2 pages maximum",
                "Emphasize quantified achievements",
                "Include GPA if recent graduate (above 3.0)",
                "Do not include photo",
                "Focus on results and impact"
            ]
        }
        return tips.get(target_country, [])
    
    def _create_optimization_action_plan(self, cv_content: str, target_country: str,
                                          target_role: str, target_industry: str) -> List[Dict[str, str]]:
        """Create step-by-step action plan for CV optimization"""
        plan = []
        
        plan.append({
            "step": 1,
            "action": "Format Optimization",
            "description": f"Adjust CV format for {target_country.upper()} market standards",
            "priority": "High"
        })
        
        plan.append({
            "step": 2,
            "action": "Keyword Integration",
            "description": f"Add industry-specific keywords for {target_industry}",
            "priority": "High"
        })
        
        plan.append({
            "step": 3,
            "action": "Achievement Quantification",
            "description": "Add numbers, percentages, and metrics to all achievements",
            "priority": "High"
        })
        
        plan.append({
            "step": 4,
            "action": "ATS Optimization",
            "description": "Remove special characters and ensure ATS compatibility",
            "priority": "Medium"
        })
        
        plan.append({
            "step": 5,
            "action": "Action Verb Enhancement",
            "description": "Replace weak verbs with strong action verbs",
            "priority": "Medium"
        })
        
        return plan
    
    def _calculate_overall_cv_score(self, cv_content: str, target_country: str) -> int:
        """Calculate overall CV score"""
        ats_score = self._calculate_ats_score(cv_content, target_country)
        
        word_count = len(cv_content.split())
        length_score = 100 if 400 <= word_count <= 1000 else 70
        
        quantification_count = len(re.findall(r'\d+%|\d+\s*percent|\d+x', cv_content))
        quant_score = min(quantification_count * 15, 100)
        
        overall = (ats_score * 0.4 + length_score * 0.3 + quant_score * 0.3)
        return round(overall)


class LinkedInOptimizer:
    """LinkedIn profile optimization for job search"""
    
    async def optimize(self, profile_data: Dict[str, Any], target_country: str) -> Dict[str, Any]:
        """Optimize LinkedIn profile"""
        
        headline_analysis = self._analyze_headline(profile_data.get("headline", ""))
        summary_analysis = self._analyze_summary(profile_data.get("summary", ""))
        experience_analysis = self._analyze_experience(profile_data.get("experience", []))
        skills_analysis = self._analyze_skills(profile_data.get("skills", []))
        
        return {
            "overall_score": self._calculate_profile_score(profile_data),
            "headline": headline_analysis,
            "summary": summary_analysis,
            "experience": experience_analysis,
            "skills": skills_analysis,
            "optimization_tips": self._get_optimization_tips(target_country),
            "recruiter_visibility_score": self._calculate_recruiter_visibility(profile_data)
        }
    
    def _analyze_headline(self, headline: str) -> Dict[str, Any]:
        """Analyze LinkedIn headline"""
        suggestions = []
        
        if len(headline) < 50:
            suggestions.append("Expand headline to 100-120 characters for maximum impact")
        
        if not any(char.isdigit() for char in headline):
            suggestions.append("Consider adding years of experience or achievements")
        
        keywords = ["specialist", "expert", "manager", "developer", "engineer", "consultant"]
        if not any(kw in headline.lower() for kw in keywords):
            suggestions.append("Include job title or professional designation")
        
        return {
            "current_length": len(headline),
            "suggestions": suggestions,
            "score": 100 - (len(suggestions) * 20)
        }
    
    def _analyze_summary(self, summary: str) -> Dict[str, Any]:
        """Analyze LinkedIn summary"""
        suggestions = []
        
        if len(summary) < 200:
            suggestions.append("Expand summary to 200-300 words for better visibility")
        
        if not re.search(r'\d+\s*years?', summary.lower()):
            suggestions.append("Mention years of experience")
        
        if "passionate" not in summary.lower() and "dedicated" not in summary.lower():
            suggestions.append("Add personal touch showing passion for your field")
        
        return {
            "word_count": len(summary.split()),
            "suggestions": suggestions,
            "score": 100 - (len(suggestions) * 15)
        }
    
    def _analyze_experience(self, experience: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze experience section"""
        suggestions = []
        
        if len(experience) < 2:
            suggestions.append("Add more work experience entries")
        
        for exp in experience:
            if not exp.get("description"):
                suggestions.append(f"Add description for {exp.get('title', 'position')}")
        
        return {
            "entry_count": len(experience),
            "suggestions": suggestions,
            "score": min(len(experience) * 25, 100)
        }
    
    def _analyze_skills(self, skills: List[str]) -> Dict[str, Any]:
        """Analyze skills section"""
        suggestions = []
        
        if len(skills) < 10:
            suggestions.append(f"Add more skills (current: {len(skills)}, aim for 20-30)")
        
        if len(skills) > 50:
            suggestions.append("Focus on most relevant skills (max 50)")
        
        return {
            "skill_count": len(skills),
            "suggestions": suggestions,
            "score": min(len(skills) * 3, 100)
        }
    
    def _calculate_profile_score(self, profile_data: Dict[str, Any]) -> int:
        """Calculate overall profile score"""
        score = 0
        
        if profile_data.get("headline"):
            score += 20
        if profile_data.get("summary") and len(profile_data["summary"]) > 200:
            score += 25
        if profile_data.get("experience") and len(profile_data["experience"]) >= 2:
            score += 25
        if profile_data.get("skills") and len(profile_data["skills"]) >= 10:
            score += 20
        if profile_data.get("photo"):
            score += 10
        
        return score
    
    def _get_optimization_tips(self, target_country: str) -> List[str]:
        """Get LinkedIn optimization tips"""
        return [
            "Use a professional headshot photo",
            "Create a compelling headline with keywords",
            "Write a detailed summary highlighting achievements",
            "Add rich media to showcase work",
            "Get recommendations from colleagues",
            "Join relevant industry groups",
            "Post regularly to increase visibility",
            "Engage with content in your field",
            "Use LinkedIn's 'Open to Work' feature",
            "Customize your LinkedIn URL"
        ]
    
    def _calculate_recruiter_visibility(self, profile_data: Dict[str, Any]) -> int:
        """Calculate how visible profile is to recruiters"""
        score = 0
        
        if profile_data.get("headline") and len(profile_data["headline"]) > 50:
            score += 25
        if profile_data.get("summary"):
            score += 20
        if profile_data.get("skills") and len(profile_data["skills"]) >= 15:
            score += 25
        if profile_data.get("experience") and len(profile_data["experience"]) >= 2:
            score += 20
        if profile_data.get("recommendations", 0) > 0:
            score += 10
        
        return score


class JobSearchAutomation:
    """Automated job search and application tracking"""
    
    async def search(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for jobs based on criteria"""
        return []
    
    async def create_strategy(self, profile: Dict[str, Any], target_country: str) -> Dict[str, Any]:
        """Create comprehensive job search strategy"""
        
        return {
            "daily_actions": [
                "Apply to 5-10 relevant positions",
                "Send 3-5 personalized connection requests on LinkedIn",
                "Engage with 5-10 posts in your industry",
                "Research 2-3 target companies",
                "Update application tracker"
            ],
            "weekly_actions": [
                "Attend 1-2 networking events or webinars",
                "Reach out to 2-3 recruiters in your field",
                "Update LinkedIn profile with new skills or achievements",
                "Review and refine CV based on feedback",
                "Follow up on applications from previous week"
            ],
            "monthly_actions": [
                "Conduct informational interviews with 2-3 professionals",
                "Review and update job search strategy",
                "Assess skill gaps and plan learning",
                "Network with alumni or professional associations",
                "Evaluate job search progress and adjust approach"
            ],
            "application_tracking": {
                "categories": ["Applied", "Phone Screen", "Interview", "Offer", "Rejected"],
                "metrics_to_track": [
                    "Number of applications sent",
                    "Response rate",
                    "Interview conversion rate",
                    "Average time to response",
                    "Offer rate"
                ]
            },
            "job_boards_priority": self._get_job_boards_for_country(target_country),
            "networking_strategy": self._get_networking_strategy(target_country)
        }
    
    def _get_job_boards_for_country(self, country: str) -> List[Dict[str, str]]:
        """Get prioritized job boards for country"""
        boards = {
            "uk": [
                {"name": "LinkedIn", "priority": "High", "focus": "Professional networking"},
                {"name": "Indeed UK", "priority": "High", "focus": "General jobs"},
                {"name": "Reed", "priority": "High", "focus": "All industries"},
                {"name": "Totaljobs", "priority": "Medium", "focus": "General jobs"},
                {"name": "CV-Library", "priority": "Medium", "focus": "All industries"}
            ],
            "usa": [
                {"name": "LinkedIn", "priority": "High", "focus": "Professional networking"},
                {"name": "Indeed", "priority": "High", "focus": "General jobs"},
                {"name": "Glassdoor", "priority": "High", "focus": "Company reviews"},
                {"name": "ZipRecruiter", "priority": "Medium", "focus": "General jobs"},
                {"name": "Monster", "priority": "Medium", "focus": "All industries"}
            ]
        }
        return boards.get(country, boards["uk"])
    
    def _get_networking_strategy(self, country: str) -> Dict[str, Any]:
        """Get networking strategy for country"""
        return {
            "platforms": ["LinkedIn", "Meetup", "Eventbrite", "Professional associations"],
            "activities": [
                "Join industry-specific LinkedIn groups",
                "Attend virtual and in-person networking events",
                "Participate in online communities and forums",
                "Connect with alumni from your university",
                "Engage with thought leaders in your field"
            ],
            "connection_message_template": "Hi [Name], I noticed we both work in [Industry]. I'm currently exploring opportunities in [Field] and would love to connect and learn from your experience."
        }


class RecruiterConnectionGuide:
    """Guide for connecting with recruiters"""
    
    async def get_connection_strategy(self, industry: str, target_country: str) -> Dict[str, Any]:
        """Get detailed recruiter connection strategy"""
        
        return {
            "finding_recruiters": {
                "linkedin_search": [
                    f"Search: 'Recruiter {industry} {target_country}'",
                    f"Search: 'Talent Acquisition {industry}'",
                    f"Search: 'Headhunter {industry}'",
                    "Filter by location and current company"
                ],
                "recruitment_agencies": self._get_agencies_by_country(target_country),
                "company_recruiters": [
                    "Visit target company LinkedIn pages",
                    "Look for 'Talent Acquisition' or 'Recruitment' team members",
                    "Check company careers page for recruiter contacts"
                ]
            },
            "connection_approach": {
                "linkedin_message_template": """Hi [Recruiter Name],

I hope this message finds you well. I noticed you specialize in recruiting for [Industry/Role] positions at [Company/Agency].

I'm a [Your Role] with [X] years of experience in [Key Skills/Areas]. I'm currently exploring opportunities in [Target Area] and would appreciate the chance to connect.

I'd be happy to share my CV and discuss how my background might align with roles you're working on.

Best regards,
[Your Name]""",
                "email_template": """Subject: [Your Role] - [X] Years Experience in [Industry]

Dear [Recruiter Name],

I am writing to introduce myself as a [Your Role] with [X] years of experience in [Industry]. I am currently seeking opportunities in [Target Country/Area].

Key highlights of my background:
- [Achievement 1]
- [Achievement 2]
- [Achievement 3]

I have attached my CV for your review. I would welcome the opportunity to discuss how my skills and experience might benefit your clients.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Phone] | [Email] | [LinkedIn URL]""",
                "timing": "Tuesday-Thursday, 9-11 AM or 2-4 PM local time",
                "follow_up": "Follow up after 1 week if no response"
            },
            "building_relationships": [
                "Engage with recruiter's LinkedIn posts",
                "Share relevant industry content",
                "Provide updates on your job search progress",
                "Be responsive and professional in all communications",
                "Thank recruiters for their time and assistance",
                "Stay in touch even after finding a job"
            ],
            "dos_and_donts": {
                "do": [
                    "Personalize each message",
                    "Be clear about your goals and availability",
                    "Keep CV updated and ready to share",
                    "Be responsive to recruiter outreach",
                    "Provide specific examples of your experience",
                    "Ask about the application process and timeline"
                ],
                "dont": [
                    "Send generic mass messages",
                    "Be pushy or demanding",
                    "Lie or exaggerate your experience",
                    "Ignore recruiter messages",
                    "Apply to every job without consideration",
                    "Burn bridges or be unprofessional"
                ]
            },
            "recruiter_types": {
                "internal_recruiters": {
                    "description": "Work directly for companies",
                    "approach": "Target specific companies you want to work for",
                    "advantage": "Direct access to company opportunities"
                },
                "agency_recruiters": {
                    "description": "Work for recruitment agencies",
                    "approach": "Build relationships with multiple agencies",
                    "advantage": "Access to multiple company opportunities"
                },
                "headhunters": {
                    "description": "Specialize in senior/executive roles",
                    "approach": "Build reputation and let them find you",
                    "advantage": "Access to exclusive high-level positions"
                }
            }
        }
    
    def _get_agencies_by_country(self, country: str) -> List[Dict[str, str]]:
        """Get recruitment agencies by country"""
        agencies = {
            "uk": [
                {"name": "Hays", "specialization": "Multiple industries", "website": "hays.co.uk"},
                {"name": "Michael Page", "specialization": "Professional services", "website": "michaelpage.co.uk"},
                {"name": "Robert Half", "specialization": "Finance & tech", "website": "roberthalf.co.uk"},
                {"name": "Reed Specialist Recruitment", "specialization": "All industries", "website": "reed.co.uk"},
                {"name": "Adecco", "specialization": "General recruitment", "website": "adecco.co.uk"}
            ],
            "usa": [
                {"name": "Robert Half", "specialization": "Finance & tech", "website": "roberthalf.com"},
                {"name": "Kelly Services", "specialization": "Multiple industries", "website": "kellyservices.com"},
                {"name": "Aerotek", "specialization": "Engineering & tech", "website": "aerotek.com"},
                {"name": "Randstad USA", "specialization": "General recruitment", "website": "randstadusa.com"},
                {"name": "TEKsystems", "specialization": "IT & tech", "website": "teksystems.com"}
            ]
        }
        return agencies.get(country, agencies["uk"])


class FreelancingGuide:
    """Freelancing guidance and platform recommendations"""
    
    async def create_strategy(self, skills: List[str], experience_level: str) -> Dict[str, Any]:
        """Create freelancing strategy"""
        
        return {
            "recommended_platforms": self._get_platforms_by_skills(skills, experience_level),
            "profile_optimization": {
                "headline": "Create compelling headline highlighting your expertise",
                "overview": "Write detailed overview with achievements and specializations",
                "portfolio": "Showcase 5-10 best work samples",
                "skills": "List all relevant skills with proficiency levels",
                "rates": self._get_rate_recommendations(experience_level)
            },
            "getting_started": [
                "Complete profile 100% on chosen platforms",
                "Start with competitive rates to build portfolio",
                "Apply to 10-15 jobs daily initially",
                "Deliver exceptional work to get 5-star reviews",
                "Request testimonials from satisfied clients",
                "Gradually increase rates as you build reputation"
            ],
            "pricing_strategy": {
                "beginner": "$15-30/hour or $100-500 per project",
                "intermediate": "$30-60/hour or $500-2000 per project",
                "expert": "$60-150+/hour or $2000+ per project",
                "tips": [
                    "Research market rates for your skills",
                    "Consider value-based pricing for projects",
                    "Offer package deals for repeat clients",
                    "Increase rates by 10-20% every 6 months",
                    "Don't undervalue your expertise"
                ]
            },
            "client_acquisition": [
                "Optimize profile for platform search algorithms",
                "Write personalized proposals for each job",
                "Respond quickly to client messages",
                "Ask clarifying questions before bidding",
                "Showcase relevant past work in proposals",
                "Follow up professionally if no response"
            ],
            "success_tips": [
                "Communicate clearly and frequently",
                "Set realistic deadlines and meet them",
                "Go above and beyond client expectations",
                "Request feedback and reviews",
                "Build long-term client relationships",
                "Diversify income across multiple clients",
                "Save for taxes (25-30% of income)",
                "Invest in continuous learning"
            ]
        }
    
    def _get_platforms_by_skills(self, skills: List[str], experience_level: str) -> List[Dict[str, Any]]:
        """Get recommended platforms based on skills"""
        platforms = [
            {
                "name": "Upwork",
                "best_for": "All skill levels, wide range of services",
                "fee": "5-20% based on earnings",
                "url": "upwork.com"
            },
            {
                "name": "Fiverr",
                "best_for": "Beginners, service packages",
                "fee": "20% of earnings",
                "url": "fiverr.com"
            },
            {
                "name": "Toptal",
                "best_for": "Experienced professionals, high-end clients",
                "fee": "Varies",
                "url": "toptal.com"
            },
            {
                "name": "Freelancer",
                "best_for": "All levels, competitive bidding",
                "fee": "10% or $5 minimum",
                "url": "freelancer.com"
            },
            {
                "name": "PeoplePerHour",
                "best_for": "UK/European market",
                "fee": "3.5-20% based on earnings",
                "url": "peopleperhour.com"
            }
        ]
        
        if experience_level == "expert":
            platforms.insert(0, {
                "name": "Toptal",
                "best_for": "Top 3% of freelancers",
                "fee": "Varies",
                "url": "toptal.com"
            })
        
        return platforms
    
    def _get_rate_recommendations(self, experience_level: str) -> Dict[str, str]:
        """Get rate recommendations by experience level"""
        rates = {
            "beginner": {
                "hourly": "$15-30/hour",
                "project": "$100-500 per project",
                "advice": "Focus on building portfolio and reviews"
            },
            "intermediate": {
                "hourly": "$30-60/hour",
                "project": "$500-2000 per project",
                "advice": "Emphasize quality and specialization"
            },
            "expert": {
                "hourly": "$60-150+/hour",
                "project": "$2000+ per project",
                "advice": "Position as premium service provider"
            }
        }
        return rates.get(experience_level, rates["intermediate"])
