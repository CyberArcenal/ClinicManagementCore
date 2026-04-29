# app/models/notifications/enums.py
import enum

class TemplateType(str, enum.Enum):
    PROFILE_UPDATE = "profile_update"
    PROFILE_PICTURE_CHANGED = "profile_picture_changed"
    COVER_PHOTO_CHANGED = "cover_photo_changed"
    NEW_MESSAGE = "new_message"
    MENTION_NOTIFICATION = "mention_notification"
    TAG_NOTIFICATION = "tag_notification"
    NEW_LIKE = "new_like"
    NEW_COMMENT = "new_comment"
    COMMENT_REPLY = "comment_reply"
    NEW_SHARE = "new_share"
    REACTION_UPDATE = "reaction_update"
    FRIEND_REQUEST = "friend_request"
    FRIEND_REQUEST_ACCEPTED = "friend_request_accepted"
    GROUP_INVITATION = "group_invitation"
    GROUP_POST_NOTIFICATION = "group_post_notification"
    EVENT_INVITATION = "event_invitation"
    EVENT_REMINDER = "event_reminder"
    FOLLOWER_MILESTONE = "follower_milestone"
    POST_MILESTONE = "post_milestone"
    ACHIEVEMENT_BADGE = "achievement_badge"
    LOGIN_ALERT = "login_alert"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    SECURITY_ALERT = "security_alert"

class NotificationTypeEnum(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    MESSAGE = "message"
    GROUP_INVITE = "group_invite"
    EVENT_REMINDER = "event_reminder"

class NotifyStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RESEND = "resend"