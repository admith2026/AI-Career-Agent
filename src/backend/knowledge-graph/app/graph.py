"""Neo4j graph operations — manages company/recruiter/role knowledge graph."""

import logging
from neo4j import AsyncGraphDatabase
from app.config import settings

logger = logging.getLogger(__name__)


class GraphManager:
    """Manages the knowledge graph of companies, recruiters, roles, and technologies."""

    def __init__(self):
        self._driver = None

    async def connect(self):
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        # Create constraints and indexes
        async with self._driver.session() as session:
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE")
            await session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Recruiter) REQUIRE r.email IS UNIQUE")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (t:Technology) ON (t.name)")
            await session.run("CREATE INDEX IF NOT EXISTS FOR (j:JobRole) ON (j.title)")
        logger.info("Neo4j knowledge graph connected")

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def upsert_company(self, name: str, properties: dict = None):
        """Create or update a company node."""
        props = properties or {}
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (c:Company {name: $name})
                SET c += $props, c.updated_at = datetime()
                """,
                name=name, props=props,
            )

    async def upsert_recruiter(self, email: str, name: str, company: str = None, properties: dict = None):
        """Create or update a recruiter and link to company."""
        props = properties or {}
        props["name"] = name
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (r:Recruiter {email: $email})
                SET r += $props, r.updated_at = datetime()
                """,
                email=email, props=props,
            )
            if company:
                await session.run(
                    """
                    MATCH (r:Recruiter {email: $email})
                    MERGE (c:Company {name: $company})
                    MERGE (r)-[:RECRUITS_FOR]->(c)
                    """,
                    email=email, company=company,
                )

    async def add_job_role(self, title: str, company: str, technologies: list[str] = None):
        """Add a job role node and link to company and technologies."""
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (c:Company {name: $company})
                MERGE (j:JobRole {title: $title, company: $company})
                MERGE (j)-[:AT_COMPANY]->(c)
                SET c.is_hiring = true, j.updated_at = datetime()
                """,
                title=title, company=company,
            )
            for tech in (technologies or []):
                await session.run(
                    """
                    MERGE (t:Technology {name: $tech})
                    MATCH (j:JobRole {title: $title, company: $company})
                    MERGE (j)-[:REQUIRES]->(t)
                    """,
                    tech=tech, title=title, company=company,
                )

    async def add_signal(self, company: str, signal_type: str, title: str, confidence: float = 0.5):
        """Link a hiring signal to a company."""
        async with self._driver.session() as session:
            await session.run(
                """
                MERGE (c:Company {name: $company})
                CREATE (s:HiringSignal {type: $signal_type, title: $title,
                    confidence: $confidence, detected_at: datetime()})
                MERGE (s)-[:SIGNALS]->(c)
                """,
                company=company, signal_type=signal_type,
                title=title, confidence=confidence,
            )

    async def get_company_network(self, company_name: str) -> dict:
        """Get the full knowledge graph around a company."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Company {name: $name})
                OPTIONAL MATCH (r:Recruiter)-[:RECRUITS_FOR]->(c)
                OPTIONAL MATCH (j:JobRole)-[:AT_COMPANY]->(c)
                OPTIONAL MATCH (j)-[:REQUIRES]->(t:Technology)
                OPTIONAL MATCH (s:HiringSignal)-[:SIGNALS]->(c)
                RETURN c,
                    collect(DISTINCT {name: r.name, email: r.email}) as recruiters,
                    collect(DISTINCT {title: j.title}) as roles,
                    collect(DISTINCT t.name) as technologies,
                    collect(DISTINCT {type: s.type, title: s.title, confidence: s.confidence}) as signals
                """,
                name=company_name,
            )
            record = await result.single()
            if not record:
                return {"error": "Company not found"}

            return {
                "company": dict(record["c"]),
                "recruiters": [r for r in record["recruiters"] if r.get("name")],
                "roles": [r for r in record["roles"] if r.get("title")],
                "technologies": [t for t in record["technologies"] if t],
                "signals": [s for s in record["signals"] if s.get("type")],
            }

    async def find_decision_makers(self, company_name: str) -> list[dict]:
        """Find recruiters and hiring managers for a company."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (r:Recruiter)-[:RECRUITS_FOR]->(c:Company {name: $name})
                RETURN r.name as name, r.email as email,
                       r.linkedin_url as linkedin, r.title as title
                ORDER BY r.updated_at DESC
                LIMIT 20
                """,
                name=company_name,
            )
            return [dict(record) async for record in result]

    async def get_hiring_hotspots(self, limit: int = 20) -> list[dict]:
        """Find companies with the most hiring signals."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (s:HiringSignal)-[:SIGNALS]->(c:Company)
                WITH c, count(s) as signal_count, collect(s.type) as signal_types,
                     max(s.confidence) as max_confidence
                RETURN c.name as company, signal_count, signal_types, max_confidence
                ORDER BY signal_count DESC, max_confidence DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            return [dict(record) async for record in result]

    async def get_technology_demand(self, limit: int = 20) -> list[dict]:
        """Get most in-demand technologies."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (j:JobRole)-[:REQUIRES]->(t:Technology)
                WITH t.name as technology, count(j) as demand
                RETURN technology, demand
                ORDER BY demand DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            return [dict(record) async for record in result]

    async def get_graph_stats(self) -> dict:
        """Get overview statistics of the knowledge graph."""
        async with self._driver.session() as session:
            stats = {}
            for label in ["Company", "Recruiter", "JobRole", "Technology", "HiringSignal"]:
                result = await session.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
                record = await result.single()
                stats[label.lower() + "_count"] = record["cnt"] if record else 0

            result = await session.run("MATCH ()-[r]->() RETURN count(r) as cnt")
            record = await result.single()
            stats["total_relationships"] = record["cnt"] if record else 0
            return stats

    # ─── Recruiter Intelligence ──────────────────────────────────────────────

    async def track_interaction(self, recruiter_email: str, interaction_type: str,
                                sentiment: float = 0.5, notes: str = ""):
        """Track an interaction with a recruiter and update relationship strength."""
        async with self._driver.session() as session:
            await session.run(
                """
                MATCH (r:Recruiter {email: $email})
                CREATE (i:Interaction {type: $type, sentiment: $sentiment,
                    notes: $notes, timestamp: datetime()})
                MERGE (r)-[:HAD_INTERACTION]->(i)
                WITH r
                OPTIONAL MATCH (r)-[:HAD_INTERACTION]->(all_i:Interaction)
                WITH r, count(all_i) as total, avg(all_i.sentiment) as avg_sent
                SET r.interaction_count = total,
                    r.avg_sentiment = avg_sent,
                    r.relationship_score = CASE
                        WHEN total >= 5 AND avg_sent > 0.7 THEN 'strong'
                        WHEN total >= 2 AND avg_sent > 0.4 THEN 'warm'
                        ELSE 'cold'
                    END,
                    r.last_interaction = datetime()
                """,
                email=recruiter_email, type=interaction_type,
                sentiment=sentiment, notes=notes,
            )

    async def get_recruiter_rankings(self, limit: int = 20) -> list[dict]:
        """Rank recruiters by relationship strength and hiring activity."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (r:Recruiter)
                OPTIONAL MATCH (r)-[:RECRUITS_FOR]->(c:Company)
                OPTIONAL MATCH (r)-[:HAD_INTERACTION]->(i:Interaction)
                WITH r, collect(DISTINCT c.name) as companies,
                     count(i) as interactions,
                     avg(i.sentiment) as avg_sentiment
                RETURN r.name as name, r.email as email,
                       r.relationship_score as strength,
                       companies, interactions,
                       round(coalesce(avg_sentiment, 0) * 100) / 100.0 as sentiment,
                       r.last_interaction as last_contact
                ORDER BY interactions DESC, avg_sentiment DESC
                LIMIT $limit
                """,
                limit=limit,
            )
            return [dict(record) async for record in result]

    async def get_company_recruiter_map(self, company_name: str) -> list[dict]:
        """Get all recruiters for a company with relationship strength."""
        async with self._driver.session() as session:
            result = await session.run(
                """
                MATCH (r:Recruiter)-[:RECRUITS_FOR]->(c:Company {name: $name})
                OPTIONAL MATCH (r)-[:HAD_INTERACTION]->(i:Interaction)
                WITH r, count(i) as interactions, avg(i.sentiment) as sentiment
                RETURN r.name as name, r.email as email, r.title as title,
                       r.linkedin_url as linkedin,
                       coalesce(r.relationship_score, 'cold') as strength,
                       interactions, round(coalesce(sentiment, 0) * 100) / 100.0 as sentiment
                ORDER BY interactions DESC
                """,
                name=company_name,
            )
            return [dict(record) async for record in result]
