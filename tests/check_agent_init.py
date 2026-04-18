import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from agent_gourmet.main import a2a_app as gourmet_app
from agent_acadomie.main import a2a_app as acadomie_app
from agent_explorer.main import a2a_app as explorer_app
from common.config import config
from common.agent_registry import agent_registry


def verify_agent_config():
    print("🚀 Verifying agent configurations...")

    # Check Gourmet
    gourmet_url = agent_registry.get_agent_url("gourmet")
    print(f"🍳 Gourmet URL: {gourmet_url}")
    assert gourmet_app.agent_card.url == gourmet_url
    print("✅ Gourmet initialized correctly")

    # Check Acadomie
    acadomie_url = agent_registry.get_agent_url("acadomie")
    print(f"📚 Acadomie URL: {acadomie_url}")
    assert acadomie_app.agent_card.url == acadomie_url
    print("✅ Acadomie initialized correctly")

    # Check Explorer
    explorer_url = agent_registry.get_agent_url("explorer")
    print(f"🌍 Explorer URL: {explorer_url}")
    assert explorer_app.agent_card.url == explorer_url
    print("✅ Explorer initialized correctly")

    print("\n✨ All agents initialized successfully with config URLs!")


if __name__ == "__main__":
    verify_agent_config()
