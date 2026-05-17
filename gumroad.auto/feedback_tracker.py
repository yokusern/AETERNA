#!/usr/bin/env python3
"""
Feedback Tracker - Learning from product approvals/rejections
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
FEEDBACK_DIR = BASE_DIR / "system" / "feedback"
DATA_DIR = BASE_DIR / "system" / "data"

FEEDBACK_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


class FeedbackTracker:
    """Track product feedback and learn from it"""

    def __init__(self):
        self.feedback_file = FEEDBACK_DIR / "product_feedback.json"
        self.market_data_file = DATA_DIR / "market_analysis.json"

    def load_feedback(self):
        """Load all feedback data"""
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"approved": [], "rejected": []}

    def save_feedback(self, feedback):
        """Save feedback data"""
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

    def record_approval(self, product_spec, reason="", notes=""):
        """Record an approved product"""
        feedback = self.load_feedback()
        entry = {
            "product_id": product_spec["product_id"],
            "name": product_spec["name"],
            "category": product_spec["category"],
            "subcategory": product_spec["subcategory"],
            "product_type": product_spec["product_type"],
            "price": product_spec.get("price_usd", product_spec.get("price")),
            "trend_score": product_spec.get("trend_score"),
            "reason": reason,
            "notes": notes,
            "recorded_at": datetime.now().isoformat()
        }
        feedback["approved"].append(entry)
        self.save_feedback(feedback)
        self._update_market_trends()
        print(f"✅ Approval recorded for: {product_spec['name']}")
        return entry

    def record_rejection(self, product_spec, reason="", notes=""):
        """Record a rejected product"""
        feedback = self.load_feedback()
        entry = {
            "product_id": product_spec["product_id"],
            "name": product_spec["name"],
            "category": product_spec["category"],
            "subcategory": product_spec["subcategory"],
            "product_type": product_spec["product_type"],
            "price": product_spec.get("price_usd", product_spec.get("price")),
            "trend_score": product_spec.get("trend_score"),
            "reason": reason,
            "notes": notes,
            "recorded_at": datetime.now().isoformat()
        }
        feedback["rejected"].append(entry)
        self.save_feedback(feedback)
        self._update_market_trends()
        print(f"❌ Rejection recorded for: {product_spec['name']}")
        return entry

    def _update_market_trends(self):
        """Update market trends based on feedback"""
        feedback = self.load_feedback()
        
        if not feedback["approved"] and not feedback["rejected"]:
            return
        
        category_stats = {}
        
        for item in feedback["approved"]:
            key = f"{item['category']}:{item['subcategory']}"
            if key not in category_stats:
                category_stats[key] = {"approved": 0, "rejected": 0, "total": 0}
            category_stats[key]["approved"] += 1
            category_stats[key]["total"] += 1
        
        for item in feedback["rejected"]:
            key = f"{item['category']}:{item['subcategory']}"
            if key not in category_stats:
                category_stats[key] = {"approved": 0, "rejected": 0, "total": 0}
            category_stats[key]["rejected"] += 1
            category_stats[key]["total"] += 1
        
        market_data = self._load_market_data()
        
        for category in market_data["trending_categories"]:
            key = f"{category['category']}:{category['subcategory']}"
            if key in category_stats:
                stats = category_stats[key]
                approval_rate = stats["approved"] / stats["total"] if stats["total"] > 0 else 0.5
                
                category["approval_rate"] = approval_rate
                category["total_reviews"] = stats["total"]
                category["trend_score"] = min(100, category.get("trend_score", 50) + (approval_rate * 20) - (stats["rejected"] * 5))
        
        market_data["last_updated"] = datetime.now().isoformat()
        self._save_market_data(market_data)
        print("📊 Market trends updated based on feedback")

    def _load_market_data(self):
        """Load market data"""
        if self.market_data_file.exists():
            with open(self.market_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._generate_default_data()

    def _generate_default_data(self):
        """Generate default market data"""
        return {
            "trending_categories": [
                {"category": "Programming", "subcategory": "Python", "trend_score": 95, "user_demand": "high", "avg_price": 15},
                {"category": "Programming", "subcategory": "Data Analysis", "trend_score": 92, "user_demand": "high", "avg_price": 25},
                {"category": "Business", "subcategory": "Side Hustle", "trend_score": 88, "user_demand": "high", "avg_price": 9},
                {"category": "Programming", "subcategory": "React", "trend_score": 85, "user_demand": "high", "avg_price": 20},
                {"category": "AI", "subcategory": "Prompt Engineering", "trend_score": 90, "user_demand": "high", "avg_price": 15},
                {"category": "Business", "subcategory": "Freelancing", "trend_score": 85, "user_demand": "high", "avg_price": 12},
                {"category": "Productivity", "subcategory": "Notion Templates", "trend_score": 88, "user_demand": "high", "avg_price": 9},
                {"category": "Design", "subcategory": "UI/UX", "trend_score": 80, "user_demand": "medium", "avg_price": 19},
                {"category": "Marketing", "subcategory": "Social Media", "trend_score": 82, "user_demand": "medium", "avg_price": 14}
            ],
            "content_ideas": []
        }

    def _save_market_data(self, data):
        """Save market data"""
        with open(self.market_data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_insights(self):
        """Get learning insights from feedback"""
        feedback = self.load_feedback()
        
        if not feedback["approved"] and not feedback["rejected"]:
            return {"message": "No feedback yet"}
        
        approved_count = len(feedback["approved"])
        rejected_count = len(feedback["rejected"])
        
        category_counts = {}
        for item in feedback["approved"]:
            key = f"{item['category']}:{item['subcategory']}"
            category_counts[key] = category_counts.get(key, 0) + 1
        
        top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        rejection_reasons = {}
        for item in feedback["rejected"]:
            if item["reason"]:
                rejection_reasons[item["reason"]] = rejection_reasons.get(item["reason"], 0) + 1
        
        return {
            "total_approved": approved_count,
            "total_rejected": rejected_count,
            "approval_rate": approved_count / (approved_count + rejected_count) if (approved_count + rejected_count) > 0 else 0,
            "top_categories": top_categories,
            "common_rejection_reasons": rejection_reasons,
            "last_updated": datetime.now().isoformat()
        }

    def print_summary(self):
        """Print a human-readable summary"""
        insights = self.get_insights()
        
        print("=" * 70)
        print("  📊 Feedback Learning Summary")
        print("=" * 70)
        
        if "message" in insights:
            print(f"\n  ℹ️ {insights['message']}")
        else:
            print(f"\n  ✅ Approved: {insights['total_approved']}")
            print(f"  ❌ Rejected: {insights['total_rejected']}")
            print(f"  📈 Approval Rate: {insights['approval_rate']*100:.1f}%")
            
            if insights['top_categories']:
                print(f"\n  🏆 Top Categories:")
                for cat, count in insights['top_categories']:
                    print(f"     - {cat}: {count} approvals")
            
            if insights['common_rejection_reasons']:
                print(f"\n  ⚠️ Common Rejection Reasons:")
                for reason, count in insights['common_rejection_reasons'].items():
                    print(f"     - {reason}: {count} times")
        
        print("\n" + "=" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Feedback Tracker - Learn from product decisions')
    parser.add_argument('--summary', action='store_true', help='Show feedback summary')
    
    args = parser.parse_args()
    
    tracker = FeedbackTracker()
    
    if args.summary:
        tracker.print_summary()
    else:
        print("📋 Feedback Tracker")
        print("\nUsage:")
        print("  python feedback_tracker.py --summary  # Show summary")
        print("\n(Programmatic use: Import FeedbackTracker class)")


if __name__ == "__main__":
    main()
