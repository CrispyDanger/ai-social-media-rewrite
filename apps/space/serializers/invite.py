from rest_framework import serializers

from apps.account.models import User
from apps.space.models import Invite, Membership

from .creator import CreatorSerializer
from .space_preview import SpacePreviewSerializer


class InviteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    space = SpacePreviewSerializer(read_only=True)
    invitee = CreatorSerializer(read_only=True)
    invited_by = CreatorSerializer(read_only=True)

    class Meta:
        model = Invite
        fields = (
            'id',
            'username',
            'space',
            'invitee',
            'invited_by',
            'status',
            'created_at',
        )
        read_only_fields = ('status', 'created_at')

    def validate_username(self, value):
        user = User.objects.filter(username__iexact=value).first()
        if user is None:
            raise serializers.ValidationError('User not found.')
        return user

    def validate(self, attrs):
        invitee = attrs.pop('username')
        _validate_new_invite(invitee, self.context['space'], self.context['request'].user)
        attrs['invitee'] = invitee
        return attrs


def _validate_new_invite(invitee, space, invited_by):
    if invitee.id == invited_by.id:
        raise serializers.ValidationError({'username': 'You cannot invite yourself.'})
    if Membership.objects.filter(space=space, user=invitee).exists():
        raise serializers.ValidationError({'username': 'User is already a member.'})
    pending = Invite.objects.filter(
        space=space,
        invitee=invitee,
        status=Invite.Status.PENDING,
    )
    if pending.exists():
        raise serializers.ValidationError({'username': 'User already has a pending invite.'})
