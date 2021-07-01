from rest_framework import serializers
from .models import AssistanceProgram, EligibleTreatment


class AssistanceProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistanceProgram
        fields = '__all__'  # importing all fields


class EligibleTreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibleTreatment
        fields = '__all__'  # importing all fields