import json

import httpx
from sqlalchemy.orm import Session

from app.db.models import LeadSnapshot, WebhookDelivery, WebhookTarget
from app.schemas.webhook import WebhookTargetCreate


def create_webhook_target(db: Session, payload: WebhookTargetCreate) -> WebhookTarget:
    data = payload.model_dump(mode='python')
    data['target_url'] = str(data['target_url'])
    target = WebhookTarget(**data)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def list_webhook_targets(db: Session, active_only: bool = False) -> list[WebhookTarget]:
    query = db.query(WebhookTarget).order_by(WebhookTarget.created_at.desc())
    if active_only:
        query = query.filter(WebhookTarget.active.is_(True))
    return query.all()


def list_webhook_deliveries(db: Session, target_id: int) -> list[WebhookDelivery]:
    return db.query(WebhookDelivery).filter(WebhookDelivery.webhook_target_id == target_id).order_by(WebhookDelivery.created_at.desc()).all()


def _target_accepts_snapshot(target: WebhookTarget, snapshot: LeadSnapshot) -> bool:
    tier_set = {tier.strip() for tier in target.lead_tiers.split(',') if tier.strip()}
    return snapshot.score >= target.min_score and snapshot.lead_tier in tier_set


def deliver_lead_snapshot(db: Session, target: WebhookTarget, snapshot: LeadSnapshot) -> WebhookDelivery:
    if not snapshot.executive_payload:
        raise ValueError('Lead snapshot sem payload executivo')

    payload = json.loads(snapshot.executive_payload)
    if not _target_accepts_snapshot(target, snapshot):
        delivery = WebhookDelivery(
            webhook_target_id=target.id,
            company_id=snapshot.company_id,
            status='skipped',
            response_body='Lead fora do critério do target',
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery

    body = {
        'target': target.name,
        'lead': payload,
        'snapshot': {
            'score': snapshot.score,
            'lead_tier': snapshot.lead_tier,
            'conversion_probability': snapshot.conversion_probability,
        },
    }

    try:
        response = httpx.post(target.target_url, json=body, timeout=20.0)
        delivery = WebhookDelivery(
            webhook_target_id=target.id,
            company_id=snapshot.company_id,
            status='success' if response.status_code < 400 else 'error',
            response_status=response.status_code,
            response_body=response.text[:2000],
        )
    except Exception as exc:
        delivery = WebhookDelivery(
            webhook_target_id=target.id,
            company_id=snapshot.company_id,
            status='error',
            response_body=str(exc),
        )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def dispatch_latest_leads(db: Session, target: WebhookTarget, limit: int = 20) -> list[WebhookDelivery]:
    snapshots = db.query(LeadSnapshot).order_by(LeadSnapshot.created_at.desc()).limit(limit).all()
    deliveries = []
    seen_company_ids = set()
    for snapshot in snapshots:
        if snapshot.company_id in seen_company_ids:
            continue
        seen_company_ids.add(snapshot.company_id)
        deliveries.append(deliver_lead_snapshot(db, target, snapshot))
    return deliveries


def dispatch_snapshot_to_eligible_targets(db: Session, snapshot: LeadSnapshot) -> list[WebhookDelivery]:
    targets = db.query(WebhookTarget).filter(WebhookTarget.active.is_(True)).order_by(WebhookTarget.created_at.asc()).all()
    deliveries: list[WebhookDelivery] = []
    for target in targets:
        if _target_accepts_snapshot(target, snapshot):
            deliveries.append(deliver_lead_snapshot(db, target, snapshot))
    return deliveries
