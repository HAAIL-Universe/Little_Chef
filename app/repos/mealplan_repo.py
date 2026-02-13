from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.db.conn import connect, get_database_url
from app.repos.user_repo import ensure_user
from app.schemas import MealPlanResponse


class MealPlanRepository:
    """
    In-memory confirmed meal plan store (per user).
    """

    def __init__(self) -> None:
        self._plans_by_user: Dict[str, List[dict]] = {}

    def save_plan(
        self,
        user_id: str,
        thread_id: str,
        proposal_id: str,
        plan: MealPlanResponse,
    ) -> MealPlanResponse:
        bucket = self._plans_by_user.setdefault(user_id, [])
        record = {
            "plan_id": plan.plan_id,
            "thread_id": thread_id,
            "proposal_id": proposal_id,
            "plan": plan.model_dump(mode="json"),
            "plan_created_at": plan.created_at,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        }
        replaced = False
        for idx, existing in enumerate(bucket):
            if existing.get("plan_id") == plan.plan_id:
                bucket[idx] = record
                replaced = True
                break
        if not replaced:
            bucket.append(record)
        return plan

    def get_latest_plan(self, user_id: str) -> Optional[MealPlanResponse]:
        bucket = self._plans_by_user.get(user_id, [])
        if not bucket:
            return None
        latest = max(bucket, key=lambda item: item.get("confirmed_at", ""))
        payload = latest.get("plan")
        if not payload:
            return None
        return MealPlanResponse.model_validate(payload)

    def clear(self) -> None:
        self._plans_by_user.clear()


class DbMealPlanRepository:
    def save_plan(
        self,
        user_id: str,
        provider_subject: str,
        email: str | None,
        thread_id: str,
        proposal_id: str,
        plan: MealPlanResponse,
    ) -> MealPlanResponse:
        plan_payload = plan.model_dump(mode="json")
        plan_created_at = plan.created_at or datetime.now(timezone.utc).isoformat()
        with connect() as conn, conn.cursor() as cur:
            ensure_user(cur, user_id, provider_subject, email)
            cur.execute(
                """
                INSERT INTO meal_plans (
                    plan_id, user_id, thread_id, proposal_id, plan, plan_created_at, confirmed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, now())
                ON CONFLICT (plan_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    thread_id = EXCLUDED.thread_id,
                    proposal_id = EXCLUDED.proposal_id,
                    plan = EXCLUDED.plan,
                    plan_created_at = EXCLUDED.plan_created_at,
                    confirmed_at = now()
                """,
                (
                    plan.plan_id,
                    user_id,
                    thread_id,
                    proposal_id,
                    json.dumps(plan_payload),
                    plan_created_at,
                ),
            )
            conn.commit()
        return plan

    def get_latest_plan(self, user_id: str) -> Optional[MealPlanResponse]:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT plan
                FROM meal_plans
                WHERE user_id = %s
                ORDER BY confirmed_at DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return MealPlanResponse.model_validate(payload)


def get_mealplan_repository():
    if get_database_url():
        return DbMealPlanRepository()
    return MealPlanRepository()
