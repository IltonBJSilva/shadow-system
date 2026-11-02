from flask import flash, redirect, render_template, request, url_for

from app.core.errors import DomainError

from app.modules.hunter import services as hunter

from . import bp, services
from .rules import FAILURE_REASONS, Rules


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        services.save_rules(_rules_from_form())
        hunter.set_achievement_rewards(request.form.get("achievement_rewards") == "on")
        flash("Regras do System atualizadas.", "success")
        return redirect(url_for("gamification.index"))
    return render_template("gamification/index.html", rules=services.get_rules(), history=services.history(),
                           reasons=FAILURE_REASONS, pending_failures=services.pending_failures_count(),
                           achievement_rewards=hunter.achievement_rewards_enabled())


@bp.get("/failures")
def failures():
    return render_template("gamification/failures.html", pending=services.list_failures(pending_only=True),
                           history=[f for f in services.list_failures() if f.reason], reasons=FAILURE_REASONS,
                           stats=services.failure_stats(), rules=services.get_rules())


@bp.post("/failures/<int:failure_id>")
def classify(failure_id: int):
    message, category = services.classify_failure(failure_id, request.form.get("reason", ""),
                                                  request.form.get("note", ""))
    flash(message, category)
    return redirect(url_for("gamification.failures"))


def _rules_from_form() -> Rules:
    form = request.form

    def number(name: str, low: int = 0, high: int = 1000) -> int:
        try:
            value = int(form.get(name, "0"))
        except ValueError as exc:
            raise DomainError("Use apenas números inteiros nas regras.") from exc
        if not low <= value <= high:
            raise DomainError(f"Valor fora do intervalo ({low} a {high}).")
        return value

    tiers = []
    for index in range(3):
        days, percent = form.get(f"tier_days_{index}", "").strip(), form.get(f"tier_percent_{index}", "").strip()
        if days and percent:
            tiers.append((number(f"tier_days_{index}", 1, 3650), number(f"tier_percent_{index}", 1, 500)))
    return Rules(
        bonuses_enabled=form.get("bonuses_enabled") == "on",
        first_quest_bonus_xp=number("first_quest_bonus_xp"),
        daily_combo_percent=number("daily_combo_percent", 0, 500),
        daily_combo_min_xp=number("daily_combo_min_xp"),
        early_bonus_percent=number("early_bonus_percent", 0, 500),
        streak_tiers=sorted(tiers),
        penalties_enabled=form.get("penalties_enabled") == "on",
        penalty_xp_percent=number("penalty_xp_percent", 0, 100),
        penalty_quest_enabled=form.get("penalty_quest_enabled") == "on",
        refund_reasons=[key for key in FAILURE_REASONS if key in form.getlist("refund_reasons")],
    )
