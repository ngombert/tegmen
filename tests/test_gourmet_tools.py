"""Verification script for Agent Gourmet tools."""

from agent_gourmet.tools import search_recipes, get_recipe_details
from agent_gourmet.agent import agent

def verify_tools():
    print("🍳 Testing search_recipes tool...")
    # Test 1: Search all
    results = search_recipes("recette")
    print(f"   Input 'recette' -> Found {len(results)} recipes")
    
    # Test 2: Search specific
    results = search_recipes("carbonara")
    if len(results) == 1 and results[0]["name"] == "Pâtes Carbonara":
        print("   ✅ Search 'carbonara' passed")
    else:
        print("   ❌ Search 'carbonara' failed")

    # Test 3: Search with tag only
    results = search_recipes("", tag="végétarien")
    if len(results) >= 1 and results[0]["name"] == "Ratatouille":
        print("   ✅ Search tag 'végétarien' passed")
    else:
        print(f"   ❌ Search tag 'végétarien' failed (Found {len(results)})")

    print("\n📝 Testing get_recipe_details tool...")
    details = get_recipe_details("1")
    if details["name"] == "Pâtes Carbonara":
        print("   ✅ Get details id='1' passed")
    else:
        print("   ❌ Get details id='1' failed")

    print("\n🤖 Checking Agent Configuration...")
    if len(agent.tools) == 2:
        print(f"   ✅ Agent has {len(agent.tools)} tools registered")
    else:
        print(f"   ❌ Agent has {len(agent.tools)} tools (expected 2)")
        
    print("\n✨ Gourmet Tools Verification Complete!")

if __name__ == "__main__":
    verify_tools()
