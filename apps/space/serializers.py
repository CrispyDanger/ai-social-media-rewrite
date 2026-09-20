from rest_framework import serializers

from apps.account.models import User
from apps.space.models import Invite, Membership, Space
from apps.space.services import unique_slug_for


class CreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'display_name')


class SpaceSerializer(serializers.ModelSerializer):
    created_by = CreatorSerializer(read_only=True)
    member_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Space
        fields = (
            'id',
            'name',
            'slug',
            'description',
            'created_by',
            'created_at',
            'member_count',
        )
        extra_kwargs = {
            'slug': {'required': False},
            'description': {'required': False, 'allow_blank': True},
        }

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError('This field may not be blank.')
        return name

    def validate_slug(self, value):
        slug = value.lower()
        queryset = Space.objects.filter(slug__iexact=slug)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('A space with this slug already exists.')
        return slug

    def create(self, validated_data):
        if not validated_data.get('slug'):
            validated_data['slug'] = unique_slug_for(validated_data['name'])
        return super().create(validated_data)


class SpacePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Space
        fields = ('id', 'name', 'slug')


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
