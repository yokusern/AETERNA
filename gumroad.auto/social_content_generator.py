#!/usr/bin/env python3
"""
Social Media Content Generator - For Pinterest & Twitter (Semi-Automated)
Generates ready-to-post content - you copy-paste into scheduling tools
"""

import os
import json
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "social_content"
CONTENT_DIR.mkdir(exist_ok=True)


class SocialContentGenerator:
    """Generate social media content for Pinterest & Twitter"""
    
    def __init__(self):
        self.products_dir = BASE_DIR / "products"
    
    def get_latest_products(self, count=5):
        """Get latest products from products directory"""
        products = []
        if not self.products_dir.exists():
            return products
        
        product_dirs = sorted(
            [d for d in self.products_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for dir_path in product_dirs:
            spec_file = dir_path / "spec.json"
            if spec_file.exists():
                with open(spec_file, 'r', encoding='utf-8') as f:
                    spec = json.load(f)
                
                if "subcategory" in spec and "price_usd" in spec:
                    products.append({
                        "dir": dir_path,
                        "spec": spec
                    })
                    if len(products) >= count:
                        break
        return products
    
    def generate_pinterest_pin(self, product_spec):
        """Generate Pinterest Pin content"""
        price = product_spec.get('price_usd', product_spec.get('price', 15))
        
        title_templates = [
            f"{product_spec['name']}: Your Ultimate Guide",
            f"Get {product_spec['name']} Now",
            f"Master {product_spec['subcategory']} with {product_spec['name']}",
            f"{product_spec['name']} - Everything You Need",
            f"Transform Your {product_spec['subcategory']} Skills"
        ]
        
        description_templates = [
            f"Discover the ultimate guide to {product_spec['subcategory']}. This {product_spec['product_type']} is perfect for beginners and intermediate learners. Get yours today for ${price}!",
            f"Ready to master {product_spec['subcategory']}? This comprehensive {product_spec['product_type']} has everything you need. Download now and start learning!",
            f"Looking for the best {product_spec['subcategory']} resource? Look no further! This {product_spec['product_type']} is packed with value. Get it for ${price}!"
        ]
        
        hashtags = self._get_hashtags(product_spec['category'], product_spec['subcategory'])
        
        return {
            "platform": "Pinterest",
            "title": random.choice(title_templates),
            "description": random.choice(description_templates),
            "hashtags": hashtags,
            "price": f"${price}",
            "product_name": product_spec['name'],
            "category": product_spec['category'],
            "subcategory": product_spec['subcategory']
        }
    
    def generate_twitter_tweet(self, product_spec):
        """Generate Twitter/X tweet content"""
        price = product_spec.get('price_usd', product_spec.get('price', 15))
        
        hooks = [
            "I just created this...",
            "Stop scrolling, check this out...",
            "Here's how to...",
            "You're missing out on...",
            "This changed how I..."
        ]
        
        templates = [
            f"{random.choice(hooks)} {product_spec['name']} - your guide to {product_spec['subcategory']}. ${price} #DigitalProduct #{product_spec['subcategory'].replace(' ', '')}",
            f"Want to learn {product_spec['subcategory']}? Check out {product_spec['name']} - only ${price}! #{product_spec['category']} #{product_spec['subcategory'].replace(' ', '')}",
            f"Just launched: {product_spec['name']} - the ultimate {product_spec['product_type']} for {product_spec['subcategory']}. Get it now! ${price}"
        ]
        
        return {
            "platform": "Twitter/X",
            "tweet": random.choice(templates),
            "product_name": product_spec['name'],
            "price": f"${price}"
        }
    
    def _get_hashtags(self, category, subcategory):
        """Get relevant hashtags"""
        base_hashtags = [
            "#DigitalProduct", "#PassiveIncome", "#SideHustle",
            "#Maker", "#IndieHacker", "#OnlineBusiness",
            "#CreatorEconomy", "#DigitalDownload"
        ]
        
        category_tags = {
            "Programming": ["#Programming", "#Coding", "#WebDev", "#Tech"],
            "Business": ["#Business", "#Entrepreneur", "#Startup", "#Freelance"],
            "Productivity": ["#Productivity", "#Notion", "#Workflow", "#Efficiency"],
            "Design": ["#Design", "#UIUX", "#Creative", "#GraphicDesign"],
            "AI": ["#AI", "#ArtificialIntelligence", "#MachineLearning", "#PromptEngineering"],
            "Marketing": ["#Marketing", "#SocialMedia", "#SEO", "#ContentMarketing"]
        }
        
        tags = base_hashtags.copy()
        tags.extend(category_tags.get(category, []))
        tags.append(f"#{subcategory.replace(' ', '')}")
        
        return list(set(tags))[:10]  # Max 10 hashtags
    
    def generate_batch_content(self, product_count=5):
        """Generate content for multiple products"""
        products = self.get_latest_products(product_count)
        if not products:
            return {"message": "No products found"}
        
        all_content = []
        
        for product in products:
            pinterest = self.generate_pinterest_pin(product["spec"])
            twitter = self.generate_twitter_tweet(product["spec"])
            
            all_content.append({
                "product_id": product["spec"]["product_id"],
                "product_name": product["spec"]["name"],
                "pinterest": pinterest,
                "twitter": twitter
            })
        
        return all_content
    
    def save_content(self, content_batch):
        """Save generated content to file"""
        timestamp = int(datetime.now().timestamp())
        file_path = CONTENT_DIR / f"social_content_{timestamp}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content_batch, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def print_content_summary(self, content_batch):
        """Print human-readable summary"""
        print("=" * 70)
        print("  📱 Social Media Content Ready!")
        print("=" * 70)
        
        for i, item in enumerate(content_batch, 1):
            print(f"\n[{i}] {item['product_name']}")
            
            print("\n  📌 Pinterest:")
            print(f"     Title: {item['pinterest']['title']}")
            print(f"     Description: {item['pinterest']['description'][:100]}...")
            print(f"     Hashtags: {' '.join(item['pinterest']['hashtags'][:5])}...")
            
            print("\n  🐦 Twitter/X:")
            print(f"     {item['twitter']['tweet']}")
        
        print("\n" + "=" * 70)
        print("  💡 Copy-paste into scheduling tools (Buffer, Later, etc.)")
        print("=" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate social media content (Pinterest & Twitter)')
    parser.add_argument('--count', type=int, default=5, help='Number of products to generate for (default:5)')
    
    args = parser.parse_args()
    
    generator = SocialContentGenerator()
    
    print("\n🔍 Finding latest products...")
    content_batch = generator.generate_batch_content(args.count)
    
    if "message" in content_batch:
        print(f"\n⚠️  {content_batch['message']}")
        print("   First, create some products with: python main.py")
    else:
        file_path = generator.save_content(content_batch)
        generator.print_content_summary(content_batch)
        print(f"\n✅ Full content saved to: {file_path}")


if __name__ == "__main__":
    main()
