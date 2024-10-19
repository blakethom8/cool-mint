from database.pgvector import VectorStore


vec = VectorStore()

vec.semantic_search("What's the working from home policy?")
vec.keyword_search("Policy")
