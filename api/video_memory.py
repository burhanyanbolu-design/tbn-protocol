"""
TBN Video Agent — Knowledge Memory
====================================
Every video the agent watches gets stored as learned knowledge.
The agent builds up understanding over time — like a brain that never forgets.

Entity types it learns:
  - PEOPLE:        Individuals, influencers, speakers, founders, experts
  - COMPANIES:     Businesses, startups, corporations, brands
  - BRANDS:        Products, services, platforms
  - ORGANISATIONS: Universities, governments, NGOs, institutions
  - PODCASTS:      Shows, channels, series, podcasters
  - TOPICS:        Subjects, fields, industries, concepts
  - LOCATIONS:     Cities, countries, venues, offices
  - PRODUCTS:      Software, hardware, tools, frameworks

Feed it 50 videos about a topic → it becomes an expert.
Ask "What does Burhan Yanbolu do?" → pulls from ALL videos it's watched.
Ask "What companies are in AI governance?" → synthesises from everything.
Ask "What did Lex Fridman say about AI safety?" → finds it.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-VM-7d3e1f9a
"""

import os
import json
import hashlib
import uuid
import re
from datetime import datetime, timezone

MEMORY_FILE = "data/video_memory.json"
ENTITIES_FILE = "data/video_entities.json"
KNOWLEDGE_FILE = "data/video_knowledge.json"


def _load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def _save_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── Entity Types ──────────────────────────────────────────────────────
ENTITY_TYPES = [
    "person", "company", "brand", "organisation",
    "podcast", "topic", "location", "product",
    "university", "influencer", "channel",
]


def store_video_knowledge(video_hash, source, mode, understanding, receipt,
                          duration=None, file_size=None, entities_extracted=None):
    """
    Store everything learned from a video into the knowledge memory.
    Called after every successful video analysis.
    
    entities_extracted: optional dict from Gemini with structured entity data
    """
    memory = _load_json(MEMORY_FILE)
    entities = _load_json(ENTITIES_FILE)
    knowledge = _load_json(KNOWLEDGE_FILE)

    now = datetime.now(timezone.utc).isoformat()
    memory_id = f"mem_{uuid.uuid4().hex[:12]}"

    # Extract knowledge from understanding
    summary = understanding.get("summary", "")
    transcript = understanding.get("transcript_summary", "")
    events = understanding.get("events", [])
    objects = understanding.get("objects", [])
    context = understanding.get("context", "")
    confidence = understanding.get("confidence", 0)
    authenticity = understanding.get("authenticity", {})

    # ── Build memory entry ────────────────────────────────────────────
    entry = {
        "memory_id": memory_id,
        "video_hash": video_hash,
        "source": source,
        "mode": mode,
        "timestamp": now,
        "duration_seconds": duration,
        "file_size_mb": file_size,
        "summary": summary,
        "transcript": transcript,
        "events": events,
        "objects": objects,
        "context": context,
        "confidence": confidence,
        "authenticity": authenticity,
        "receipt_id": receipt.get("receipt_id", ""),
        "risk_score": receipt.get("risk_score", 0),
    }

    # Store by video hash (dedup — same video won't be stored twice per mode)
    store_key = f"{video_hash}_{mode}"
    memory[store_key] = entry
    _save_json(MEMORY_FILE, memory)

    # ── Process entities from Gemini extraction ───────────────────────
    if entities_extracted:
        _store_entities(entities, entities_extracted, source, now, memory_id, summary, transcript)
    else:
        # Fallback: basic extraction from text
        _extract_entities_basic(entities, summary, transcript, events, context, source, now, memory_id)

    _save_json(ENTITIES_FILE, entities)

    # ── Store knowledge claims ────────────────────────────────────────
    _store_knowledge_claims(knowledge, summary, transcript, events, source, now, memory_id)
    _save_json(KNOWLEDGE_FILE, knowledge)

    return memory_id


def _store_entities(entities, extracted, source, timestamp, memory_id, summary, transcript):
    """Store structured entities from Gemini's extraction."""
    all_text = f"{summary} {transcript}"

    for entity_type, entity_list in extracted.items():
        if entity_type not in ENTITY_TYPES:
            continue
        if not isinstance(entity_list, list):
            continue

        for item in entity_list:
            if isinstance(item, str):
                name = item.strip()
                description = ""
            elif isinstance(item, dict):
                name = item.get("name", "").strip()
                description = item.get("description", "")
            else:
                continue

            if not name or len(name) < 2:
                continue

            entity_key = f"{entity_type}:{name.lower().replace(' ', '_')}"

            if entity_key not in entities:
                entities[entity_key] = {
                    "name": name,
                    "type": entity_type,
                    "first_seen": timestamp,
                    "mentions": 0,
                    "facts": [],
                    "sources": [],
                    "memory_ids": [],
                    "description": description,
                    "related_entities": [],
                }

            ent = entities[entity_key]
            ent["mentions"] += 1
            ent["last_seen"] = timestamp

            if source not in ent["sources"]:
                ent["sources"].append(source)
            if memory_id not in ent["memory_ids"]:
                ent["memory_ids"].append(memory_id)

            if description and description not in ent["facts"]:
                ent["facts"].append(description)

            # Extract sentences mentioning this entity
            sentences = re.split(r'[.!?]', all_text)
            for sentence in sentences:
                if name.lower() in sentence.lower():
                    fact = sentence.strip()
                    if fact and len(fact) > 10 and fact not in ent["facts"]:
                        ent["facts"].append(fact)
                        if len(ent["facts"]) > 100:
                            ent["facts"] = ent["facts"][-100:]


def _extract_entities_basic(entities, summary, transcript, events, context, source, timestamp, memory_id):
    """Fallback: extract entities using regex patterns when Gemini extraction isn't available."""
    all_text = f"{summary} {transcript} {' '.join(events)} {context}"

    # Find capitalised multi-word names (likely people, companies, brands)
    name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    found_names = re.findall(name_pattern, all_text)

    # Single capitalised words that might be brands/companies
    single_pattern = r'\b([A-Z][a-z]{2,})\b'
    single_names = re.findall(single_pattern, all_text)

    skip_words = {
        "The", "This", "That", "These", "Those", "There", "Here",
        "What", "When", "Where", "Which", "Who", "How", "Why",
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
        "None", "True", "False", "Yes", "No", "Not", "Also", "However",
        "Furthermore", "Additionally", "Moreover", "Therefore", "Meanwhile",
    }

    all_names = set(found_names) | set(n for n in single_names if n not in skip_words)

    for name in all_names:
        if name in skip_words or len(name) < 3:
            continue

        # Guess entity type
        entity_type = "person"  # Default
        name_lower = name.lower()
        if any(w in name_lower for w in ["university", "college", "institute", "school"]):
            entity_type = "university"
        elif any(w in name_lower for w in ["inc", "ltd", "corp", "llc", "group", "solutions"]):
            entity_type = "company"
        elif any(w in name_lower for w in ["podcast", "show", "cast"]):
            entity_type = "podcast"

        entity_key = f"{entity_type}:{name.lower().replace(' ', '_')}"

        if entity_key not in entities:
            entities[entity_key] = {
                "name": name,
                "type": entity_type,
                "first_seen": timestamp,
                "mentions": 0,
                "facts": [],
                "sources": [],
                "memory_ids": [],
                "description": "",
                "related_entities": [],
            }

        ent = entities[entity_key]
        ent["mentions"] += 1
        ent["last_seen"] = timestamp

        if source not in ent["sources"]:
            ent["sources"].append(source)
        if memory_id not in ent["memory_ids"]:
            ent["memory_ids"].append(memory_id)

        # Extract facts
        sentences = re.split(r'[.!?]', all_text)
        for sentence in sentences:
            if name in sentence:
                fact = sentence.strip()
                if fact and len(fact) > 10 and fact not in ent["facts"]:
                    ent["facts"].append(fact)
                    if len(ent["facts"]) > 100:
                        ent["facts"] = ent["facts"][-100:]


def _store_knowledge_claims(knowledge, summary, transcript, events, source, timestamp, memory_id):
    """Store individual knowledge claims (facts) for retrieval."""
    all_text = f"{summary} {transcript}"
    sentences = re.split(r'[.!?]', all_text)

    for sentence in sentences:
        fact = sentence.strip()
        if not fact or len(fact) < 15:
            continue

        # Hash the fact for dedup
        fact_hash = hashlib.md5(fact.lower().encode()).hexdigest()[:12]

        if fact_hash not in knowledge:
            knowledge[fact_hash] = {
                "fact": fact,
                "source": source,
                "memory_id": memory_id,
                "timestamp": timestamp,
                "confidence": 1,
            }
        else:
            # Same fact from multiple sources = higher confidence
            knowledge[fact_hash]["confidence"] += 1
            knowledge[fact_hash]["last_confirmed"] = timestamp


def query_memory(question):
    """
    Query the video memory with a natural language question.
    Returns all relevant knowledge the agent has learned.
    """
    memory = _load_json(MEMORY_FILE)
    entities = _load_json(ENTITIES_FILE)
    knowledge = _load_json(KNOWLEDGE_FILE)

    question_lower = question.lower()
    results = {
        "question": question,
        "entities_found": [],
        "memories_found": [],
        "knowledge_claims": [],
        "total_videos_watched": len(memory),
        "total_entities_known": len(entities),
        "total_facts_stored": len(knowledge),
    }

    # ── Search entities ───────────────────────────────────────────────
    for key, entity in entities.items():
        name_lower = entity["name"].lower()
        if name_lower in question_lower or any(
            word in question_lower for word in name_lower.split() if len(word) > 3
        ):
            results["entities_found"].append(entity)

    # Sort by mentions (most referenced first)
    results["entities_found"].sort(key=lambda x: x.get("mentions", 0), reverse=True)

    # ── Search memories (full text) ───────────────────────────────────
    search_terms = [t for t in question_lower.split() if len(t) > 2]
    for store_key, entry in memory.items():
        text_blob = f"{entry.get('summary', '')} {entry.get('transcript', '')} {' '.join(entry.get('events', []))}".lower()
        matches = sum(1 for term in search_terms if term in text_blob)
        if matches >= max(1, len(search_terms) // 3):
            results["memories_found"].append({
                "memory_id": entry.get("memory_id"),
                "source": entry.get("source"),
                "summary": entry.get("summary"),
                "transcript": entry.get("transcript"),
                "timestamp": entry.get("timestamp"),
                "relevance": matches / len(search_terms) if search_terms else 0,
            })

    # Sort by relevance
    results["memories_found"].sort(key=lambda x: x.get("relevance", 0), reverse=True)
    results["memories_found"] = results["memories_found"][:10]

    # ── Search knowledge claims ───────────────────────────────────────
    for fact_hash, claim in knowledge.items():
        fact_lower = claim["fact"].lower()
        if any(term in fact_lower for term in search_terms if len(term) > 3):
            results["knowledge_claims"].append(claim)

    # Sort by confidence (multi-source facts first)
    results["knowledge_claims"].sort(key=lambda x: x.get("confidence", 0), reverse=True)
    results["knowledge_claims"] = results["knowledge_claims"][:20]

    return results


def get_memory_stats():
    """Return stats about what the agent has learned."""
    memory = _load_json(MEMORY_FILE)
    entities = _load_json(ENTITIES_FILE)
    knowledge = _load_json(KNOWLEDGE_FILE)

    # Group entities by type
    by_type = {}
    for key, ent in entities.items():
        etype = ent.get("type", "unknown")
        if etype not in by_type:
            by_type[etype] = []
        by_type[etype].append({"name": ent["name"], "mentions": ent["mentions"]})

    # Sort each type by mentions
    for etype in by_type:
        by_type[etype].sort(key=lambda x: x["mentions"], reverse=True)
        by_type[etype] = by_type[etype][:10]  # Top 10 per type

    return {
        "total_videos_watched": len(memory),
        "total_entities_known": len(entities),
        "total_facts_stored": len(knowledge),
        "entities_by_type": by_type,
        "entity_type_counts": {
            etype: sum(1 for e in entities.values() if e.get("type") == etype)
            for etype in ENTITY_TYPES
        },
    }


def get_entity(entity_type, name):
    """Get everything known about a specific entity."""
    entities = _load_json(ENTITIES_FILE)

    # Try exact match
    entity_key = f"{entity_type}:{name.lower().replace(' ', '_')}"
    if entity_key in entities:
        return entities[entity_key]

    # Try partial match across all types
    name_lower = name.lower()
    for key, ent in entities.items():
        if name_lower in ent["name"].lower() or name_lower in key:
            return ent

    return None


def get_all_entities(entity_type=None):
    """Get all entities, optionally filtered by type."""
    entities = _load_json(ENTITIES_FILE)

    if entity_type:
        return {k: v for k, v in entities.items() if v.get("type") == entity_type}
    return entities
