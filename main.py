from fastapi import FastAPI, Query
from anicli_api.source.animego import Extractor
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = Extractor()


# =========================
# 🔒 WATCH v1 — НЕ ТРОГАЕМ
# =========================
@app.get("/watch")
def watch(title: str = Query(...)):
    results = extractor.search(title)
    if not results:
        return {"error": "Anime not found"}

    anime = results[0].get_anime()
    episodes = list(anime.get_episodes())
    if not episodes:
        return {"error": "No episodes"}

    episode = episodes[0]
    sources = list(episode.get_sources())
    if not sources:
        return {"error": "No sources"}

    for source in sources:
        if getattr(source, "url", None):
            return {
                "title": anime.title,
                "embedUrl": source.url
            }

    return {"error": "No iframe source found"}


# =========================
# 🎥 WATCH SOURCES — ВЫБОР ПЛЕЕРА
# =========================

def detect_player(source):
    url = source.url.lower()

    if "animego" in url:
        return {"id": "animego", "name": "AnimeGo", "priority": 3}
    if "kodik" in url:
        return {"id": "kodik", "name": "Kodik", "priority": 2}
    if "aniboom" in url:
        return {"id": "aniboom", "name": "AniBoom", "priority": 1}

    return {"id": "unknown", "name": "Unknown", "priority": 0}


@app.get("/watch/sources")
def watch_sources(
    title: str = Query(...),
    episode: int = Query(1)
):
    results = extractor.search(title)
    if not results:
        return {"error": "Anime not found"}

    anime = results[0].get_anime()
    episodes = list(anime.get_episodes())
    total = len(episodes)

    if episode < 1 or episode > total:
        episode = 1

    episode_numbers = list(range(1, total + 1))
    current_episode = episodes[episode - 1]
    sources = list(current_episode.get_sources())

    players = []

    for source in sources:
        if not getattr(source, "url", None):
            continue

        info = detect_player(source)

        players.append({
            "id": info["id"],
            "name": info["name"],
            "priority": info["priority"],
            "embedUrl": source.url
        })

    # 🔥 САМЫЙ ПОПУЛЯРНЫЙ — ПЕРВЫЙ
    players.sort(key=lambda p: p["priority"], reverse=True)

    return {
        "title": anime.title,
        "episode": episode,
        "episodes": episode_numbers,
        "players": players
    }

@app.get("/health")
def health():
    return {"status": "ok"}
