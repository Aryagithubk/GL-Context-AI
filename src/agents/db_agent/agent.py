"""
DBAgent — Natural Language to SQL agent.
Converts user questions into SQL, executes against a database (SQLite for demo),
and interprets the results using the LLM.
"""

import time
import sqlite3
import re
from typing import Any, Dict, List
from src.agents.base_agent import BaseAgent, AgentContext, AgentResponse, AgentStatus
from src.utils.logger import setup_logger

logger = setup_logger("DBAgent")


class DBAgent(BaseAgent):
    """Agent that converts natural language to SQL and queries databases"""

    def __init__(self, config: Dict[str, Any], llm_provider: Any):
        super().__init__(config, llm_provider)
        self._name = "DBAgent"
        self.db_path = config.get("db_path", "./data/demo.db")
        self.schema_info = ""

    @property
    def description(self) -> str:
        return "Converts natural language questions into SQL queries and retrieves data from databases."

    @property
    def supported_intents(self) -> List[str]:
        return ["data_query", "analytics", "reporting", "database"]

    async def initialize(self) -> None:
        """Connect to DB and introspect schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Introspect schema
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()

            schema_parts = []
            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                col_defs = ", ".join([f"{c[1]} ({c[2]})" for c in columns])
                schema_parts.append(f"Table '{table_name}': columns = [{col_defs}]")

                # Get sample rows
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample = cursor.fetchall()
                if sample:
                    col_names = [c[1] for c in columns]
                    sample_rows = [dict(zip(col_names, row)) for row in sample]
                    schema_parts.append(f"  Sample rows: {sample_rows}")

            conn.close()
            self.schema_info = "\n".join(schema_parts)

            if not tables:
                self._status = AgentStatus.ERROR
                logger.warning("DBAgent: No tables found in database.")
            else:
                self._status = AgentStatus.READY
                logger.info(f"DBAgent initialized — found {len(tables)} table(s).")

        except Exception as e:
            self._status = AgentStatus.ERROR
            logger.error(f"DBAgent init failed: {e}")

    async def can_handle(self, context: AgentContext) -> float:
        """Confidence scoring based on DB-related keywords"""
        if self._status != AgentStatus.READY:
            return 0.0

        score = 0.3
        query_lower = context.query.lower()

        db_keywords = [
            "employee", "employees", "salary", "database", "table",
            "count", "how many", "list all", "average", "total",
            "department", "departments", "record", "data", "query",
            "highest", "lowest", "maximum", "minimum", "sum",
        ]
        matches = sum(1 for kw in db_keywords if kw in query_lower)
        if matches >= 2:
            score += 0.4
        elif matches == 1:
            score += 0.2

        if context.intent in ["data_query", "analytics", "reporting", "database"]:
            score += 0.2

        return min(score, 1.0)

    async def execute(self, context: AgentContext) -> AgentResponse:
        """Generate SQL, execute, and interpret results"""
        start = time.time()

        try:
            # Step 1: Generate SQL from natural language
            nl_to_sql_prompt = (
                f"You are a SQL expert. Given the following database schema, "
                f"generate a SQLite SQL query to answer the user's question.\n\n"
                f"DATABASE SCHEMA:\n{self.schema_info}\n\n"
                f"USER QUESTION: {context.query}\n\n"
                f"RULES:\n"
                f"- Return ONLY the SQL query, no explanation\n"
                f"- Use only SELECT statements (read-only)\n"
                f"- Do not use DROP, DELETE, INSERT, UPDATE, ALTER, or CREATE\n"
                f"- Use correct table and column names from the schema\n"
                f"- Wrap the SQL in ```sql ... ``` tags\n\n"
                f"SQL:"
            )

            sql_response = await self.llm.generate(nl_to_sql_prompt)
            sql_query = self._extract_sql(sql_response.text)

            if not sql_query:
                return AgentResponse(
                    success=False,
                    error="Could not generate a valid SQL query.",
                    execution_time_ms=(time.time() - start) * 1000,
                )

            # Step 2: Validate — only allow SELECT
            if not self._is_safe_query(sql_query):
                return AgentResponse(
                    success=False,
                    error="Query rejected: only SELECT queries are allowed.",
                    execution_time_ms=(time.time() - start) * 1000,
                )

            # Step 3: Execute
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            conn.close()

            # Step 4: Interpret results with LLM
            results_text = f"Columns: {columns}\nRows ({len(rows)} results):\n"
            for row in rows[:20]:  # Limit to 20 rows in LLM context
                row_dict = dict(zip(columns, row))
                results_text += f"  {row_dict}\n"

            interpret_prompt = (
                f"The user asked: \"{context.query}\"\n\n"
                f"The following SQL was executed:\n```sql\n{sql_query}\n```\n\n"
                f"Results:\n{results_text}\n\n"
                f"Provide a clear, natural language summary of the results. "
                f"Be concise and directly answer the user's question."
            )

            interpretation = await self.llm.generate(interpret_prompt)

            return AgentResponse(
                success=True,
                answer=interpretation.text,
                confidence=0.85,
                sources=[{
                    "agent_name": self.name,
                    "source_type": "database",
                    "source_identifier": self.db_path,
                    "relevance_score": 0.85,
                    "excerpt": f"SQL: {sql_query} → {len(rows)} row(s)",
                }],
                raw_data={"sql": sql_query, "columns": columns, "rows": rows[:50]},
                execution_time_ms=(time.time() - start) * 1000,
            )

        except sqlite3.Error as e:
            logger.error(f"DBAgent SQL error: {e}")
            return AgentResponse(
                success=False,
                error=f"Database error: {str(e)}",
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error(f"DBAgent execution error: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )

    def _extract_sql(self, text: str) -> str:
        """Extract SQL from LLM response (may be wrapped in markdown)"""
        # Try to find SQL in code block
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try generic code block
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try to find a SELECT statement directly
        match = re.search(r"(SELECT\b.*?;)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Last resort: just use the whole text if it looks like SQL
        stripped = text.strip().rstrip(";") + ";"
        if stripped.upper().startswith("SELECT"):
            return stripped

        return ""

    def _is_safe_query(self, sql: str) -> bool:
        """Only allow SELECT statements"""
        normalized = sql.strip().upper()
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "EXEC"]
        for keyword in dangerous:
            if keyword in normalized:
                return False
        return normalized.startswith("SELECT")
