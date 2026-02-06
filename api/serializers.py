from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Market, Outcome, Position, Trade

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'balance', 'currency', 'role', 'tier', 'avatarUrl', 'joinedDate']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

class OutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outcome
        fields = ['id', 'label', 'probability']

class MarketSerializer(serializers.ModelSerializer):
    outcomes = OutcomeSerializer(many=True)
    
    class Meta:
        model = Market
        fields = ['id', 'title', 'description', 'imageUrl', 'category', 'volume', 'endDate', 'status', 'change24h', 'outcomes', 'winner_id']

    def create(self, validated_data):
        outcomes_data = validated_data.pop('outcomes', [])
        market = Market.objects.create(**validated_data)
        for outcome_data in outcomes_data:
            Outcome.objects.create(market=market, **outcome_data)
        return market

class PositionSerializer(serializers.ModelSerializer):
    market_title = serializers.CharField(source='market.title', read_only=True)
    outcome_label = serializers.CharField(source='outcome.label', read_only=True)
    
    class Meta:
        model = Position
        fields = ['id', 'market', 'market_title', 'outcome', 'outcome_label', 'shares', 'avgPrice', 'side']

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = '__all__'
