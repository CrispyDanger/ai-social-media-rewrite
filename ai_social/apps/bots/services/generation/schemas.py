from pydantic import BaseModel, Field

POST_MAX_LENGTH = 280


class NewPost(BaseModel):
    """A new original post written in the bot's voice."""

    text: str = Field(min_length=1, max_length=POST_MAX_LENGTH)


class Reply(BaseModel):
    """Reply to the post with a short message."""

    text: str = Field(min_length=1, max_length=POST_MAX_LENGTH)


class Like(BaseModel):
    """Like the post without writing anything."""


class Repost(BaseModel):
    """Repost the post to your followers."""


Decision = Reply | Like | Repost
