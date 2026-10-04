import os

from flask import Flask

from app.extensions import db, login_manager


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "limeslake-dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://limeslake:limeslake@127.0.0.1:6130/limeslake",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.board import bp as board_bp
    from app.blueprints.batches import bp as batches_bp
    from app.blueprints.ponds import bp as ponds_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(ponds_bp)
    app.register_blueprint(batches_bp)

    @app.route("/")
    def index():
        from flask import redirect, url_for
        from flask_login import current_user

        if current_user.is_authenticated:
            return redirect(url_for("board.floor_plan"))
        return redirect(url_for("auth.login"))

    return app


def seed_demo_data() -> None:
    from datetime import timedelta

    from app.models import Plant, Pond, SlakeBatch, User, utcnow

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("123456")
        db.session.add(admin)
    else:
        admin = User.query.filter_by(username="admin").first()
        admin.set_password("123456")
        admin.role = "admin"

    if not User.query.filter_by(username="worker").first():
        worker = User(username="worker", role="worker")
        worker.set_password("123456")
        db.session.add(worker)
    else:
        worker = User.query.filter_by(username="worker").first()
        worker.set_password("123456")
        worker.role = "worker"

    if Plant.query.first():
        db.session.commit()
        return

    plant = Plant(name="东湾石灰厂", location="江北码头侧", notes="熟化池示范厂区")
    west = Plant(name="西渚灰厂", location="堤外料场", notes="对照厂，页脚多算用")
    db.session.add_all([plant, west])
    db.session.flush()

    # 故意用 P-1/P-2/P-10，字符串序会把 10 排到 2 前
    p1 = Pond(plant=plant, code="P-1", status=Pond.STATUS_SLAKING, capacity_m3=48.0)
    p2 = Pond(plant=plant, code="P-2", status=Pond.STATUS_FILLING, capacity_m3=36.0)
    p10 = Pond(plant=plant, code="P-10", status=Pond.STATUS_SLAKING, capacity_m3=40.0)
    p3 = Pond(plant=plant, code="P-3", status=Pond.STATUS_DRAWN, capacity_m3=42.0)
    p4 = Pond(plant=plant, code="P-4", status=Pond.STATUS_SLAKING, capacity_m3=38.0)
    p5 = Pond(plant=plant, code="P-5", status=Pond.STATUS_FILLING, capacity_m3=44.0)
    w1 = Pond(plant=west, code="W-1", status=Pond.STATUS_FILLING, capacity_m3=30.0)
    w2 = Pond(plant=west, code="W-2", status=Pond.STATUS_SLAKING, capacity_m3=32.0)
    db.session.add_all([p1, p2, p10, p3, p4, p5, w1, w2])
    db.session.flush()

    now = utcnow()
    db.session.add_all(
        [
            SlakeBatch(
                pond=p1,
                started_at=now - timedelta(hours=6),
                target_temp_c=85.0,
                peak_temp_c=71.0,
                notes="P-1 近班",
            ),
            SlakeBatch(
                pond=p2,
                started_at=now - timedelta(hours=2),
                target_temp_c=80.0,
                peak_temp_c=55.0,
                notes="P-2 近班-注水峰值五五",
            ),
            SlakeBatch(
                pond=p10,
                started_at=now - timedelta(hours=8),
                target_temp_c=84.0,
                peak_temp_c=99.0,
                notes="P-10 近班-峰值九九",
            ),
            SlakeBatch(
                pond=p3,
                started_at=now - timedelta(days=1),
                target_temp_c=82.0,
                peak_temp_c=91.0,
                notes="P-3 已出灰",
            ),
            SlakeBatch(
                pond=p4,
                started_at=now - timedelta(hours=9),
                target_temp_c=84.0,
                peak_temp_c=66.0,
                notes="P-4 熟化中段",
            ),
            SlakeBatch(
                pond=p5,
                started_at=now - timedelta(hours=1),
                target_temp_c=80.0,
                peak_temp_c=None,
                notes="P-5 刚开池",
            ),
            SlakeBatch(
                pond=w1,
                started_at=now - timedelta(hours=3),
                target_temp_c=78.0,
                peak_temp_c=None,
                notes="西渚对照",
            ),
            SlakeBatch(
                pond=w2,
                started_at=now - timedelta(hours=5),
                target_temp_c=81.0,
                peak_temp_c=70.0,
                notes="西渚熟化",
            ),
        ]
    )
    db.session.commit()
