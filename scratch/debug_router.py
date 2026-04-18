from semantic_router.encoders import HuggingFaceEncoder
from semantic_router import Route
from semantic_router.routers import SemanticRouter

encoder = HuggingFaceEncoder(name="sentence-transformers/all-MiniLM-L6-v2")
chitchat_route = Route(name="chitchat", utterances=["Bonjour", "Salut"])
router = SemanticRouter(encoder=encoder, routes=[chitchat_route], auto_sync="local")

print(f"Index ready: {router.index.is_ready()}")
res = router("Bonjour")
print(f"Result for 'Bonjour': {res.name}")
print(f"Attributes of res: {dir(res)}")
if hasattr(res, 'score'):
    print(f"Score: {res.score}")
