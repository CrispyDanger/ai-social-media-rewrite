from django.db import transaction

from apps.space.models import Invite, Membership


@transaction.atomic
def accept_invite(invite):
    Membership.objects.get_or_create(space=invite.space, user=invite.invitee)
    invite.status = Invite.Status.ACCEPTED
    invite.save(update_fields=['status'])


def decline_invite(invite):
    invite.status = Invite.Status.DECLINED
    invite.save(update_fields=['status'])
