import json
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .. import exc, util, validators
from .site import Site

log = logging.getLogger(__name__)


class EmailUserManager(BaseUserManager):
    """Custom manager for email-based User.

    This replaces the manager formerly provided by ``django-custom-user``.
    """

    def _create_user(
        self, email, password, is_staff, is_superuser, **extra_fields
    ):
        """
        Create and save a User with the given email and password.

        :param str email: user email
        :param str password: user password
        :param bool is_staff: whether user staff or not
        :param bool is_superuser: whether user admin or not
        :return User: user
        :raise ValueError: email is not set
        """
        now = timezone.now()
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        is_active = extra_fields.pop("is_active", True)
        user = self.model(
            email=email,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=is_superuser,
            last_login=now,
            date_joined=now,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        is_staff = extra_fields.pop("is_staff", False)
        return self._create_user(
            email, password, is_staff, False, **extra_fields
        )

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a superuser with the given email and password."""
        return self._create_user(
            email, password, True, True, **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    """A custom user object that utilizes email as the username.

    Replaces the former ``custom_user.models.AbstractEmailUser`` base class
    with an equivalent inline implementation based on ``AbstractBaseUser``
    and ``PermissionsMixin``.

    The following attributes are inherited from the superclasses:
        * password
        * last_login
        * is_superuser
    """

    email = models.EmailField(
        _("email address"), max_length=255, unique=True, db_index=True
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as "
            "active. Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(
        _("date joined"), default=timezone.now
    )
    secret_key = models.CharField(
        max_length=44,
        default=util.generate_secret_key,
        help_text="The user's secret_key used for API authentication.",
    )

    objects = EmailUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def get_full_name(self):
        """Return the email."""
        return self.email

    def get_short_name(self):
        """Return the email."""
        return self.email

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this User."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def username(self):
        return self.get_username()

    def get_permissions(self):
        permissions = []
        if self.is_staff or self.is_superuser:
            permissions.append("admin")
        sites = Site.objects.all()

        return {
            str(site.id): {
                "permissions": permissions,
                "site_id": site.id,
                "user_id": self.id,
            }
            for site in sites
        }

    def rotate_secret_key(self):
        self.secret_key = util.generate_secret_key()
        self.save()

    def generate_auth_token(self):
        """Serialize user data and encrypt token."""
        # Serialize data and utf-encode
        data = json.dumps({"email": self.email})

        # Encrypt data w/ servers's secret_key (it must be utf-encoded)
        f = Fernet(str(settings.SECRET_KEY))
        auth_token = f.encrypt(bytes(data, "utf-8"))
        return auth_token

    def verify_secret_key(self, secret_key):
        """Validate secret_key"""
        return secret_key == self.secret_key

    @classmethod
    def verify_auth_token(cls, email, auth_token, expiration=None):
        """Verify token and return a User object."""
        if expiration is None:
            expiration = settings.AUTH_TOKEN_EXPIRY

        # First we lookup the user by email
        query = cls.objects.filter(email=email)
        user = query.first()

        if user is None:
            log.debug("Invalid user when verifying token")
            raise exc.ValidationError(
                {"auth_token": "Invalid user when verifying token"}
            )
            # return None  # Invalid user

        # Decrypt auth_token w/ user's secret_key
        f = Fernet(str(settings.SECRET_KEY))
        try:
            decrypted_data = f.decrypt(
                bytes(auth_token, "utf-8"), ttl=expiration
            )
        except InvalidToken:
            log.debug("Invalid/expired auth_token when decrypting.")
            raise exc.ValidationError(
                {"auth_token": "Invalid/expired auth_token."}
            )
            # return None  # Invalid token

        # Deserialize data
        try:
            data = json.loads(decrypted_data)
        except ValueError:
            log.debug("Token could not be deserialized.")
            raise exc.ValidationError(
                {"auth_token": "Token could not be deserialized."}
            )
            # return None  # Valid token, but expired

        if email != data["email"]:
            log.debug("Invalid user when deserializing.")
            raise exc.ValidationError(
                {"auth_token": "Invalid user when deserializing."}
            )
            # return None  # User email did not match payload
        return user

    def clean_email(self, value):
        return validators.validate_email(value)

    def clean_fields(self, exclude=None):
        self.email = self.clean_email(self.email)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(User, self).save(*args, **kwargs)

    def to_dict(self, with_permissions=False, with_secret_key=False):
        out = [
            ("id", self.id),
            ("email", self.email),
        ]

        if with_secret_key:
            out.append(("secret_key", self.secret_key))

        if with_permissions:
            out.append(("permissions", self.get_permissions()))

        return dict(out)
