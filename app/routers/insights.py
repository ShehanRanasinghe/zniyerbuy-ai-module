from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List

router = APIRouter()

class PlatformData(BaseModel):
    totalUsers: int
    activeUsers: int
    totalShops: int
    verifiedShops: int
    pendingShops: int
    rejectedShops: int
    totalProducts: int
    flaggedProducts: int
    activeDeals: int
    newUsersThisMonth: int
    dealsThisMonth: int

class InsightsRequest(BaseModel):
    platformData: PlatformData

def generate_platform_insights(data: PlatformData) -> List[str]:
    """
    Generate actionable insights based on platform statistics.
    Uses rule-based logic to provide recommendations.
    """
    insights = []
    
    # User growth analysis
    user_growth_rate = (data.newUsersThisMonth / data.totalUsers * 100) if data.totalUsers > 0 else 0
    if user_growth_rate > 15:
        insights.append(f"Strong user growth of {user_growth_rate:.1f}% this month. Consider scaling infrastructure and support resources.")
    elif user_growth_rate < 5:
        insights.append(f"User growth is {user_growth_rate:.1f}% this month. Launch marketing campaigns or referral programs to boost acquisition.")
    
    # Shop verification analysis
    pending_rate = (data.pendingShops / data.totalShops * 100) if data.totalShops > 0 else 0
    if pending_rate > 20:
        insights.append(f"{data.pendingShops} shops ({pending_rate:.1f}%) are pending verification. Prioritize shop approvals to improve seller satisfaction.")
    
    rejected_rate = (data.rejectedShops / data.totalShops * 100) if data.totalShops > 0 else 0
    if rejected_rate > 10:
        insights.append(f"High shop rejection rate ({rejected_rate:.1f}%). Review verification criteria and provide clearer guidelines to sellers.")
    
    # Product quality analysis
    flagged_rate = (data.flaggedProducts / data.totalProducts * 100) if data.totalProducts > 0 else 0
    if flagged_rate > 3:
        insights.append(f"{data.flaggedProducts} products ({flagged_rate:.1f}%) are flagged. Investigate quality issues and enforce stricter product guidelines.")
    elif flagged_rate < 1:
        insights.append(f"Low flagged product rate ({flagged_rate:.1f}%). Product quality monitoring is effective. Maintain current standards.")
    
    # Deal activity analysis
    deals_per_shop = data.activeDeals / data.verifiedShops if data.verifiedShops > 0 else 0
    if deals_per_shop < 0.5:
        insights.append(f"Only {deals_per_shop:.2f} deals per verified shop. Encourage sellers to create more deals to boost customer engagement.")
    elif deals_per_shop > 2:
        insights.append(f"High deal activity with {deals_per_shop:.2f} deals per shop. Promote these deals on the homepage to drive sales.")
    
    # User engagement analysis
    active_rate = (data.activeUsers / data.totalUsers * 100) if data.totalUsers > 0 else 0
    if active_rate < 80:
        insights.append(f"User engagement is {active_rate:.1f}%. Send personalized notifications and recommendations to re-engage inactive users.")
    
    # Products per shop analysis
    products_per_shop = data.totalProducts / data.verifiedShops if data.verifiedShops > 0 else 0
    if products_per_shop < 10:
        insights.append(f"Average {products_per_shop:.1f} products per shop. Provide seller training and incentives to expand product catalogs.")
    
    # Ensure we always return at least 5 insights
    if len(insights) < 5:
        insights.append("Platform metrics are healthy. Continue monitoring key performance indicators and user feedback.")
        insights.append("Consider A/B testing new features to improve user experience and conversion rates.")
        insights.append("Analyze user behavior patterns to identify opportunities for personalization and targeted marketing.")
    
    # Return exactly 5 insights
    return insights[:5]

@router.post("/generate")
def generate_insights(request: InsightsRequest):
    """
    Generate AI-powered insights for the admin dashboard.
    Analyzes platform statistics and returns actionable recommendations.
    """
    try:
        insights = generate_platform_insights(request.platformData)
        
        return {
            "success": True,
            "insights": insights,
            "method": "rule_based_analysis"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "insights": [
                "Unable to generate insights at this time. Please try again later."
            ]
        }
