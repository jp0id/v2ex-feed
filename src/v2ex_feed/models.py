from pathlib import Path
from tortoise import Tortoise, fields
from tortoise.models import Model
from settings import settings


class Post(Model):
    id = fields.IntField(pk=True)
    v2ex_id = fields.CharField(max_length=100, unique=True)
    node_name = fields.CharField(max_length=100, null=True)
    title = fields.CharField(max_length=255)
    link = fields.CharField(max_length=255)
    content = fields.TextField(null=True)
    published = fields.DatetimeField(null=True)
    updated = fields.DatetimeField(null=True)
    author_name = fields.CharField(max_length=255, null=True)
    author_uri = fields.CharField(max_length=255, null=True)
    sent = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(null=True)
    updated_at = fields.DatetimeField(null=True)

    class Meta:
        table = "v2ex_posts"


def _build_db_url() -> str:
    raw = settings.DB_FILE
    db_path = Path(raw).expanduser()

    if not db_path.is_absolute():
        project_root = Path(__file__).resolve().parents[2]
        db_path = project_root / "data" / db_path.name

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite://{db_path}"


async def init_db() -> None:
    await Tortoise.init(
        db_url=_build_db_url(),
        modules={"models": ["v2ex_feed.models"]},
        use_tz=False,
        timezone=settings.TIMEZONE,
    )
    await Tortoise.generate_schemas()
