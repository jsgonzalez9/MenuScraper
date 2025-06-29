import json
import os

os.makedirs("output", exist_ok=True)

def create_health_focused_menu_data():
    """Create comprehensive demo data for health-focused menu analysis"""
    
    print("=== HEALTH-FOCUSED MENU DATA FOR ALLERGY APP ===")
    print("Creating detailed menu data with allergen and ingredient information\n")
    
    # Comprehensive menu data with detailed allergen and ingredient information
    health_menu_data = [
        {
            "restaurant_name": "Alinea",
            "restaurant_url": "https://www.alinearestaurant.com",
            "cuisine_type": "Contemporary American",
            "price_range": "$$$$",
            "menu_items": [
                {
                    "name": "Grilled Octopus",
                    "description": "Grilled octopus with chickpea puree, olive oil, and lemon",
                    "price": "$28",
                    "potential_allergens": ["shellfish"],
                    "ingredients": ["octopus", "chickpeas", "olive oil", "lemon", "herbs"],
                    "section": "Appetizers",
                    "dietary_info": ["gluten-free", "dairy-free"]
                },
                {
                    "name": "Pan-Seared Salmon",
                    "description": "Atlantic salmon with quinoa, roasted vegetables, and herb butter",
                    "price": "$34",
                    "potential_allergens": ["fish", "dairy"],
                    "ingredients": ["salmon", "quinoa", "broccoli", "carrots", "butter", "herbs"],
                    "section": "Main Courses",
                    "dietary_info": ["gluten-free"]
                },
                {
                    "name": "Chocolate Soufflé",
                    "description": "Dark chocolate soufflé with vanilla ice cream and berry compote",
                    "price": "$16",
                    "potential_allergens": ["dairy", "eggs", "wheat"],
                    "ingredients": ["dark chocolate", "eggs", "flour", "milk", "vanilla", "berries"],
                    "section": "Desserts",
                    "dietary_info": ["vegetarian"]
                }
            ],
            "total_items": 3,
            "allergen_summary": {
                "dairy": 2,
                "eggs": 1,
                "fish": 1,
                "shellfish": 1,
                "wheat": 1
            }
        },
        {
            "restaurant_name": "Girl & the Goat",
            "restaurant_url": "https://www.girlandthegoat.com",
            "cuisine_type": "Contemporary American",
            "price_range": "$$$",
            "menu_items": [
                {
                    "name": "Wood-Fired Pig Face",
                    "description": "Crispy pig face with tamarind, cilantro, mint, and peanuts",
                    "price": "$18",
                    "potential_allergens": ["peanuts"],
                    "ingredients": ["pork", "tamarind", "cilantro", "mint", "peanuts", "chili"],
                    "section": "Small Plates",
                    "dietary_info": ["gluten-free", "dairy-free"]
                },
                {
                    "name": "Goat Empanadas",
                    "description": "House-made empanadas filled with goat meat, served with olive tapenade",
                    "price": "$16",
                    "potential_allergens": ["wheat", "eggs"],
                    "ingredients": ["goat meat", "flour", "eggs", "olives", "capers", "herbs"],
                    "section": "Small Plates",
                    "dietary_info": ["dairy-free"]
                },
                {
                    "name": "Seared Scallops",
                    "description": "Pan-seared scallops with cauliflower puree, raisins, and pine nuts",
                    "price": "$32",
                    "potential_allergens": ["shellfish", "tree_nuts"],
                    "ingredients": ["scallops", "cauliflower", "raisins", "pine nuts", "butter"],
                    "section": "Large Plates",
                    "dietary_info": ["gluten-free"]
                },
                {
                    "name": "Vegetarian Pasta",
                    "description": "House-made pasta with seasonal vegetables, parmesan, and truffle oil",
                    "price": "$24",
                    "potential_allergens": ["wheat", "eggs", "dairy"],
                    "ingredients": ["pasta", "zucchini", "tomatoes", "parmesan", "truffle oil", "basil"],
                    "section": "Large Plates",
                    "dietary_info": ["vegetarian"]
                }
            ],
            "total_items": 4,
            "allergen_summary": {
                "wheat": 2,
                "eggs": 2,
                "dairy": 1,
                "shellfish": 1,
                "tree_nuts": 1,
                "peanuts": 1
            }
        },
        {
            "restaurant_name": "Kuma's Corner",
            "restaurant_url": "https://www.kumascorner.com",
            "cuisine_type": "American Burger Joint",
            "price_range": "$$",
            "menu_items": [
                {
                    "name": "The Kuma Burger",
                    "description": "1/3 lb beef patty with bacon, cheddar cheese, lettuce, tomato on brioche bun",
                    "price": "$16",
                    "potential_allergens": ["wheat", "dairy", "eggs"],
                    "ingredients": ["beef", "bacon", "cheddar cheese", "lettuce", "tomato", "brioche bun"],
                    "section": "Burgers",
                    "dietary_info": []
                },
                {
                    "name": "Veggie Burger",
                    "description": "House-made black bean patty with avocado, sprouts, and vegan mayo",
                    "price": "$14",
                    "potential_allergens": ["wheat", "soy"],
                    "ingredients": ["black beans", "avocado", "sprouts", "vegan mayo", "whole wheat bun"],
                    "section": "Burgers",
                    "dietary_info": ["vegetarian", "vegan"]
                },
                {
                    "name": "Buffalo Chicken Wings",
                    "description": "Crispy chicken wings tossed in buffalo sauce, served with celery and blue cheese",
                    "price": "$12",
                    "potential_allergens": ["dairy"],
                    "ingredients": ["chicken wings", "buffalo sauce", "celery", "blue cheese", "hot sauce"],
                    "section": "Appetizers",
                    "dietary_info": ["gluten-free"]
                },
                {
                    "name": "Fish Tacos",
                    "description": "Grilled mahi-mahi with cabbage slaw, pico de gallo, and chipotle crema",
                    "price": "$15",
                    "potential_allergens": ["fish", "dairy"],
                    "ingredients": ["mahi-mahi", "cabbage", "tomatoes", "onions", "sour cream", "corn tortillas"],
                    "section": "Entrees",
                    "dietary_info": ["gluten-free"]
                }
            ],
            "total_items": 4,
            "allergen_summary": {
                "wheat": 2,
                "dairy": 3,
                "eggs": 1,
                "fish": 1,
                "soy": 1
            }
        },
        {
            "restaurant_name": "Arun's Thai",
            "restaurant_url": "https://www.arunsthai.com",
            "cuisine_type": "Thai",
            "price_range": "$$$",
            "menu_items": [
                {
                    "name": "Pad Thai",
                    "description": "Stir-fried rice noodles with shrimp, tofu, bean sprouts, and peanuts",
                    "price": "$18",
                    "potential_allergens": ["shellfish", "soy", "peanuts", "fish"],
                    "ingredients": ["rice noodles", "shrimp", "tofu", "bean sprouts", "peanuts", "fish sauce"],
                    "section": "Noodles",
                    "dietary_info": ["gluten-free"]
                },
                {
                    "name": "Green Curry",
                    "description": "Thai green curry with chicken, eggplant, bamboo shoots, and coconut milk",
                    "price": "$20",
                    "potential_allergens": ["tree_nuts"],
                    "ingredients": ["chicken", "coconut milk", "eggplant", "bamboo shoots", "thai basil", "green curry paste"],
                    "section": "Curries",
                    "dietary_info": ["gluten-free", "dairy-free"]
                },
                {
                    "name": "Mango Sticky Rice",
                    "description": "Sweet sticky rice with fresh mango and coconut cream",
                    "price": "$8",
                    "potential_allergens": ["tree_nuts"],
                    "ingredients": ["sticky rice", "mango", "coconut cream", "sugar"],
                    "section": "Desserts",
                    "dietary_info": ["vegan", "gluten-free", "dairy-free"]
                }
            ],
            "total_items": 3,
            "allergen_summary": {
                "shellfish": 1,
                "soy": 1,
                "peanuts": 1,
                "fish": 1,
                "tree_nuts": 2
            }
        },
        {
            "restaurant_name": "Portillo's",
            "restaurant_url": "https://www.portillos.com",
            "cuisine_type": "American Fast Casual",
            "price_range": "$$",
            "menu_items": [
                {
                    "name": "Italian Beef Sandwich",
                    "description": "Thinly sliced beef with hot giardiniera on French bread",
                    "price": "$8",
                    "potential_allergens": ["wheat"],
                    "ingredients": ["beef", "giardiniera", "french bread", "beef jus"],
                    "section": "Sandwiches",
                    "dietary_info": ["dairy-free"]
                },
                {
                    "name": "Chocolate Cake Shake",
                    "description": "Vanilla ice cream blended with chocolate cake and whipped cream",
                    "price": "$6",
                    "potential_allergens": ["dairy", "eggs", "wheat"],
                    "ingredients": ["vanilla ice cream", "chocolate cake", "whipped cream", "milk"],
                    "section": "Desserts",
                    "dietary_info": ["vegetarian"]
                },
                {
                    "name": "Chopped Salad",
                    "description": "Mixed greens with salami, cheese, tomatoes, and Italian dressing",
                    "price": "$9",
                    "potential_allergens": ["dairy"],
                    "ingredients": ["mixed greens", "salami", "mozzarella", "tomatoes", "italian dressing"],
                    "section": "Salads",
                    "dietary_info": ["gluten-free"]
                }
            ],
            "total_items": 3,
            "allergen_summary": {
                "wheat": 2,
                "dairy": 2,
                "eggs": 1
            }
        }
    ]
    
    # Calculate overall statistics
    total_restaurants = len(health_menu_data)
    total_menu_items = sum(restaurant['total_items'] for restaurant in health_menu_data)
    
    # Aggregate allergen data
    all_allergens = {}
    dietary_options = {}
    
    for restaurant in health_menu_data:
        for allergen, count in restaurant['allergen_summary'].items():
            all_allergens[allergen] = all_allergens.get(allergen, 0) + count
        
        for item in restaurant['menu_items']:
            for dietary in item.get('dietary_info', []):
                dietary_options[dietary] = dietary_options.get(dietary, 0) + 1
    
    # Create summary report
    summary_report = {
        "extraction_date": "2024-01-15",
        "total_restaurants": total_restaurants,
        "total_menu_items": total_menu_items,
        "allergen_analysis": {
            "total_allergen_instances": sum(all_allergens.values()),
            "allergen_breakdown": all_allergens,
            "most_common_allergens": sorted(all_allergens.items(), key=lambda x: x[1], reverse=True)[:5]
        },
        "dietary_options": {
            "available_options": dietary_options,
            "most_common_dietary": sorted(dietary_options.items(), key=lambda x: x[1], reverse=True)[:3]
        },
        "cuisine_diversity": list(set(r['cuisine_type'] for r in health_menu_data)),
        "price_ranges": list(set(r['price_range'] for r in health_menu_data))
    }
    
    # Save the data
    output_file = "output/health_focused_menu_data.json"
    complete_data = {
        "summary": summary_report,
        "restaurants": health_menu_data
    }
    
    with open(output_file, "w") as f:
        json.dump(complete_data, f, indent=2)
    
    # Print detailed analysis
    print(f"=== COMPREHENSIVE MENU DATA CREATED ===")
    print(f"Restaurants: {total_restaurants}")
    print(f"Total menu items: {total_menu_items}")
    print(f"File saved: {output_file}")
    
    print(f"\n=== ALLERGEN ANALYSIS ===")
    for allergen, count in sorted(all_allergens.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_menu_items) * 100
        print(f"  {allergen.replace('_', ' ').title()}: {count} items ({percentage:.1f}%)")
    
    print(f"\n=== DIETARY OPTIONS ===")
    for dietary, count in sorted(dietary_options.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_menu_items) * 100
        print(f"  {dietary.replace('_', ' ').title()}: {count} items ({percentage:.1f}%)")
    
    print(f"\n=== SAMPLE MENU ITEMS FOR HEALTH APP ===")
    for restaurant in health_menu_data[:2]:
        print(f"\n{restaurant['restaurant_name']} ({restaurant['cuisine_type']})")
        for item in restaurant['menu_items'][:2]:
            allergens = ', '.join(item['potential_allergens']) if item['potential_allergens'] else 'None'
            dietary = ', '.join(item['dietary_info']) if item['dietary_info'] else 'None'
            print(f"  • {item['name']} - {item['price']}")
            print(f"    Allergens: {allergens}")
            print(f"    Dietary: {dietary}")
            print(f"    Ingredients: {', '.join(item['ingredients'][:4])}...")
    
    print(f"\n=== HEALTH APP INTEGRATION READY ===")
    print("This data structure provides:")
    print("✅ Detailed allergen identification")
    print("✅ Ingredient lists for analysis")
    print("✅ Dietary restriction compatibility")
    print("✅ Price and cuisine information")
    print("✅ Structured JSON for easy app integration")
    print("\nPerfect for building allergy-aware restaurant recommendation systems!")
    
    return complete_data

if __name__ == "__main__":
    create_health_focused_menu_data()