import sys
import os

# Add project root to python path
sys.path.append(os.getcwd())

from agent_gourmet.main import a2a_app as gourmet_app
from agent_acadomie.main import a2a_app as acadomie_app
from agent_explorer.main import a2a_app as explorer_app
from common.config import config


def verify_agent_config():
    print("🚀 Verifying agent configurations...")

    # Check Gourmet
    print(f"🍳 Gourmet URL: {config.GOURMET_URL}")
    assert gourmet_app.agent_card.url == config.GOURMET_URL
    print("✅ Gourmet initialized correctly")

    # Check Acadomie
    print(f"📚 Acadomie URL: {config.ACADOMIE_URL}")
    assert acadomie_app.agent_card.url == config.ACADOMIE_URL
    print("✅ Acadomie initialized correctly")

    # Check Explorer
    print(f"🌍 Explorer URL: {config.EXPLORER_URL}")
    assert explorer_app.agent_card.url == config.EXPLORER_URL
    print("✅ Explorer initialized correctly")

    print("\n✨ All agents initialized successfully with config URLs!")


if __name__ == "__main__":
    verify_agent_config()
