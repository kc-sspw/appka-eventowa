import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class AccountManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        account = self.model(username=username, **extra)
        account.set_password(password)
        account.full_clean()
        account.save()
        return account

    def create_superuser(self, username, password=None, **extra):
        return self.create_user(username, password, role="PLATFORM", event=None, **extra)


class Account(AbstractBaseUser):
    class Role(models.TextChoices):
        PLATFORM = "PLATFORM", "Platforma"
        ORGANIZER = "ORGANIZER", "Organizator"
        PARTICIPANT = "PARTICIPANT", "Uczestnik"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", null=True, blank=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=64, unique=True)
    first_name = models.CharField(max_length=60, blank=True)
    public_number = models.PositiveIntegerField(null=True, blank=True)
    role = models.CharField(max_length=12, choices=Role, default=Role.PARTICIPANT)
    is_active = models.BooleanField(default=True)
    objects = AccountManager()
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(role="PLATFORM", event__isnull=True)
                    | Q(role__in=["ORGANIZER", "PARTICIPANT"], event__isnull=False)
                ),
                name="account_event_role",
            ),
            models.UniqueConstraint(
                fields=["event", "public_number"], name="public_number_per_event"
            ),
        ]

    @property
    def is_staff(self):
        return self.role == self.Role.PLATFORM

    @property
    def is_superuser(self):
        return self.is_staff

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_staff

    def has_module_perms(self, app_label):
        return self.is_active and self.is_staff

    def clean(self):
        if (self.role == self.Role.PLATFORM) != (self.event_id is None):
            raise ValidationError("Konto platformy nie należy do wydarzenia.")

    def __str__(self):
        return f"{self.first_name or 'Osoba'} · #{self.public_number or '—'}"


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    members = models.ManyToManyField(Account, through="Membership", related_name="event_groups")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "name"], name="event_group_name")]

    def __str__(self):
        return self.name


class Membership(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["account", "group"], name="unique_membership")
        ]


class ImportBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    batch_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["event", "batch_id"], name="batch_idempotency")
        ]


class ImportRow(models.Model):
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE)
    row_id = models.UUIDField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    created = models.BooleanField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["batch", "row_id"], name="row_idempotency")]


class AccountSession(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, unique=True)
